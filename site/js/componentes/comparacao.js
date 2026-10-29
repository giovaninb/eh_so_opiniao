/* ComparisonCard: "Duas frases, uma diferença". Mostra as duas frases lado a lado (empilhadas no celular), deixa abrir a
   leitura de cada uma e só depois revela o que muda. Ninguém precisa responder; nada vira nota. */
import { el, idUnico, focar } from "../nucleo/dom.js";
import { LEITURA_HUMANA } from "../nucleo/constantes.js";
import { CompartilharComparacao } from "./compartilhar.js";

function CartaFrase(f, letra) {
  const id = idUnico("par");
  const detalhes = el("dl");
  const item = (rotulo, valor) => { if (valor) detalhes.append(el("div", {}, [el("dt", { text: rotulo }), el("dd", { text: valor })])); };
  item("O que a frase faz", f.mecanismo);
  item("O que poderia mudar a leitura", f.muda_se);
  return el("article", { class: "carta-par", "aria-labelledby": id }, [
    el("p", { class: "rotulo-par", text: `Frase ${letra}` }),
    f.aviso_conteudo ? el("p", { class: "aviso-conteudo", role: "note" }, [el("strong", { text: "Aviso de conteúdo: " }), "esta frase usa ou cita linguagem pejorativa, só para estudo."]) : null,
    el("p", { class: "frase", id, text: f.texto }),
    el("details", { class: "detalhe" }, [
      el("summary", { text: "Ver a leitura da revisão desta frase" }),
      el("p", { class: `leitura-humana ${f.tipo}`, text: LEITURA_HUMANA[f.tipo] || "" }),
      detalhes,
    ]),
  ]);
}

export function Comparacao(par, a, b, { aoProxima } = {}) {
  const titulo = el("h2", { text: par.titulo, tabindex: "-1" });
  const revelacao = el("div", { class: "revelacao-par", "aria-live": "polite" });
  const botao = el("button", {
    type: "button", class: "botao", text: "Ver o que muda",
    onclick: () => {
      const t = el("h3", { text: "O que muda de uma frase para a outra", tabindex: "-1" });
      revelacao.replaceChildren(el("div", { class: "revelacao" }, [
        t,
        el("p", { text: par.diferenca }),
        el("p", { class: "suave", text: `Limite desta comparação: ${par.limite}` }),
        el("p", { class: "aviso-natureza", text: "Exemplos escritos para fins educativos. A leitura foi revisada por uma pessoa e pode ser questionada." }),
        aoProxima ? el("div", { class: "passo-seguinte" }, [el("button", { type: "button", class: "botao botao-claro", text: "Outra comparação", onclick: aoProxima })]) : null,
      ]));
      botao.hidden = true;
      focar(t);
    },
  });
  const elemento = el("section", { class: "comparacao-par", "aria-labelledby": "titulo-par" }, [
    Object.assign(titulo, { id: "titulo-par" }),
    el("p", { class: "pergunta", text: "O que muda de uma frase para a outra?" }),
    el("div", { class: "comparacao" }, [CartaFrase(a, "A"), CartaFrase(b, "B")]),
    el("div", { class: "acoes-cartao" }, [botao]),
    revelacao,
    CompartilharComparacao(par, a, b),
  ]);
  return { elemento, titulo };
}
