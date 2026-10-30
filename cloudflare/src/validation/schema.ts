import type { Avaliacao, Motivo, Tipo } from "../types";

export const MAX_BODY = 8000;
export const MIN_FRASE = 10;
export const MAX_FRASE = 280;
export const MAX_COMENTARIO = 280;
export const MAX_CONTEXTO = 280;
export const MAX_LOTE = 5;
export const ID_FRASE = /^[A-Z]{1,3}-\d{1,4}$/;
export const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const AVALIACOES = new Set<Avaliacao>(["nao_vejo_problema", "possivel_discriminacao", "preciso_contexto"]);
const ALIAS_AVAL: Record<string, Avaliacao> = {
  opiniao: "nao_vejo_problema",
  discriminacao: "possivel_discriminacao",
  contexto: "preciso_contexto",
};
const MOTIVOS = new Set<Motivo>([
  "falta_contexto", "discordo_classificacao", "explicacao_incompleta",
  "interpretacao_excessiva", "erro_texto", "outro",
]);
const ALIAS_MOTIVO: Record<string, Motivo> = { erro_no_texto: "erro_texto" };
const TIPOS = new Set<Tipo>(["avaliacoes", "contestacao", "sugestao_frase"]);
const ALIAS_TIPO: Record<string, Tipo> = { avaliacoes_voluntarias: "avaliacoes" };
const MODOS = new Set(["descobrir", "inicio", "explorar", "frase", "comparar", "assuntos", "desconhecido"]);
const COMUNS = new Set([
  "schema_version", "tipo", "submission_id", "conteudo_versao", "aviso_versao",
  "consentimento", "turnstile_token", "armadilha",
]);
const POR_TIPO: Record<Tipo, Set<string>> = {
  avaliacoes: new Set([...COMUNS, "avaliacoes", "n"]),
  contestacao: new Set([...COMUNS, "frase_id", "motivo", "comentario", "avaliacao_contestada"]),
  sugestao_frase: new Set([...COMUNS, "texto", "frase", "interpretacao_sugerida", "avaliacao", "contexto"]),
};

export type Falha = { campo: string; motivo: string };

export function avaliacaoCanonica(v: unknown): Avaliacao | null {
  const s = String(v || "").trim();
  if (AVALIACOES.has(s as Avaliacao)) return s as Avaliacao;
  return ALIAS_AVAL[s] || null;
}

export function tipoCanonico(v: unknown): Tipo | null {
  const s = String(v || "").trim();
  if (TIPOS.has(s as Tipo)) return s as Tipo;
  return ALIAS_TIPO[s] || null;
}

function sim(v: unknown): boolean {
  if (v === true || v === 1) return true;
  return ["sim", "true", "on", "1"].includes(String(v).toLowerCase());
}

function chaves(obj: Record<string, unknown>): string[] {
  return Object.keys(obj);
}

export function validar(bruto: unknown): { ok: true; dados: Record<string, unknown> } | { ok: false; falhas: Falha[] } {
  const falhas: Falha[] = [];
  if (!bruto || typeof bruto !== "object" || Array.isArray(bruto)) {
    return { ok: false, falhas: [{ campo: "corpo", motivo: "json_objeto" }] };
  }
  const o = bruto as Record<string, unknown>;
  const tipo = tipoCanonico(o.tipo);
  if (!tipo) falhas.push({ campo: "tipo", motivo: "invalido" });
  if (tipo) {
    for (const k of chaves(o)) {
      if (!POR_TIPO[tipo].has(k)) falhas.push({ campo: k, motivo: "desconhecido" });
    }
  }
  if (o.armadilha && String(o.armadilha).trim()) falhas.push({ campo: "armadilha", motivo: "preenchida" });
  if (!sim(o.consentimento)) falhas.push({ campo: "consentimento", motivo: "ausente" });
  if (!UUID.test(String(o.submission_id || ""))) falhas.push({ campo: "submission_id", motivo: "uuid" });
  if (!String(o.turnstile_token || "").trim()) falhas.push({ campo: "turnstile_token", motivo: "ausente" });
  if (falhas.length || !tipo) return { ok: false, falhas };

  const base: Record<string, unknown> = {
    schema_version: String(o.schema_version || "3"),
    tipo,
    submission_id: String(o.submission_id),
    aviso_versao: String(o.aviso_versao || ""),
    consentimento: 1,
    turnstile_token: String(o.turnstile_token),
  };

  if (tipo === "avaliacoes") {
    const lista = Array.isArray(o.avaliacoes) ? o.avaliacoes : [];
    if (!lista.length) falhas.push({ campo: "avaliacoes", motivo: "vazio" });
    if (lista.length > MAX_LOTE) falhas.push({ campo: "avaliacoes", motivo: "lote" });
    const itens = [];
    for (const it of lista) {
      if (!it || typeof it !== "object") { falhas.push({ campo: "avaliacoes", motivo: "item" }); continue; }
      const a = it as Record<string, unknown>;
      const av = avaliacaoCanonica(a.avaliacao);
      if (!ID_FRASE.test(String(a.frase_id || ""))) falhas.push({ campo: "frase_id", motivo: "invalido" });
      if (!av) falhas.push({ campo: "avaliacao", motivo: "invalido" });
      const modo = String(a.modo || "desconhecido");
      itens.push({
        frase_id: String(a.frase_id || ""),
        tema_id: String(a.tema_id || ""),
        modo: MODOS.has(modo) ? modo : "desconhecido",
        avaliacao: av,
        conteudo_versao: String(a.conteudo_versao || ""),
        contexto_exibido: sim(a.contexto_exibido) ? 1 : 0,
        analise_revelada: sim(a.analise_revelada) ? 1 : 0,
      });
    }
    if (falhas.length) return { ok: false, falhas };
    return { ok: true, dados: { ...base, avaliacoes: itens } };
  }

  if (tipo === "contestacao") {
    const frase_id = String(o.frase_id || "");
    if (!ID_FRASE.test(frase_id)) falhas.push({ campo: "frase_id", motivo: "invalido" });
    const comentario = String(o.comentario || "").trim();
    if (comentario.length > MAX_COMENTARIO) falhas.push({ campo: "comentario", motivo: "tamanho" });
    let motivo = String(o.motivo || "").trim();
    if (motivo) motivo = ALIAS_MOTIVO[motivo] || motivo;
    if (motivo && !MOTIVOS.has(motivo as Motivo)) falhas.push({ campo: "motivo", motivo: "invalido" });
    if (!comentario && !motivo) falhas.push({ campo: "comentario", motivo: "vazio" });
    if (falhas.length) return { ok: false, falhas };
    return {
      ok: true,
      dados: {
        ...base,
        frase_id,
        conteudo_versao: String(o.conteudo_versao || ""),
        motivo: motivo || "",
        comentario,
      },
    };
  }

  const texto = String(o.texto || o.frase || "").trim();
  if (texto.length < MIN_FRASE || texto.length > MAX_FRASE) falhas.push({ campo: "texto", motivo: "tamanho" });
  if (/<\s*script/i.test(texto)) falhas.push({ campo: "texto", motivo: "html" });
  const interp = avaliacaoCanonica(o.interpretacao_sugerida || o.avaliacao);
  if (!interp) falhas.push({ campo: "interpretacao_sugerida", motivo: "invalido" });
  const contexto = String(o.contexto || "").trim();
  if (contexto.length > MAX_CONTEXTO) falhas.push({ campo: "contexto", motivo: "tamanho" });
  if (falhas.length) return { ok: false, falhas };
  return { ok: true, dados: { ...base, texto, interpretacao_sugerida: interp, contexto } };
}
