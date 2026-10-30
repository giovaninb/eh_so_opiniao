export type ResultadoTurnstile =
  | { ok: true }
  | { ok: false; motivo: "invalido" | "hostname" | "action" | "reutilizado" | "indisponivel" | "secret" };

const SITEVERIFY = "https://challenges.cloudflare.com/turnstile/v0/siteverify";

export async function verificarTurnstile(
  token: string,
  secret: string,
  hostnames: string[],
  action: string,
  fetchImpl: typeof fetch = fetch,
): Promise<ResultadoTurnstile> {
  if (!secret) return { ok: false, motivo: "secret" };
  if (!token || token.length > 2048) return { ok: false, motivo: "invalido" };
  const corpo = new URLSearchParams({ secret, response: token });
  // Sem remoteip: Siteverify não recebe endereço de rede. Rate limit usa hash efêmero à parte.
  const controle = new AbortController();
  const t = setTimeout(() => controle.abort(), 4000);
  try {
    const r = await fetchImpl(SITEVERIFY, {
      method: "POST",
      body: corpo,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      signal: controle.signal,
    });
    const json = (await r.json()) as {
      success?: boolean;
      hostname?: string;
      action?: string;
      "error-codes"?: string[];
    };
    if (!json.success) {
      const codes = json["error-codes"] || [];
      if (codes.includes("timeout-or-duplicate")) return { ok: false, motivo: "reutilizado" };
      return { ok: false, motivo: "invalido" };
    }
    if (hostnames.length && (!json.hostname || !hostnames.includes(json.hostname))) {
      return { ok: false, motivo: "hostname" };
    }
    if (action && json.action && json.action !== action && json.action !== "test") {
      return { ok: false, motivo: "action" };
    }
    return { ok: true };
  } catch {
    return { ok: false, motivo: "indisponivel" };
  } finally {
    clearTimeout(t);
  }
}
