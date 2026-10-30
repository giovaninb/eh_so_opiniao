/* ImageCard: desenha o cartão compartilhável (Stories/Status 1080×1920 e prévia 1200×630) num <canvas> do próprio navegador.
   Sem serviço externo, sem biblioteca. Frase com aviso de conteúdo NÃO é desenhada.
   Não leva endereço do site: o cartão é autônomo (CC BY 4.0 · Giovani Bettoni + LinkedIn). */
import { ajustarTexto } from "./logica.js";
import { AUTORIA } from "./constantes.js?v=7";

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
  return `${base} ${AUTORIA.linha}. Formato ${formato.rotulo}.`;
}

export function textoAlternativoPar(par, a, b, formato) {
  const cit = (f) => (f.aviso_conteudo ? "uma frase com aviso de conteúdo" : `“${f.texto}”`);
  return `Cartão do É Só Opinião? comparando ${cit(a)} e ${cit(b)}. O que muda: ${par.diferenca} ${AUTORIA.linha}. Formato ${formato.rotulo}.`;
}

function textoDaFrase(f) {
  return f.aviso_conteudo
    ? "Esta frase tem aviso de conteúdo e não aparece nesta imagem."
    : `“${f.texto}”`;
}

function wrap(ctx, texto, largura, { peso, familia, maximo, minimo, linhasMax }) {
  return ajustarTexto((t, tam) => { ctx.font = `${peso} ${tam}px ${familia}`; return ctx.measureText(t).width; }, texto, largura, { maximo, minimo, linhasMax });
}

function metricasBloco(ctx, { w, frase, vertical, maximo, minimo, linhasMax }) {
  const pad = vertical ? 36 : 16;
  const rotulo = vertical ? 26 : 15;
  const util = w - 2 * pad;
  const ajuste = wrap(ctx, textoDaFrase(frase), util, {
    peso: "700",
    familia: SERIF,
    maximo: maximo ?? (vertical ? 44 : 22),
    minimo: minimo ?? (vertical ? 26 : 15),
    linhasMax: linhasMax ?? (vertical ? 6 : 5),
  });
  const lh = 1.28;
  const primeira = pad + rotulo + (vertical ? 18 : 10) + ajuste.tamanho;
  const ultima = primeira + (ajuste.linhas.length - 1) * ajuste.tamanho * lh;
  return { pad, rotulo, ajuste, lh, h: ultima + pad + ajuste.tamanho * 0.35 };
}

function desenharBloco(ctx, { x, y, w, h, letra, frase, vertical, met }) {
  const m = met || metricasBloco(ctx, { w, frase, vertical });
  const altura = h || m.h;
  ctx.fillStyle = "#fff";
  ctx.fillRect(x, y, w, altura);
  ctx.strokeStyle = COR.linha;
  ctx.lineWidth = 2;
  ctx.strokeRect(x, y, w, altura);
  ctx.fillStyle = COR.destaque;
  ctx.font = `800 ${m.rotulo}px ${SANS}`;
  ctx.fillText(`FRASE ${letra}`, x + m.pad, y + m.pad + m.rotulo);
  ctx.fillStyle = COR.tinta;
  ctx.font = `700 ${m.ajuste.tamanho}px ${SERIF}`;
  let yy = y + m.pad + m.rotulo + (vertical ? 16 : 10) + m.ajuste.tamanho;
  for (const l of m.ajuste.linhas) {
    ctx.fillText(l, x + m.pad, yy, w - 2 * m.pad);
    yy += m.ajuste.tamanho * m.lh;
  }
  return altura;
}

function alturaDiferenca(ctx, { w, texto, vertical, maximo, minimo, linhasMax }) {
  const titulo = vertical ? 30 : 15;
  const minFont = minimo ?? (vertical ? 26 : 13);
  const maxFont = maximo ?? (vertical ? 38 : 17);
  const lh = 1.35;
  const pad = vertical ? 32 : 14;
  const padX = vertical ? 40 : 16;
  const gapTitulo = vertical ? 18 : 8;
  const ajuste = wrap(ctx, texto || "", w - 2 * padX, {
    peso: "400",
    familia: SANS,
    maximo: maxFont,
    minimo: minFont,
    linhasMax: linhasMax ?? (vertical ? 12 : 6),
  });
  const corpo = ajuste.linhas.length * ajuste.tamanho * lh;
  return { titulo, pad, padX, gapTitulo, ajuste, lh, h: pad + titulo + gapTitulo + corpo + pad };
}

function desenharDiferenca(ctx, { x, y, w, texto, vertical, met }) {
  const m = met || alturaDiferenca(ctx, { w, texto, vertical });
  ctx.fillStyle = "#f3eee4";
  ctx.fillRect(x, y, w, m.h);
  ctx.fillStyle = COR.destaque;
  ctx.fillRect(x, y, vertical ? 10 : 5, m.h);
  ctx.font = `800 ${m.titulo}px ${SANS}`;
  ctx.fillText("O QUE MUDA", x + m.padX, y + m.pad + m.titulo);
  ctx.fillStyle = COR.tinta;
  ctx.font = `400 ${m.ajuste.tamanho}px ${SANS}`;
  let yy = y + m.pad + m.titulo + m.gapTitulo + m.ajuste.tamanho;
  for (const l of m.ajuste.linhas) {
    ctx.fillText(l, x + m.padX, yy, w - 2 * m.padX);
    yy += m.ajuste.tamanho * m.lh;
  }
  return m.h;
}

