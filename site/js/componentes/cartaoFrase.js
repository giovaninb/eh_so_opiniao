/* PhraseCard: tema, frase e a pergunta. A análise (PhraseReveal) só aparece depois da resposta ou de um pedido,
   e nunca diz ao visitante que ele "acertou" ou "errou". */
import { el, idUnico, focar } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { AVALIACOES, NOME_AVALIACAO, LEITURA_HUMANA, NATUREZA } from "../nucleo/constantes.js";
import { Enquete } from "./enquete.js";

function nomeTema(f) {
  const t = estado.temas.find((x) => x.id === f.tema);
  return t ? t.nome : "";
}

export function MetaFrase(f) {
  const nat = NATUREZA[f.natureza] || NATUREZA.ficticio;
  return el("p", { class: "meta" }, [
    nomeTema(f) ? el("span", { class: "tema", text: nomeTema(f) }) : null,
    el("span", { class: "natureza", text: f.revisao && !f.revisao.por_humano ? "Rascunho (não revisado)" : nat.rotulo }),
  ]);
}

/** ClassificationExplanation: a sugestão automática fica separada e rotulada como hipótese. */
function SugestaoAutomatica(f) {
  const nomes = (f.ia && f.ia.sinalizou ? f.ia.sinalizou : []).map((r) => r.nome);
  const texto = nomes.length ? `sugeriu: ${nomes.join(", ")}` : "não sinalizou nenhuma categoria";
  return el("details", { class: "detalhe ia" }, [
    el("summary", { text: "Sugestão automática (não é decisão humana)" }),
    el("p", { text: `Um programa simples de regras (${(f.ia && f.ia.metodo) || "baseline"}) ${texto}. É só uma hipótese: a leitura acima foi feita por uma pessoa.` }),
    el("p", { class: "pequeno suave", text: f.ia && f.ia.concorda_com_revisao ? "Neste caso a sugestão coincidiu com a revisão." : "Neste caso a sugestão foi diferente da revisão, e é por isso que toda classificação passa por uma pessoa." }),
  ]);
}

export function Revelacao(f, valor, { rotuloProxima, aoProxima } = {}) {
  const nat = NATUREZA[f.natureza] || NATUREZA.ficticio;
  const rascunho = f.revisao && !f.revisao.por_humano;
  const titulo = el("h3", { text: "A leitura da revisão", tabindex: "-1" });
  const sua = valor === "pulou" ? "Você viu a análise sem responder."
    : valor ? `Você marcou: ${NOME_AVALIACAO[valor]}. A leitura da revisão pode ser diferente, e isso faz parte da discussão.`
      : "Você viu a análise sem responder.";
  const detalhes = el("dl");
  const item = (rotulo, conteudo) => { if (conteudo) detalhes.append(el("div", {}, [el("dt", { text: rotulo }), el("dd", {}, [conteudo])])); };
  item("Contexto", f.contexto ? el("span", { text: f.contexto }) : null);
  item("O que a frase faz", f.mecanismo ? el("span", { text: f.mecanismo }) : null);
  item("Por que essa leitura", f.razoes && f.razoes.length ? el("ul", {}, f.razoes.map((r) => el("li", { text: r }))) : null);
  item("O que poderia mudar a leitura", f.muda_se ? el("span", { text: f.muda_se }) : null);
  item("Rótulos da revisão", f.rotulos && f.rotulos.length ? el("span", { text: f.rotulos.map((r) => r.nome).join(" · ") }) : null);
  const acoes = el("div", { class: "passo-seguinte" });
  if (aoProxima) acoes.append(el("button", { type: "button", class: "botao", text: rotuloProxima || "Próxima frase", onclick: aoProxima }));
  acoes.append(BotaoCompartilhar(f));
  const caixa = el("div", { class: "revelacao" }, [
    titulo,
    el("p", { class: "sua-leitura", text: sua }),
    el("span", { class: `leitura-humana ${f.tipo}`, text: LEITURA_HUMANA[f.tipo] || "" }),
    detalhes,
    el("p", { class: "aviso-natureza", text: rascunho ? "Rascunho local: ainda não foi revisado por uma pessoa." : nat.aviso }),
    SugestaoAutomatica(f),
    Enquete(f.id, valor && valor !== "pulou" ? valor : null),
    acoes,
  ]);
  return { elemento: caixa, titulo };
}

function BotaoCompartilhar(f) {
  const url = `${location.origin}${location.pathname}#/frase/${encodeURIComponent(f.id)}`;
  const retorno = el("span", { class: "pequeno suave", role: "status" });
  const botao = el("button", { type: "button", class: "botao botao-claro", text: "Compartilhar esta frase" });
  botao.addEventListener("click", async () => {
    try {
      if (navigator.share) await navigator.share({ title: "É Só Opinião?", url });
      else { await navigator.clipboard.writeText(url); retorno.textContent = "Link copiado."; }
    } catch (e) {
      if (!e || e.name !== "AbortError") retorno.textContent = `Copie o link: ${url}`;
    }
  });
  return el("div", {}, [botao, retorno]);
}

/**
 * opcoes: { permitirPular, aoPular, aoResponder(valor), rotuloProxima, aoProxima, abertoSemResponder }
 * Retorna { elemento, focar() }.
 */
export function CartaoFrase(f, opcoes = {}) {
  const idFrase = idUnico("frase");
  const idPergunta = idUnico("pergunta");
  const slot = el("div", { "aria-live": "polite" });
  const respostaAtual = () => estado.respostas.get(f.id);
  const botoes = AVALIACOES.map((a) => el("button", {
    type: "button", class: "opcao-resposta", "data-valor": a.valor, "aria-pressed": String(respostaAtual() === a.valor), text: a.rotulo,
    onclick: () => responder(a.valor),
  }));
  const acoes = el("div", { class: "acoes-cartao" });

  function mostrarRevelacao(valor) {
    const r = Revelacao(f, valor, { rotuloProxima: opcoes.rotuloProxima, aoProxima: opcoes.aoProxima });
    slot.replaceChildren(r.elemento);
    acoes.hidden = true;
    return r;
  }
  function responder(valor) {
    estado.respostas.set(f.id, valor);
    botoes.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.valor === valor)));
    const r = mostrarRevelacao(valor);
    focar(r.titulo);
    if (opcoes.aoResponder) opcoes.aoResponder(valor);
  }
  acoes.append(el("button", { type: "button", class: "botao-texto", text: "Ver análise sem responder", onclick: () => { const r = mostrarRevelacao(respostaAtual() || "pulou"); focar(r.titulo); } }));
  if (opcoes.permitirPular) acoes.append(el("button", { type: "button", class: "botao-texto", text: "Pular", onclick: () => opcoes.aoPular && opcoes.aoPular() }));

  const elemento = el("article", { class: "cartao-frase", "aria-labelledby": idFrase, tabindex: "-1" }, [
    MetaFrase(f),
    el("p", { class: "frase", id: idFrase, text: f.texto }),
    el("p", { class: "pergunta", id: idPergunta, text: "O que você acha desta frase?" }),
    el("div", { class: "opcoes", role: "group", "aria-labelledby": idPergunta }, botoes),
    acoes,
    slot,
  ]);
  if (respostaAtual()) mostrarRevelacao(respostaAtual());
  return { elemento, focar: () => focar(elemento) };
}
