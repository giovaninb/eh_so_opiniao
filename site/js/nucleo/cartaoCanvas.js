/* ImageCard: desenha o cartão compartilhável (Stories/Status 1080×1920 e prévia 1200×630) num <canvas> do próprio navegador.
   Sem serviço externo, sem biblioteca. Frase com aviso de conteúdo NÃO é desenhada: o cartão fica só com a pergunta do projeto. */
import { ajustarTexto } from "./logica.js";

export const FORMATOS = {
  stories: { id: "stories", largura: 1080, altura: 1920, rotulo: "Stories e Status (9:16)", sufixo: "stories" },
  previa: { id: "previa", largura: 1200, altura: 630, rotulo: "Prévia para redes (1200×630)", sufixo: "previa" },
};
const COR = { fundo: "#fbf8f2", tinta: "#1d1a17", suave: "#5a524a", destaque: "#b53a1c", linha: "#e4dccf", faixa: "#fff" };
const SERIF = 'Georgia, "Times New Roman", serif';
const SANS = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';

export function textoAlternativo(f, formato) {
  const base = f.aviso_conteudo
    ? "Cartão do É Só Opinião? com a pergunta: onde termina a opinião e começa a discriminação? A frase tem aviso de conteúdo e não aparece na imagem."
    : `Cartão do É Só Opinião? com a frase de exemplo: “${f.texto}” e a pergunta: opinião ou discriminação?`;
  return `${base} Formato ${formato.rotulo}.`;
}

export function textoAlternativoPar(par, a, b, formato) {
  const cit = (f) => (f.aviso_conteudo ? "uma frase com aviso de conteúdo" : `“${f.texto}”`);
  return `Cartão do É Só Opinião? comparando ${cit(a)} e ${cit(b)}. Pergunta: o que muda de uma para a outra? Formato ${formato.rotulo}.`;
}

function enderecoCurto(url) {
  try { const u = new URL(url); return `${u.host}${u.pathname}`.replace(/\/$/, ""); } catch { return url; }
}

