import { el, limpar, focar } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { NOME_AVALIACAO, TAMANHO_SESSAO } from "../nucleo/constantes.js";
import { criarAleatorio, sortearSessao, frasesDoGrupo, frasesDoAssunto, assuntoPorId } from "../nucleo/logica.js";
import { CartaoFrase } from "../componentes/cartaoFrase.js?v=9";
import { Progresso } from "../componentes/progresso.js";
import { TemasDescoberta, ContextoDoGrupo } from "../componentes/temasDescoberta.js";
import { EstadoErro, EstadoVazio } from "../componentes/estados.js";

function baseDaSessao() {
  const assunto = assuntoPorId(estado.camadaAssuntos, estado.assuntoAtual);
  if (assunto && assunto.visivel) return frasesDoAssunto(estado.frases, assunto);
  return frasesDoGrupo(estado.frases, estado.grupoAtual);
}

function novaSessao() {
  const base = baseDaSessao();
  const n = Math.min(TAMANHO_SESSAO, base.length);
  estado.sessao = { itens: sortearSessao(base, n, criarAleatorio(estado.semente)), indice: 0, historico: [], grupo: estado.grupoAtual, assunto: estado.assuntoAtual };
}

function escolherTema(corpo, grupo) {
  estado.grupoAtual = grupo;
  estado.assuntoAtual = "";
  novaSessao();
  desenhar(corpo, { focarCartao: true });
}

function cabecalho(corpo) {
  const assunto = assuntoPorId(estado.camadaAssuntos, estado.assuntoAtual);
  const grupoContexto = estado.grupoAtual || (assunto && (assunto.grupos_legado || [])[0]) || "";
  return [
    TemasDescoberta({ aoEscolher: (g) => escolherTema(corpo, g), assunto }),
    grupoContexto ? ContextoDoGrupo(grupoContexto) : null,
  ];
}

function fim(corpo, s) {
  const contagem = {};
  s.historico.forEach((h) => { contagem[h] = (contagem[h] || 0) + 1; });
  const linhas = Object.keys(NOME_AVALIACAO).filter((k) => contagem[k]).map((k) => `${contagem[k]} ${NOME_AVALIACAO[k]}`);
  if (contagem.pulou) linhas.push(`${contagem.pulou} pulada${contagem.pulou > 1 ? "s" : ""}`);
  const titulo = el("h2", { text: "Você chegou ao fim desta sequência", tabindex: "-1" });
  const assunto = assuntoPorId(estado.camadaAssuntos, s.assunto);
  const relacionados = ((assunto && assunto.relacionados) || []).map((id) => assuntoPorId(estado.camadaAssuntos, id)).filter((a) => a && a.visivel);
  limpar(corpo, ...cabecalho(corpo), el("section", { class: "fim-sessao", "aria-labelledby": "titulo-fim" }, [
    Object.assign(titulo, { id: "titulo-fim" }),
    el("p", { text: `Você leu ${s.itens.length} frase${s.itens.length > 1 ? "s" : ""}${linhas.length ? ": " + linhas.join(", ") : ""}. Isso não é uma nota: é só o seu percurso.` }),
    el("p", { class: "suave", text: "Se alguma frase te fez pensar, conte como você a lê, sem identificar ninguém." }),
    relacionados.length ? el("p", {}, ["Assuntos relacionados: ", ...relacionados.flatMap((a, i) => [i ? ", " : "", el("a", { href: a.url, text: a.nome })])]) : null,
    el("div", { class: "passo-seguinte" }, [
      el("button", { type: "button", class: "botao", text: (estado.assuntoAtual || estado.grupoAtual) ? "Mais frases deste tema" : "Mais cinco frases", onclick: () => { novaSessao(); desenhar(corpo); } }),
      el("a", { class: "botao botao-claro", href: "#/explorar", text: "Explorar a biblioteca" }),
      el("a", { class: "botao botao-claro", href: "#/participar", text: "Participar com uma frase" }),
    ]),
  ]));
  focar(titulo);
}

function desenhar(corpo, { focarCartao = false } = {}) {
  const s = estado.sessao;
  if (!s.itens.length) {
    limpar(corpo, ...cabecalho(corpo), EstadoVazio({ titulo: "Não há frases publicadas neste assunto", texto: "Assuntos sem exemplos aprovados não abrem uma sequência vazia.", acao: { rotulo: "Escolher outro assunto", aoClicar: () => { location.hash = "#/assuntos"; } } }));
    return;
  }
  if (s.indice >= s.itens.length) { fim(corpo, s); return; }
  const f = s.itens[s.indice];
  const ultima = s.indice === s.itens.length - 1;
  const avancar = (resposta) => { s.historico.push(resposta || estado.respostas.get(f.id) || "pulou"); s.indice += 1; desenhar(corpo, { focarCartao: true }); window.scrollTo(0, 0); };
  const cartao = CartaoFrase(f, {
    permitirPular: true, aoPular: () => avancar("pulou"),
    rotuloProxima: ultima ? "Concluir" : "Próxima frase", aoProxima: () => avancar(),
  });
  limpar(corpo, ...cabecalho(corpo), Progresso(s.indice + 1, s.itens.length), cartao.elemento);
  if (focarCartao) cartao.focar();
}

export const descobrir = {
  titulo: "Descobrir",
  rotaAtiva: "descobrir",
  async montar({ consulta } = {}) {
    const corpo = document.getElementById("descobrir-corpo");
    corpo.setAttribute("aria-busy", "false");
    if (estado.erro) { limpar(corpo, EstadoErro({ titulo: "Não foi possível carregar as frases", texto: "Tente de novo em instantes.", aoTentarDeNovo: () => location.reload() })); return; }
    if (!estado.frases.length) { limpar(corpo, EstadoVazio({ titulo: "Ainda não há frases revisadas", texto: "Nada é publicado antes da revisão por uma pessoa." })); return; }
    const pedidoAssunto = consulta && consulta.get("assunto");
    const pedidoTema = consulta && consulta.get("tema");
    const assunto = assuntoPorId(estado.camadaAssuntos, pedidoAssunto);
    if (assunto && assunto.visivel) {
      if (estado.assuntoAtual !== pedidoAssunto) { estado.assuntoAtual = pedidoAssunto; estado.grupoAtual = ""; novaSessao(); }
    } else if (pedidoTema && estado.grupos.some((g) => g.id === pedidoTema)) {
      if (estado.grupoAtual !== pedidoTema || estado.assuntoAtual) { estado.grupoAtual = pedidoTema; estado.assuntoAtual = ""; novaSessao(); }
    }
    if (!estado.sessao || estado.sessao.indice >= (estado.sessao.itens || []).length) novaSessao();
    desenhar(corpo);
  },
};