function encaixarVertical(ctx, { util, a, b, diferenca, disponivel }) {
  const tentativas = [
    { fraseMax: 44, fraseMin: 28, fraseLinhas: 5, difMax: 38, difMin: 28, difLinhas: 10, gap: 28 },
    { fraseMax: 40, fraseMin: 26, fraseLinhas: 6, difMax: 34, difMin: 26, difLinhas: 11, gap: 22 },
    { fraseMax: 36, fraseMin: 24, fraseLinhas: 6, difMax: 30, difMin: 24, difLinhas: 12, gap: 18 },
    { fraseMax: 32, fraseMin: 22, fraseLinhas: 7, difMax: 26, difMin: 20, difLinhas: 12, gap: 16 },
  ];
  let escolhido;
  for (const t of tentativas) {
    const metA = metricasBloco(ctx, { w: util, frase: a, vertical: true, maximo: t.fraseMax, minimo: t.fraseMin, linhasMax: t.fraseLinhas });
    const metB = metricasBloco(ctx, { w: util, frase: b, vertical: true, maximo: t.fraseMax, minimo: t.fraseMin, linhasMax: t.fraseLinhas });
    const metD = alturaDiferenca(ctx, { w: util, texto: diferenca, vertical: true, maximo: t.difMax, minimo: t.difMin, linhasMax: t.difLinhas });
    const h = metA.h + metB.h + metD.h + 2 * t.gap;
    escolhido = { metA, metB, metD, gap: t.gap, h };
    if (h <= disponivel) break;
  }
  const extra = Math.max(0, disponivel - escolhido.h);
  const gap = escolhido.gap + Math.min(20, extra / 4);
  const usado = escolhido.metA.h + escolhido.metB.h + escolhido.metD.h + 2 * gap;
  return { ...escolhido, gap, folgaTopo: Math.max(0, (disponivel - usado) / 2) };
}

function alturaCredito(vertical) {
  return vertical ? 150 : 78;
}

function desenharCredito(ctx, { m, y, util, vertical, natureza }) {
  const ficticio = natureza === "ficticio" || !natureza;
  ctx.fillStyle = COR.suave;
  ctx.font = `400 ${vertical ? 24 : 14}px ${SANS}`;
  ctx.fillText(ficticio ? "Exemplo fictício · conteúdo educativo" : "Conteúdo educativo", m, y, util);
  y += vertical ? 34 : 20;
  ctx.fillStyle = COR.tinta;
  ctx.font = `700 ${vertical ? 26 : 15}px ${SANS}`;
  ctx.fillText(AUTORIA.linha, m, y, util);
  y += vertical ? 32 : 18;
  ctx.fillStyle = COR.destaque;
  ctx.font = `600 ${vertical ? 24 : 14}px ${SANS}`;
  ctx.fillText(AUTORIA.linkedin, m, y, util);
}

export function desenharCartao(canvas, { formato, frase }) {
  const { largura: W, altura: H } = formato;
  const vertical = H > W;
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext("2d");
  const m = vertical ? 96 : 56;
  const util = W - 2 * m;
  ctx.fillStyle = COR.fundo; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = COR.destaque; ctx.fillRect(0, 0, W, vertical ? 24 : 16);
  ctx.textBaseline = "alphabetic"; ctx.textAlign = "left";

  let y = m + (vertical ? 80 : 36);
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${vertical ? 68 : 40}px ${SERIF}`;
  ctx.fillText("É Só Opinião?", m, y);
  y += vertical ? 56 : 32;
  ctx.fillStyle = COR.suave; ctx.font = `400 ${vertical ? 36 : 22}px ${SANS}`;
  ctx.fillText("Onde termina a opinião e começa a discriminação?", m, y, util);

  const comAviso = Boolean(frase.aviso_conteudo);
  const rotulo = comAviso ? "UMA FRASE PARA PENSAR" : "OPINIÃO OU DISCRIMINAÇÃO?";
  y += vertical ? 120 : 48;
  ctx.fillStyle = COR.destaque; ctx.font = `800 ${vertical ? 38 : 22}px ${SANS}`;
  ctx.fillText(rotulo, m, y);

  const creditoH = alturaCredito(vertical);
  const textoPrincipal = textoDaFrase(frase);
  const areaAltura = H - creditoH - y - (vertical ? 80 : 36);
  const ajuste = wrap(ctx, textoPrincipal, util, {
    peso: "700", familia: SERIF,
    maximo: comAviso ? (vertical ? 64 : 36) : (vertical ? 84 : 44),
    minimo: vertical ? 40 : 22,
    linhasMax: Math.max(2, Math.floor(areaAltura / ((vertical ? 40 : 22) * 1.28))),
  });
  const lh = 1.28;
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${ajuste.tamanho}px ${SERIF}`;
  let yy = y + (vertical ? 36 : 18) + ajuste.tamanho;
  for (const l of ajuste.linhas) { ctx.fillText(l, m, yy); yy += ajuste.tamanho * lh; }

  const linhaY = H - creditoH - (vertical ? 36 : 16);
  ctx.strokeStyle = COR.linha; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(m, linhaY); ctx.lineTo(W - m, linhaY); ctx.stroke();
  desenharCredito(ctx, { m, y: linhaY + (vertical ? 44 : 24), util, vertical, natureza: frase.natureza });
  return canvas;
}