export function desenharCartao(canvas, { formato, frase, url }) {
  const { largura: W, altura: H } = formato;
  const vertical = H > W;
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext("2d");
  const m = vertical ? 96 : 72;
  const util = W - 2 * m;
  ctx.fillStyle = COR.fundo; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = COR.destaque; ctx.fillRect(0, 0, W, vertical ? 24 : 16);
  ctx.textBaseline = "alphabetic"; ctx.textAlign = "left";

  let y = m + (vertical ? 80 : 40);
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${vertical ? 68 : 46}px ${SERIF}`;
  ctx.fillText("É Só Opinião?", m, y);
  y += vertical ? 56 : 38;
  ctx.fillStyle = COR.suave; ctx.font = `400 ${vertical ? 36 : 26}px ${SANS}`;
  ctx.fillText("Onde termina a opinião e começa a discriminação?", m, y, util);

  const comAviso = Boolean(frase.aviso_conteudo);
  const rotulo = comAviso ? "UMA FRASE PARA PENSAR" : "OPINIÃO OU DISCRIMINAÇÃO?";
  y += vertical ? 150 : 72;
  ctx.fillStyle = COR.destaque; ctx.font = `800 ${vertical ? 38 : 26}px ${SANS}`;
  ctx.fillText(rotulo, m, y);

  const textoPrincipal = comAviso ? "Esta frase tem aviso de conteúdo e não aparece aqui. Abra o link para ler com contexto." : `“${frase.texto}”`;
  const areaAltura = (vertical ? H - 480 : H - 150) - y - (vertical ? 60 : 30);
  const maximo = comAviso ? (vertical ? 64 : 40) : (vertical ? 84 : 52);
  const minimo = vertical ? 40 : 28;
  const lh = 1.28;
  const linhasMax = Math.max(2, Math.floor(areaAltura / (minimo * lh)));
  const ajuste = ajustarTexto((t, tam) => { ctx.font = `700 ${tam}px ${SERIF}`; return ctx.measureText(t).width; }, textoPrincipal, util, { maximo, minimo, linhasMax });
  const possiveis = Math.floor(areaAltura / (ajuste.tamanho * lh));
  const linhas = ajuste.linhas.slice(0, Math.max(possiveis, 1));
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${ajuste.tamanho}px ${SERIF}`;
  let yy = y + (vertical ? 36 : 20) + ajuste.tamanho;
  for (const l of linhas) { ctx.fillText(l, m, yy); yy += ajuste.tamanho * lh; }

  const base = H - (vertical ? 120 : 52);
  ctx.strokeStyle = COR.linha; ctx.lineWidth = 3;
  const linhaY = base - (vertical ? 250 : 96);
  ctx.beginPath(); ctx.moveTo(m, linhaY); ctx.lineTo(W - m, linhaY); ctx.stroke();
  ctx.fillStyle = COR.suave; ctx.font = `400 ${vertical ? 34 : 24}px ${SANS}`;
  ctx.fillText(frase.natureza === "ficticio" || !frase.natureza ? "Exemplo fictício · conteúdo educativo" : "Conteúdo educativo", m, linhaY + (vertical ? 60 : 36), util);
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${vertical ? 40 : 28}px ${SANS}`;
  ctx.fillText(vertical ? "Veja o contexto e diga como você lê:" : "Veja o contexto:", m, linhaY + (vertical ? 126 : 70), util);
  ctx.fillStyle = COR.destaque; ctx.font = `800 ${vertical ? 42 : 28}px ${SANS}`;
  ctx.fillText(enderecoCurto(url), m, linhaY + (vertical ? 186 : 104), util);
  if (vertical) { ctx.fillStyle = COR.suave; ctx.font = `400 30px ${SANS}`; ctx.fillText("Exposição Quem Pode Pertencer?", m, H - 56, util); }
  return canvas;
}

function textoDaFrase(f) {
  return f.aviso_conteudo
    ? "Esta frase tem aviso de conteúdo e não aparece aqui. Abra o link."
    : `“${f.texto}”`;
}

function desenharBloco(ctx, { x, y, w, h, letra, frase, vertical }) {
  ctx.fillStyle = "#fff";
  ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = COR.linha;
  ctx.lineWidth = 2;
  ctx.strokeRect(x, y, w, h);
  const pad = vertical ? 28 : 20;
  ctx.fillStyle = COR.destaque;
  ctx.font = `800 ${vertical ? 26 : 18}px ${SANS}`;
  ctx.fillText(`FRASE ${letra}`, x + pad, y + pad + (vertical ? 22 : 16));
  const util = w - 2 * pad;
  const topo = y + pad + (vertical ? 48 : 36);
  const area = h - (topo - y) - pad;
  const maximo = vertical ? 42 : 26;
  const minimo = vertical ? 24 : 16;
  const lh = 1.25;
  const linhasMax = Math.max(2, Math.floor(area / (minimo * lh)));
  const ajuste = ajustarTexto((t, tam) => { ctx.font = `700 ${tam}px ${SERIF}`; return ctx.measureText(t).width; }, textoDaFrase(frase), util, { maximo, minimo, linhasMax });
  ctx.fillStyle = COR.tinta;
  ctx.font = `700 ${ajuste.tamanho}px ${SERIF}`;
  let yy = topo + ajuste.tamanho;
  for (const l of ajuste.linhas) { ctx.fillText(l, x + pad, yy, util); yy += ajuste.tamanho * lh; }
}

export function desenharComparacao(canvas, { formato, par, a, b, url }) {
  const { largura: W, altura: H } = formato;
  const vertical = H > W;
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext("2d");
  const m = vertical ? 80 : 48;
  const util = W - 2 * m;
  ctx.fillStyle = COR.fundo; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = COR.destaque; ctx.fillRect(0, 0, W, vertical ? 24 : 16);
  ctx.textBaseline = "alphabetic"; ctx.textAlign = "left";

  let y = m + (vertical ? 56 : 28);
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${vertical ? 56 : 36}px ${SERIF}`;
  ctx.fillText("É Só Opinião?", m, y);
  y += vertical ? 44 : 28;
  ctx.fillStyle = COR.destaque; ctx.font = `800 ${vertical ? 28 : 18}px ${SANS}`;
  ctx.fillText("DUAS FRASES, UMA DIFERENÇA", m, y, util);
  y += vertical ? 52 : 32;
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${vertical ? 40 : 24}px ${SERIF}`;
  ctx.fillText(par.titulo, m, y, util);

  const rodape = vertical ? 280 : 120;
  const gap = vertical ? 28 : 20;
  const blocoY = y + (vertical ? 36 : 20);
  const blocoH = H - blocoY - rodape;
  if (vertical) {
    const h = (blocoH - gap) / 2;
    desenharBloco(ctx, { x: m, y: blocoY, w: util, h, letra: "A", frase: a, vertical });
    desenharBloco(ctx, { x: m, y: blocoY + h + gap, w: util, h, letra: "B", frase: b, vertical });
  } else {
    const w = (util - gap) / 2;
    desenharBloco(ctx, { x: m, y: blocoY, w, h: blocoH, letra: "A", frase: a, vertical: false });
    desenharBloco(ctx, { x: m + w + gap, y: blocoY, w, h: blocoH, letra: "B", frase: b, vertical: false });
  }

  const base = H - (vertical ? 88 : 36);
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${vertical ? 36 : 22}px ${SANS}`;
  ctx.fillText("O que muda de uma para a outra?", m, base - (vertical ? 88 : 40), util);
  ctx.fillStyle = COR.suave; ctx.font = `400 ${vertical ? 28 : 18}px ${SANS}`;
  ctx.fillText("Exemplo fictício · conteúdo educativo", m, base - (vertical ? 44 : 18), util);
  ctx.fillStyle = COR.destaque; ctx.font = `800 ${vertical ? 32 : 20}px ${SANS}`;
  ctx.fillText(enderecoCurto(url), m, base, util);
  return canvas;
}

function blobDoCanvas(canvas) {
  return new Promise((resolve, reject) => canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("não foi possível gerar a imagem"))), "image/png"));
}

/** Miniatura para a tela (bem menor que 1080×1920). No celular, copiar a imagem da página pega o arquivo
    interno E o recorte visual se os dois tamanhos forem diferentes — por isso a miniatura não é o arquivo de Status. */
function canvasMiniatura(origem, maxLarguraCss) {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const alvo = Math.round(maxLarguraCss * dpr);
  const escala = Math.min(1, alvo / origem.width);
  const mini = document.createElement("canvas");
  mini.width = Math.max(1, Math.round(origem.width * escala));
  mini.height = Math.max(1, Math.round(origem.height * escala));
  mini.getContext("2d").drawImage(origem, 0, 0, mini.width, mini.height);
  return mini;
}

export async function gerarImagem({ formato, frase, par, a, b, url }) {
  const canvas = document.createElement("canvas");
  if (par) desenharComparacao(canvas, { formato, par, a, b, url });
  else desenharCartao(canvas, { formato, frase, url });
  const mini = canvasMiniatura(canvas, formato.id === "stories" ? 280 : 540);
  const [arquivo, previa] = await Promise.all([blobDoCanvas(canvas), blobDoCanvas(mini)]);
  return { arquivo, previa, largura: canvas.width, altura: canvas.height };
}
