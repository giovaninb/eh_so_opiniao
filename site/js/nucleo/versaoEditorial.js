/* Versão editorial da frase publicada. Precisa coincidir com participacao_esquema.versao_editorial. */

function ordenado(v) {
  if (Array.isArray(v)) return v.map(ordenado);
  if (v && typeof v === "object") return Object.fromEntries(Object.keys(v).sort().map((k) => [k, ordenado(v[k])]));
  return v;
}

export function payloadEditorial(f) {
  const rotulos = (f.rotulos || []).map((r) => (r && typeof r === "object" ? r.id : String(r))).filter(Boolean).sort();
  return {
    aviso_conteudo: !!f.aviso_conteudo,
    contexto: f.contexto || "",
    id: f.id || "",
    mecanismo: f.mecanismo || "",
    muda_se: f.muda_se || "",
    razoes: Array.isArray(f.razoes) ? f.razoes : [],
    rotulos,
    texto: f.texto || "",
    tipo: f.tipo || "",
  };
}

export async function versaoEditorial(f) {
  if (f.conteudo_versao) return f.conteudo_versao;
  const bruto = JSON.stringify(ordenado(payloadEditorial(f)));
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(bruto));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 12);
}

export async function garantirVersoes(frases) {
  await Promise.all(frases.map(async (f) => { f.conteudo_versao = await versaoEditorial(f); }));
}
