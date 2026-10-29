/* DiscoveryThemes: atalhos (Mulheres, Homens e expectativas sociais, Pessoas idosas, Religiões, Pessoas trans…) para
   ler frases de um assunto. É navegação, não pontuação: nada aqui mede ou rotula quem lê. */
import { el } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";

function nomeDoGrupo(id) {
  const g = estado.grupos.find((x) => x.id === id);
  return g ? g.nome : "Ao acaso";
}

export function TemasDescoberta({ aoEscolher }) {
  if (!estado.grupos.length) return null;
  const contagem = {};
  estado.frases.forEach((f) => { if (f.grupo) contagem[f.grupo] = (contagem[f.grupo] || 0) + 1; });
  const opcoes = [{ id: "", nome: "Ao acaso" }, ...estado.grupos.filter((g) => contagem[g.id])];
  const chips = opcoes.map((o) => el("button", {
    type: "button", class: "chip", "data-grupo": o.id, "aria-pressed": String((estado.grupoAtual || "") === o.id),
    text: o.id ? `${o.nome} (${contagem[o.id]})` : o.nome,
    onclick: () => aoEscolher(o.id),
  }));
  return el("details", { class: "detalhe temas-descoberta", open: estado.grupoAtual ? "" : null }, [
    el("summary", { text: `Tema: ${nomeDoGrupo(estado.grupoAtual)}. Escolher outro` }),
    el("div", { class: "chips", role: "group", "aria-label": "Temas para descobrir" }, chips),
  ]);
}

/** Dados de contexto do grupo escolhido (dado, fonte, ano, metodologia e limitações). Fica fechado por padrão. */
export function ContextoDoGrupo(grupo) {
  const itens = (estado.contexto || []).filter((i) => i.grupo === grupo);
  if (!itens.length) return null;
  const blocos = itens.map((i) => {
    const dl = el("dl");
    const linha = (rotulo, valor) => { if (valor) dl.append(el("dt", { text: rotulo }), el("dd", { text: String(valor) })); };
    linha("Dado", i.dado);
    linha("Fonte", i.fonte);
    linha("Ano", i.ano);
    linha("Metodologia", i.metodologia);
    linha("Limitações", i.limitacoes);
    linha("O que foi conferido", i.conferencia);
    if (i.links && i.links.length) {
      dl.append(el("dt", { text: "Links" }), el("dd", {}, i.links.map((l) => el("a", { href: l.url, target: "_blank", rel: "noopener noreferrer", text: l.rotulo, class: "link-externo" }))));
    }
    return el("div", {}, [el("p", { class: "titulo-item", text: i.titulo }), dl]);
  });
  return el("details", { class: "detalhe contexto-dados" }, [el("summary", { text: "Dados e fontes sobre este tema" }), ...blocos]);
}
