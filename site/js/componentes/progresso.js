/* DiscoveryProgress: "2 de 5 situações", sem pontuação nem ranking. */
import { el } from "../nucleo/dom.js";

export function Progresso(atual, total) {
  const pct = Math.round((atual / total) * 100);
  return el("div", { class: "progresso" }, [
    el("span", { text: `${atual} de ${total} ${total > 1 ? "situações" : "situação"}` }),
    el("span", { class: "progresso-barra", role: "progressbar", "aria-label": "Progresso da sessão", "aria-valuemin": "1", "aria-valuemax": String(total), "aria-valuenow": String(atual) },
      [el("span", { style: `width:${pct}%` })]),
  ]);
}
