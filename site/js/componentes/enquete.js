/* Resultado agregado e envio voluntário do voto. Só mostra números reais e só com o mínimo de leituras. */
import { el } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { AVALIACOES, NOME_AVALIACAO } from "../nucleo/constantes.js";
import { envioAtivo, enviar } from "./envio.js";

export function Enquete(fraseId, valor) {
  const caixa = el("div", { class: "enquete" });
  const r = estado.resultados[fraseId];
  if (r && r.n >= estado.minimoVotos) {
    const pct = (x) => Math.round((100 * x) / r.n) + "%";
    caixa.append(el("p", { text: `Enquete informal (${r.n} leituras): ${AVALIACOES.map((a) => `${a.curto} ${pct(r[a.valor])}`).join(" · ")}. Não representa a população.` }));
  }
  if (valor && envioAtivo() && !estado.votosEnviados.has(fraseId)) {
    const botao = el("button", { type: "button", class: "botao-texto", text: "Contar minha leitura na enquete (anônimo)" });
    const retorno = el("span", { class: "pequeno", role: "status" });
    botao.addEventListener("click", async () => {
      botao.disabled = true;
      try {
        const resp = await enviar({ tipo: "voto", frase_id: fraseId, avaliacao: valor, consentimento: "sim" });
        estado.votosEnviados.add(fraseId);
        botao.remove();
        retorno.textContent = resp.confirmado ? `Leitura enviada (${NOME_AVALIACAO[valor]}). Obrigado.` : `Enviada ao serviço (${NOME_AVALIACAO[valor]}); ele não permite confirmar o recebimento.`;
      } catch {
        botao.disabled = false;
        retorno.textContent = "Não foi possível enviar agora. Tente de novo.";
      }
    });
    caixa.append(botao, retorno);
  }
  return caixa;
}
