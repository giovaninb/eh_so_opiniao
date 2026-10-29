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

/** Convite para compartilhar um caso. Tom de pergunta, sem apontar ninguém e sem dizer o que a pessoa "é".
    A frase NÃO vai no texto: a prévia do link (título e descrição da página do caso) é quem a apresenta, e frases com aviso de
    conteúdo nem ali são citadas. */
export function mensagemCompartilhar(_frase, url) {
  return `Essa frase parece comum, mas o contexto pode mudar a interpretação. Onde você coloca a linha? Veja a análise no É Só Opinião?: ${url}`;
}

export function mensagemComparacao(url) {
  return `Duas frases parecidas podem pedir leituras diferentes. O que muda de uma para a outra? Veja a comparação no É Só Opinião?: ${url}`;
}

export function linkWhatsApp(mensagem) {
  return `https://wa.me/?text=${encodeURIComponent(mensagem)}`;
}

/** Frases de um tema de descoberta (grupo). Grupo vazio = todas. */
export function frasesDoGrupo(frases, grupo) {
  return grupo ? frases.filter((f) => f.grupo === grupo) : frases;
}

/** Quebra um texto em linhas que cabem em `largura`, usando `medir(texto)` (ex.: ctx.measureText). Palavras maiores que a linha ficam sozinhas. */
export function quebrarLinhas(medir, texto, largura) {
  const linhas = [];
  let atual = "";
  for (const palavra of String(texto).split(/\s+/).filter(Boolean)) {
    const tentativa = atual ? `${atual} ${palavra}` : palavra;
    if (atual && medir(tentativa) > largura) { linhas.push(atual); atual = palavra; } else atual = tentativa;
  }
  if (atual) linhas.push(atual);
  return linhas;
}

/** Maior tamanho de fonte (de `maximo` a `minimo`, de 2 em 2) em que o texto cabe em `linhasMax` linhas. */
export function ajustarTexto(medirComTamanho, texto, largura, { maximo, minimo, linhasMax }) {
  for (let tamanho = maximo; tamanho >= minimo; tamanho -= 2) {
    const linhas = quebrarLinhas((t) => medirComTamanho(t, tamanho), texto, largura);
    if (linhas.length <= linhasMax) return { tamanho, linhas };
  }
  const linhas = quebrarLinhas((t) => medirComTamanho(t, minimo), texto, largura).slice(0, linhasMax);
  linhas[linhas.length - 1] = `${linhas[linhas.length - 1].replace(/[\s.,;:!?]+$/, "")}…`;
  return { tamanho: minimo, linhas };
}

/** Nome de arquivo seguro para a imagem de um caso. */
export function nomeArquivoImagem(id, formato) {
  return `eh-so-opiniao-${String(id).toLowerCase().replace(/[^a-z0-9-]+/g, "-")}-${formato}.png`;
}

/** Comparações publicadas em que as duas frases existem (defesa extra no navegador). */
export function paresValidos(pares, porId) {
  return (pares || []).filter((p) => porId.has(p.a) && porId.has(p.b));
}