export function desenharComparacao(canvas, { formato, par, a, b }) {
  const { largura: W, altura: H } = formato;
  const vertical = H > W;
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext("2d");
  const m = vertical ? 72 : 40;
  const util = W - 2 * m;
  ctx.fillStyle = COR.fundo; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = COR.destaque; ctx.fillRect(0, 0, W, vertical ? 24 : 12);
  ctx.textBaseline = "alphabetic"; ctx.textAlign = "left";

  let y = m + (vertical ? 48 : 22);
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${vertical ? 52 : 28}px ${SERIF}`;
  ctx.fillText("É Só Opinião?", m, y);
  y += vertical ? 40 : 22;
  ctx.fillStyle = COR.destaque; ctx.font = `800 ${vertical ? 24 : 14}px ${SANS}`;
  ctx.fillText("DUAS FRASES, UMA DIFERENÇA", m, y, util);
  y += vertical ? 44 : 22;
  ctx.fillStyle = COR.tinta; ctx.font = `700 ${vertical ? 34 : 20}px ${SERIF}`;
  ctx.fillText(par.titulo, m, y, util);
  y += vertical ? 28 : 16;

  const creditoH = alturaCredito(vertical);
  const yCredito = H - creditoH + (vertical ? 28 : 18);
  const gap = vertical ? 22 : 14;
  const diferenca = par.diferenca || "";

  if (vertical) {
    const disponivel = yCredito - 28 - y;
    const lote = encaixarVertical(ctx, { util, a, b, diferenca, disponivel });
    const yA = y + lote.folgaTopo;
    const yDif = yA + lote.metA.h + lote.gap;
    const yB = yDif + lote.metD.h + lote.gap;
    desenharBloco(ctx, { x: m, y: yA, w: util, letra: "A", frase: a, vertical: true, met: lote.metA });
    desenharDiferenca(ctx, { x: m, y: yDif, w: util, texto: diferenca, vertical: true, met: lote.metD });
    desenharBloco(ctx, { x: m, y: yB, w: util, letra: "B", frase: b, vertical: true, met: lote.metB });
  } else {
    const wBox = (util - gap) / 2;
    const metA = metricasBloco(ctx, { w: wBox, frase: a, vertical: false });
    const metB = metricasBloco(ctx, { w: wBox, frase: b, vertical: false });
    const hBox = Math.max(metA.h, metB.h);
    desenharBloco(ctx, { x: m, y, w: wBox, h: hBox, letra: "A", frase: a, vertical: false, met: metA });
    desenharBloco(ctx, { x: m + wBox + gap, y, w: wBox, h: hBox, letra: "B", frase: b, vertical: false, met: metB });
    const yDif = y + hBox + gap;
    const hDifMax = Math.max(48, yCredito - 16 - yDif);
    const metD = alturaDiferenca(ctx, { w: util, texto: diferenca, vertical: false });
    const linhasMax = metD.h > hDifMax
      ? Math.max(2, Math.floor((hDifMax - 36) / (13 * 1.35)))
      : undefined;
    const metFit = linhasMax ? alturaDiferenca(ctx, { w: util, texto: diferenca, vertical: false, linhasMax }) : metD;
    const yDifDesenho = yDif + Math.max(0, (hDifMax - metFit.h) / 2);
    desenharDiferenca(ctx, { x: m, y: yDifDesenho, w: util, texto: diferenca, vertical: false, met: metFit });
  }

  ctx.strokeStyle = COR.linha; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(m, yCredito - (vertical ? 22 : 14)); ctx.lineTo(W - m, yCredito - (vertical ? 22 : 14)); ctx.stroke();
  desenharCredito(ctx, { m, y: yCredito, util, vertical, natureza: "ficticio" });
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

export async function gerarImagem({ formato, frase, par, a, b }) {
  const canvas = document.createElement("canvas");
  if (par) desenharComparacao(canvas, { formato, par, a, b });
  else desenharCartao(canvas, { formato, frase });
  const mini = canvasMiniatura(canvas, formato.id === "stories" ? 280 : 540);
  const [arquivo, previa] = await Promise.all([blobDoCanvas(canvas), blobDoCanvas(mini)]);
  return { arquivo, previa, largura: canvas.width, altura: canvas.height };
}
