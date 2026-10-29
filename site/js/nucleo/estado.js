/* Estado compartilhado, só em memória: nada é guardado no aparelho do visitante. */
export const estado = {
  frases: [],
  porId: new Map(),
  temas: [],
  config: null,
  resultados: {},
  minimoVotos: 10,
  rascunho: new URLSearchParams(location.search).get("rascunho") === "1",
  semente: Number(new URLSearchParams(location.search).get("semente")) || null,
  erro: null,
  respostas: new Map(), // id da frase -> valor escolhido (só nesta visita)
  votosEnviados: new Set(),
  enviosFrases: 0,
  sessao: null, // modo Descoberta
  ordemBiblioteca: [], // ids na ordem da última lista exibida (para "próxima frase")
};
