/* Lógica pura (sem DOM): fácil de testar e de revisar. */

export function normalizar(texto) {
  return (texto || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

export function filtrarFrases(frases, { q = "", tipo = "", tema = "", ord = "" } = {}) {
  const termo = normalizar(q);
  let r = frases.filter((f) => {
    if (tipo && f.tipo !== tipo) return false;
    if (tema && f.tema !== tema) return false;
    if (termo && !normalizar(f.texto).includes(termo)) return false;
    return true;
  });
  if (ord === "curtas") r = [...r].sort((a, b) => a.texto.length - b.texto.length);
  else if (ord === "longas") r = [...r].sort((a, b) => b.texto.length - a.texto.length);
  else if (ord === "tema") r = [...r].sort((a, b) => (a.tema || "").localeCompare(b.tema || "", "pt-BR") || a.id.localeCompare(b.id));
  return r;
}

export function criarAleatorio(semente) {
  if (!semente) return Math.random;
  let a = semente >>> 0; // mulberry32
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Escolhe n frases variadas: no máximo 2 por tema e, havendo, ao menos uma que não seja de exclusão. */
export function sortearSessao(frases, n, aleatorio = Math.random) {
  const embaralhadas = [...frases];
  for (let i = embaralhadas.length - 1; i > 0; i--) {
    const j = Math.floor(aleatorio() * (i + 1));
    [embaralhadas[i], embaralhadas[j]] = [embaralhadas[j], embaralhadas[i]];
  }
  const escolhidas = [];
  const porTema = {};
  const aceita = (f) => (porTema[f.tema] || 0) < 2;
  const pegar = (f) => { escolhidas.push(f); porTema[f.tema] = (porTema[f.tema] || 0) + 1; };
  const primeiraNaoExclusao = embaralhadas.find((f) => f.tipo !== "exclusao");
  if (n >= 3 && primeiraNaoExclusao) pegar(primeiraNaoExclusao);
  for (const f of embaralhadas) {
    if (escolhidas.length >= n) break;
    if (!escolhidas.includes(f) && aceita(f)) pegar(f);
  }
  for (const f of embaralhadas) { // completa se a regra por tema deixou faltando
    if (escolhidas.length >= n) break;
    if (!escolhidas.includes(f)) pegar(f);
  }
  // embaralha de novo para a frase "mais leve" não ser sempre a primeira
  for (let i = escolhidas.length - 1; i > 0; i--) {
    const j = Math.floor(aleatorio() * (i + 1));
    [escolhidas[i], escolhidas[j]] = [escolhidas[j], escolhidas[i]];
  }
  return escolhidas;
}

/** Frase de abertura estável por dia: prefere casos ambíguos, que convidam à reflexão. */
export function fraseDeAbertura(frases, data = new Date()) {
  // frases com aviso de conteúdo (termos pejorativos) nunca são o destaque da página inicial
  const seguras = frases.filter((f) => !f.aviso_conteudo);
  if (!seguras.length) return null;
  frases = seguras;
  const ambiguas = frases.filter((f) => f.tipo === "ambigua");
  const base = ambiguas.length ? ambiguas : frases;
  const dia = Math.floor(Date.UTC(data.getFullYear(), data.getMonth(), data.getDate()) / 86400000);
  return base[dia % base.length];
}

export function proximaFrase(ids, idAtual) {
  if (!ids.length) return null;
  const i = ids.indexOf(idAtual);
  return ids[(i + 1) % ids.length];
}

/** Texto do convite para compartilhar uma frase. Tom de pergunta, sem apontar ninguém e sem dizer o que a pessoa "é". */
export function mensagemCompartilhar(frase, url) {
  // Frase com aviso de conteúdo (termo pejorativo explícito) não é citada na mensagem: vai só o link.
  if (frase.aviso_conteudo) return `Onde você coloca a linha entre opinião e discriminação? Leia esta frase de exemplo, que tem aviso de conteúdo, e diga como você interpreta: ${url}`;
  const limite = 200;
  const t = (frase.texto || "").trim();
  const citacao = t.length > limite ? `${t.slice(0, limite - 1).trimEnd()}…` : t;
  return `Onde você coloca a linha entre opinião e discriminação? Fiquei pensando nesta frase de exemplo: “${citacao}” Leia e diga como você interpreta: ${url}`;
}

export function linkWhatsApp(mensagem) {
  return `https://wa.me/?text=${encodeURIComponent(mensagem)}`;
}

/** Frases de um tema de descoberta (grupo). Grupo vazio = todas. */
export function frasesDoGrupo(frases, grupo) {
  return grupo ? frases.filter((f) => f.grupo === grupo) : frases;
}
