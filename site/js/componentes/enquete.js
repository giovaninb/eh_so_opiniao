/* Resultado agregado público. Avaliações da visita NÃO são enviadas daqui: só um lote voluntário, se a pessoa quiser. */
import { el } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { AVALIACOES } from "../nucleo/constantes.js";

export function Enquete(fraseId) {
  const caixa = el("div", { class: "enquete" });
  const r = estado.resultados[fraseId];
  if (r && r.n >= estado.minimoVotos) {
    const pct = (x) => Math.round((100 * x) / r.n) + "%";
    caixa.append(el("p", { text: `Enquete informal (${r.n} leituras): ${AVALIACOES.map((a) => `${a.curto} ${pct(r[a.valor])}`).join(" · ")}. Amostra voluntária, não representa a população.` }));
  }
  return caixa;
}
