/* Vistas "Entender" e "Pesquisa": conteúdo explicativo; os dados pesados só carregam quando a vista abre. */
import { el, limpar } from "../nucleo/dom.js";
import { carregarExtras } from "../nucleo/dados.js";
import { EstadoCarregando, EstadoErro } from "../componentes/estados.js";

const ROTULO_TIPO = { supervisionado: "supervisionada", exploratorio: "exploratória", salvaguarda: "salvaguarda" };

function taxonomia(t) {
  return t.rotulos.map((r) => el("article", { class: "cartao" }, [
    el("h3", { text: r.nome }),
    el("p", { class: "rotulo-tipo", text: ROTULO_TIPO[r.tipo] || r.tipo }),
    el("p", { text: r.definicao }),
    r.nao_e ? el("p", { class: "pequeno suave", text: `Não é: ${r.nao_e}` }) : null,
  ]));
}

function achados(a) {
  const itens = a.gerado_dos_relatorios || [];
  if (!itens.length) return [el("p", { class: "suave", text: "Os experimentos ainda não foram executados neste ambiente." })];
  return itens.map((i) => el("article", { class: "cartao" }, [el("h3", { text: i.titulo }), el("p", { text: i.texto }), el("p", { class: "pequeno suave", text: `Experimento ${i.experimento}` })]));
}

function catalogo(c) {
  return c.map((d) => el("article", { class: "cartao" }, [
    el("h3", { text: d.nome }),
    el("p", { class: "pequeno suave", text: `Licença: ${d.licenca} · ${d.plataforma}` }),
    el("p", { class: "rotulo-tipo", text: d.rotulo_uso || (d.status === "acessado" ? "usada" : `pendente (${String(d.status).replace(/_/g, " ")})`) }),
    d.explicacao_uso ? el("p", { class: "pequeno", text: d.explicacao_uso }) : null,
  ]));
}

function ligacao(url, texto, nome) {
  return el("a", { href: url, rel: "noopener", "aria-label": `${texto}: ${nome}`, text: texto });
}

/** Artigos e fontes das bases catalogadas (inclui as que ainda aguardam fonte oficial). */
function referencias(c) {
  return c.map((d) => el("li", {}, [
    document.createTextNode(`${d.referencia} `),
    ligacao(d.url, "Fonte", d.nome),
    d.url_artigo ? document.createTextNode(" · ") : null,
    d.url_artigo ? ligacao(d.url_artigo, "Artigo", d.nome) : null,
  ]));
}

/** Outros recursos citados; referência teórica é identificada e nunca apresentada como base de dados. */
function outrosRecursos(r) {
  return (r.referencias || []).map((x) => el("li", {}, [
    document.createTextNode(`${x.citacao} `),
    ligacao(x.url, "Acessar", x.titulo),
    el("p", { class: "pequeno suave", text: `${x.eh_dataset_supervisionado === false ? "Referência teórica, não é base de dados. " : ""}${x.papel} Não é: ${x.o_que_nao_e}` }),
  ]));
}

async function preencher(destinos, montar) {
  destinos.forEach((d) => limpar(d, EstadoCarregando("Carregando…")));
  try {
    const dados = await carregarExtras();
    montar(dados);
  } catch {
    destinos.forEach((d) => limpar(d, EstadoErro({ titulo: "Não foi possível carregar esta parte", texto: "Tente de novo.", aoTentarDeNovo: () => preencher(destinos, montar) })));
  }
}

export const entender = {
  titulo: "Entender",
  rotaAtiva: "entender",
  async montar() {
    const tax = document.getElementById("lista-taxonomia");
    const ach = document.getElementById("lista-achados");
    await preencher([tax, ach], ({ taxonomia: t, achados: a }) => {
      limpar(tax, el("div", { class: "cartoes" }, taxonomia(t)));
      limpar(ach, ...achados(a));
    });
  },
};

export const pesquisa = {
  titulo: "Pesquisa",
  rotaAtiva: "pesquisa",
  async montar() {
    const cat = document.getElementById("lista-catalogo");
    const refs = document.getElementById("lista-referencias");
    const outros = document.getElementById("lista-referencias-outros");
    await preencher([cat, refs, outros], ({ catalogo: c, referencias: r }) => {
      limpar(cat, ...catalogo(c));
      limpar(refs, ...referencias(c));
      limpar(outros, ...outrosRecursos(r));
    });
  },
};
