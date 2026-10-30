import type { Env, ErroCodigo } from "../types";
import { cabecalhosCors } from "../security/cors";
import { verificarTurnstile } from "../security/turnstile";
import { chaveAbuso, dentroDoLimite } from "../security/rateLimit";
import { MAX_BODY, validar } from "../validation/schema";
import { gravar } from "../db/queries";

export const ROTA = "/api/v1/participacoes";

function json(status: number, corpo: unknown, extra: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...extra },
  });
}

function erro(status: number, codigo: ErroCodigo, mensagem: string, extra: Record<string, string>): Response {
  return json(status, { ok: false, erro: codigo, mensagem }, extra);
}

export async function participacoes(request: Request, env: Env): Promise<Response> {
  const cors = cabecalhosCors(request.headers.get("Origin"), env.ALLOWED_ORIGINS || "");
  if (request.method === "OPTIONS") {
    return new Response(null, { status: cors["Access-Control-Allow-Origin"] ? 204 : 403, headers: cors });
  }
  const url = new URL(request.url);
  if (url.pathname === "/api/v1/saude" && request.method === "GET") {
    return json(200, { ok: true }, cors);
  }
  if (url.pathname !== ROTA) return erro(404, "validacao", "Recurso inexistente.", cors);
  if (request.method !== "POST") return erro(405, "metodo", "Use POST.", cors);
  if (!cors["Access-Control-Allow-Origin"] && request.headers.get("Origin")) {
    return erro(403, "abuso", "Origem não autorizada.", cors);
  }

  const tipo = request.headers.get("content-type") || "";
  if (!tipo.toLowerCase().includes("application/json")) {
    return erro(415, "validacao", "Content-Type deve ser application/json.", cors);
  }
  const tamanho = Number(request.headers.get("content-length") || "0");
  if (tamanho > MAX_BODY) return erro(413, "payload", "Pedido grande demais.", cors);

  const chave = await chaveAbuso(request.headers.get("CF-Connecting-IP"));
  if (!(await dentroDoLimite(env.LIMITE, chave))) {
    return erro(429, "abuso", "Muitas tentativas. Tente de novo em instantes.", cors);
  }

  let bruto: unknown;
  try {
    const texto = await request.text();
    if (texto.length > MAX_BODY) return erro(413, "payload", "Pedido grande demais.", cors);
    bruto = JSON.parse(texto);
  } catch {
    return erro(400, "validacao", "JSON malformado.", cors);
  }

  const v = validar(bruto);
  if (!v.ok) return json(422, { ok: false, erro: "validacao", mensagem: "Campos inválidos.", falhas: v.falhas }, cors);

  const token = String(v.dados.turnstile_token);
  delete v.dados.turnstile_token;
  const hosts = (env.ALLOWED_HOSTNAMES || "").split(",").map((s) => s.trim()).filter(Boolean);
  const ts = await verificarTurnstile(token, env.TURNSTILE_SECRET_KEY || "", hosts, env.TURNSTILE_ACTION || "participacao");
  if (!ts.ok) {
    const mapa = {
      secret: [503, "indisponivel", "Serviço temporariamente indisponível."] as const,
      indisponivel: [503, "indisponivel", "Não foi possível verificar a proteção. Tente de novo."] as const,
      reutilizado: [409, "turnstile", "A verificação expirou. Tente de novo."] as const,
      hostname: [403, "turnstile", "Verificação recusada."] as const,
      action: [403, "turnstile", "Verificação recusada."] as const,
      invalido: [403, "turnstile", "Não foi possível confirmar que o envio é humano."] as const,
    };
    const [st, cod, msg] = mapa[ts.motivo];
    return erro(st, cod, msg, cors);
  }

  const createdAt = new Date().toISOString();
  try {
    const r = await gravar(env, v.dados, createdAt);
    return json(200, { ok: true, submission_id: v.dados.submission_id, idempotente: r === "idempotente" }, cors);
  } catch {
    return erro(503, "indisponivel", "Não foi possível gravar agora. Seu texto continua no formulário.", cors);
  }
}
