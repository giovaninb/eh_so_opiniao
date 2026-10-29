/* EmptyState, LoadingState e ErrorState. */
import { el } from "../nucleo/dom.js";

export function EstadoCarregando(texto = "Carregando…") {
  return el("div", { class: "carregando", role: "status" }, [
    el("span", { class: "visualmente-oculto", text: texto }),
    el("div", { class: "esqueleto", "aria-hidden": "true" }),
    el("div", { class: "esqueleto", "aria-hidden": "true" }),
  ]);
}

export function EstadoVazio({ titulo, texto, acao }) {
  return el("div", { class: "estado", role: "status" }, [
    el("h3", { text: titulo }),
    texto ? el("p", { class: "suave", text: texto }) : null,
    acao ? el("button", { type: "button", class: "botao botao-claro", text: acao.rotulo, onclick: acao.aoClicar }) : null,
  ]);
}

export function EstadoErro({ titulo, texto, aoTentarDeNovo }) {
  return el("div", { class: "estado erro", role: "alert" }, [
    el("h3", { text: titulo }),
    el("p", { text: texto }),
    aoTentarDeNovo ? el("button", { type: "button", class: "botao", text: "Tentar de novo", onclick: aoTentarDeNovo }) : null,
  ]);
}
