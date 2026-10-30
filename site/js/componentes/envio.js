/* Envio ao serviço configurado em config_participacao.json.
   provedor ausente ou "formspree": POST urlencoded (caminho atual).
   provedor "cloudflare": JSON + desafio humano. Formspree permanece até a Etapa F. */
import { estado } from "../nucleo/estado.js";
import { TEMPO_ENVIO_MS, MAX_ENVIOS_TOTAIS_VISITA } from "../nucleo/constantes.js";
import { hashCorpo } from "../nucleo/protecao.js";
import { resetarDesafio, tokenDesafio, usaCloudflare } from "./desafio.js";

const MAX_PAYLOAD = 8000;
let emVoo = false;

export class ErroEnvio extends Error {
  constructor(motivo, status = null) { super(motivo); this.motivo = motivo; this.status = status; }
}

export function envioAtivo() {
  const c = estado.config;
  return !!(c && c.ativo === true && c.contribuicoes_abertas !== false && typeof c.endpoint === "string" && c.endpoint.startsWith("https:"));
}

export function contribuicoesSuspensas() {
  const c = estado.config;
  return !!(c && c.ativo === true && c.contribuicoes_abertas === false);
}

export function provedorCloudflare() {
  return usaCloudflare(estado.config);
}

function totalEnvios() {
  return (estado.enviosFrases || 0) + (estado.enviosDiscordancia || 0) + (estado.enviosLote || 0);
}

function novoId() {
  if (crypto.randomUUID) return crypto.randomUUID();
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

function payloadCloudflare(campos) {
  const tipo = campos.tipo === "avaliacoes_voluntarias" ? "avaliacoes" : campos.tipo;
  const out = {
    schema_version: "3",
    tipo,
    submission_id: campos.submission_id || novoId(),
    aviso_versao: campos.aviso_versao || "",
    consentimento: campos.consentimento,
    armadilha: campos.armadilha || "",
  };
  if (tipo === "avaliacoes") {
    out.avaliacoes = typeof campos.avaliacoes === "string" ? JSON.parse(campos.avaliacoes) : campos.avaliacoes;
  } else if (tipo === "contestacao") {
    out.frase_id = campos.frase_id;
    out.conteudo_versao = campos.conteudo_versao || "";
    out.motivo = campos.motivo === "erro_no_texto" ? "erro_texto" : (campos.motivo || "");
    out.comentario = campos.comentario || campos.frase || "";
    if (campos.avaliacao_contestada) out.avaliacao_contestada = campos.avaliacao_contestada;
  } else {
    out.texto = campos.texto || campos.frase || "";
    out.interpretacao_sugerida = campos.interpretacao_sugerida || campos.avaliacao;
    if (campos.contexto) out.contexto = campos.contexto;
  }
  return out;
}

function motivoDaResposta(r, json) {
  if (r.status === 402 || (json && /quota|over.?limit/i.test(JSON.stringify(json)))) return "cota";
  const e = json && json.erro;
  if (e === "indisponivel") return "indisponivel";
  if (e === "turnstile") return "turnstile";
  if (e === "abuso") return "limite_visita";
  if (e === "payload") return "payload";
  if (e === "validacao") return "validacao";
  if (!r.ok) return "servico_recusou";
  if (json && (json.ok === false || json.error)) return "servico_recusou";
  return null;
}

export async function enviar(campos, { interacao = true, onEstado, caixaDesafio } = {}) {
  if (!envioAtivo()) throw new ErroEnvio("indisponivel");
  if (!interacao) return { confirmado: false, descartado: true };
  if ((campos.armadilha || "").toString().trim()) return { confirmado: false, descartado: true };
  if (emVoo) throw new ErroEnvio("servico_recusou");
  if (totalEnvios() >= MAX_ENVIOS_TOTAIS_VISITA) throw new ErroEnvio("limite_visita");
  const c = estado.config;
  const cf = usaCloudflare(c);
  if (onEstado) onEstado("validando");

  let corpo;
  let headers = { Accept: "application/json" };
  let caixa = caixaDesafio || (cf ? document.getElementById("desafio-envio") : null);
  if (cf) {
    if (onEstado) onEstado("verificando");
    const token = await tokenDesafio(caixa, c.turnstile_sitekey, {
      onEspera() { if (onEstado) onEstado("aguardando"); },
    }).catch(() => {
      throw new ErroEnvio("turnstile");
    });
    const json = payloadCloudflare(campos);
    json.turnstile_token = token;
    corpo = JSON.stringify(json);
    headers["Content-Type"] = "application/json";
  } else {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(campos)) params.append((c.campos && c.campos[k]) || k, v == null ? "" : String(v));
    if (!params.has("_gotcha")) params.append("_gotcha", "");
    corpo = params;
  }

  const serial = typeof corpo === "string" ? corpo : corpo.toString();
  if (serial.length > MAX_PAYLOAD) throw new ErroEnvio("payload");
  const chave = hashCorpo(serial);
  if (!estado.corposEnviados) estado.corposEnviados = new Set();
  if (estado.corposEnviados.has(chave)) return { confirmado: false, descartado: true };

  const controle = new AbortController();
  const tempo = setTimeout(() => controle.abort(), TEMPO_ENVIO_MS);
  const base = { method: "POST", body: corpo, credentials: "omit", referrerPolicy: "no-referrer", signal: controle.signal };
  emVoo = true;
  if (onEstado) onEstado("enviando");
  try {
    if (!cf && c.modo_resposta === "opaca") {
      await fetch(c.endpoint, { ...base, mode: "no-cors" });
      estado.corposEnviados.add(chave);
      return { confirmado: false };
    }
    const r = await fetch(c.endpoint, { ...base, mode: "cors", headers });
    let json = null;
    try { json = await r.json(); } catch { /* resposta sem JSON: vale o status HTTP */ }
    const motivo = motivoDaResposta(r, json);
    if (motivo) throw new ErroEnvio(motivo, r.status);
    estado.corposEnviados.add(chave);
    return { confirmado: true };
  } catch (e) {
    if (e instanceof ErroEnvio) throw e;
    throw new ErroEnvio(e && e.name === "AbortError" ? "tempo_esgotado" : "rede");
  } finally {
    emVoo = false;
    clearTimeout(tempo);
    if (cf && caixa && corpo) resetarDesafio(caixa);
  }
}
