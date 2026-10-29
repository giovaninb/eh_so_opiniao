/* Envio ao serviço de formulário configurado em config_participacao.json.
   Só devolve confirmação REAL: no modo "cors" exige resposta HTTP 2xx legível; no modo "opaca" (serviços sem CORS)
   o navegador não deixa ler a resposta e o resultado volta como NÃO confirmado. */
import { estado } from "../nucleo/estado.js";
import { TEMPO_ENVIO_MS } from "../nucleo/constantes.js";

export class ErroEnvio extends Error {
  constructor(motivo, status = null) { super(motivo); this.motivo = motivo; this.status = status; }
}

export function envioAtivo() {
  const c = estado.config;
  return !!(c && c.ativo === true && typeof c.endpoint === "string" && c.endpoint.startsWith("https:"));
}

export async function enviar(campos) {
  if (!envioAtivo()) throw new ErroEnvio("indisponivel");
  const c = estado.config;
  const corpo = new URLSearchParams();
  for (const [k, v] of Object.entries(campos)) corpo.append((c.campos && c.campos[k]) || k, v);
  const controle = new AbortController();
  const tempo = setTimeout(() => controle.abort(), TEMPO_ENVIO_MS);
  const base = { method: "POST", body: corpo, credentials: "omit", referrerPolicy: "no-referrer", signal: controle.signal };
  try {
    if (c.modo_resposta === "opaca") {
      await fetch(c.endpoint, { ...base, mode: "no-cors" });
      return { confirmado: false };
    }
    const r = await fetch(c.endpoint, { ...base, mode: "cors", headers: { Accept: "application/json" } });
    if (!r.ok) throw new ErroEnvio("servico_recusou", r.status);
    let json = null;
    try { json = await r.json(); } catch { /* resposta sem JSON: vale o status HTTP */ }
    if (json && (json.ok === false || json.error)) throw new ErroEnvio("servico_recusou", r.status);
    return { confirmado: true };
  } catch (e) {
    if (e instanceof ErroEnvio) throw e;
    throw new ErroEnvio(e && e.name === "AbortError" ? "tempo_esgotado" : "rede");
  } finally {
    clearTimeout(tempo);
  }
}
