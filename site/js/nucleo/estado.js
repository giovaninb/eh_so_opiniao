/* Estado compartilhado, só em memória: nada é guardado no aparelho do visitante. */
export const estado = {
  frases: [],
  porId: new Map(),
  temas: [],
  grupos: [], // temas de descoberta legado (Mulheres, Pessoas idosas…) com frases publicadas
  camadaAssuntos: { grupos: [], assuntos: [], situacoes: [] },
  pares: [], // comparações revisadas ("Duas frases, uma diferença")
  contexto: [], // dados de contexto (dado, fonte, ano, metodologia, limitações) por grupo
  grupoAtual: "", // tema legado escolhido em Descobrir ("" = ao acaso)
  assuntoAtual: "", // assunto editorial escolhido em Descobrir
  config: null,
  resultados: {},
  minimoVotos: 10,
  rascunho: new URLSearchParams(location.search).get("rascunho") === "1",
  semente: Number(new URLSearchParams(location.search).get("semente")) || null,
  erro: null,
  respostas: new Map(), // id da frase -> valor escolhido (só nesta visita)
  votosEnviados: new Set(),
  enviosFrases: 0,
  enviosDiscordancia: 0,
  sessao: null, // modo Descoberta
  ordemBiblioteca: [], // ids na ordem da última lista exibida (para "próxima frase")
};
