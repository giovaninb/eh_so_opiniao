import { el, limpar, focar } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { paresValidos } from "../nucleo/logica.js";
import { Comparacao } from "../componentes/comparacao.js";
import { EstadoErro, EstadoVazio } from "../componentes/estados.js";

function lista(corpo, pares) {
  limpar(corpo, el("ul", { class: "lista-pares" }, pares.map((p) => el("li", {}, [
    el("a", { class: "atalho", href: `#/comparar/${encodeURIComponent(p.slug)}` }, [el("span", { class: "t" }, [el("strong", { text: p.titulo }), el("span", { text: "Duas frases para comparar." })])]),
  ]))));
}

export const comparar = {
  titulo: "Duas frases, uma diferença",
  rotaAtiva: "descobrir",
  async montar({ param }) {
    const corpo = document.getElementById("comparar-corpo");
    corpo.setAttribute("aria-busy", "false");
    if (estado.erro) { limpar(corpo, EstadoErro({ titulo: "Não foi possível carregar as frases", texto: "Tente de novo em instantes.", aoTentarDeNovo: () => location.reload() })); return; }
    const pares = paresValidos(estado.pares, estado.porId);
    if (!pares.length) {
      limpar(corpo, EstadoVazio({ titulo: "Ainda não há comparações revisadas", texto: "Cada comparação só aparece depois de revisada por uma pessoa e com as duas frases publicadas.", acao: { rotulo: "Descobrir frases", aoClicar: () => { location.hash = "#/descobrir"; } } }));
      return;
    }
    if (!param) { lista(corpo, pares); return; }
    const par = pares.find((p) => p.slug === param);
    if (!par) {
      document.title = "Comparação não encontrada — É Só Opinião?";
      limpar(corpo, EstadoVazio({ titulo: "Não encontramos essa comparação", texto: "O link pode estar errado, ou a comparação ainda não foi revisada.", acao: { rotulo: "Ver as comparações", aoClicar: () => { location.hash = "#/comparar"; } } }));
      return;
    }
    document.title = `${par.titulo} — É Só Opinião?`;
    const i = pares.indexOf(par);
    const proximo = pares[(i + 1) % pares.length];
    const c = Comparacao(par, estado.porId.get(par.a), estado.porId.get(par.b), pares.length > 1 ? { aoProxima: () => { location.hash = `#/comparar/${encodeURIComponent(proximo.slug)}`; } } : {});
    limpar(corpo, el("p", {}, [el("a", { href: "#/comparar", class: "botao-texto", style: "padding-left:0", text: "← Todas as comparações" })]), c.elemento);
    focar(c.titulo);
  },
};
