/* Avaliações da visita, só em memória. Nada vai ao aparelho nem ao formulário até a pessoa confirmar. */
import { estado } from "./estado.js";
import { TAMANHO_SESSAO } from "./constantes.js";

export const SCHEMA_PARTICIPACAO = "2";
export const AVISO_VERSAO = "participacao-2";
export const MAX_AVALIACOES_LOTE = TAMANHO_SESSAO;

export function modoAtual() {
  const bruto = (location.hash || "").replace(/^#\/?/, "");
  const rota = bruto.split("?")[0].split("/")[0];
  return rota || "inicio";
}

export function registrarAvaliacao({ frase, valor, modo, contextoExibido, analiseRevelada }) {
  if (!frase || !frase.id || !valor || valor === "pulou") return;
  if (!estado.avaliacoesVisita) estado.avaliacoesVisita = new Map();
  estado.avaliacoesVisita.set(frase.id, {
    frase_id: frase.id,
    conteudo_versao: frase.conteudo_versao || "desconhecida",
    tema_id: frase.tema || "",
    modo: modo || modoAtual(),
    avaliacao: valor,
    contexto_exibido: contextoExibido ? "sim" : "nao",
    analise_revelada: analiseRevelada ? "sim" : "nao",
  });
}

export function avaliacoesDoLote(ids) {
  const mapa = estado.avaliacoesVisita || new Map();
  const enviadas = estado.lotesEnviados || new Set();
  const saida = [];
  for (const id of ids || []) {
    const a = mapa.get(id);
    if (!a || enviadas.has(id)) continue;
    saida.push(a);
    if (saida.length >= MAX_AVALIACOES_LOTE) break;
  }
  return saida;
}

export function marcarLoteEnviado(ids) {
  if (!estado.lotesEnviados) estado.lotesEnviados = new Set();
  (ids || []).forEach((id) => estado.lotesEnviados.add(id));
}

export function limparAvaliacoes(ids) {
  if (!estado.avaliacoesVisita) return;
  (ids || []).forEach((id) => estado.avaliacoesVisita.delete(id));
}
