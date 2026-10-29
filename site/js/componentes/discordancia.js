/* "Discordo da interpretação": comentário opcional e privado sobre a leitura de uma frase publicada.
   Só existe quando há um serviço de recebimento real configurado (config_participacao.json). Nunca simula envio e
   nunca abre issue pública: o texto vai ao mesmo formulário privado de "Participe", é mascarado e lido por uma pessoa. */
import { el, idUnico } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { mascarar } from "../nucleo/mascara.js";
import { MAX_ENVIOS_POR_VISITA } from "../nucleo/constantes.js";
import { enviar, envioAtivo, ErroEnvio } from "./envio.js";

const MAX = 280;
const ERROS = {
  rede: "Não foi possível falar com o serviço de envio. Verifique a conexão e tente de novo. Seu texto continua aqui.",
  tempo_esgotado: "O envio demorou demais e foi interrompido. Tente de novo. Seu texto continua aqui.",
  servico_recusou: "O serviço recusou o envio. Seu texto continua aqui; tente de novo mais tarde.",
  indisponivel: "O envio não está disponível agora.",
};

export function Discordancia(f) {
  if (!envioAtivo() || (f.revisao && !f.revisao.por_humano)) return null;
  const id = idUnico("disc");
  const campo = el("textarea", { id: `${id}-texto`, rows: "4", maxlength: String(MAX + 40), autocomplete: "off", "aria-describedby": `${id}-dica ${id}-aviso` });
  const aviso = el("p", { class: "pequeno suave", id: `${id}-aviso`, hidden: "" });
  const consentimento = el("input", { type: "checkbox", id: `${id}-ok` });
  const erro = el("p", { class: "erro-campo", id: `${id}-erro`, hidden: "" });
  const armadilha = el("input", { type: "text", tabindex: "-1", autocomplete: "off" });
  const retorno = el("div", { role: "status", "aria-live": "polite" });
  const botao = el("button", { type: "submit", class: "botao botao-claro", text: "Enviar para revisão" });

  campo.addEventListener("input", () => {
    const { tipos } = mascarar(campo.value);
    aviso.hidden = tipos.length === 0;
    aviso.textContent = tipos.length ? `Vamos trocar por marcadores: ${tipos.join(", ")}` : "";
  });

  const form = el("form", { class: "formulario discordancia", novalidate: "" }, [
    el("p", { class: "pequeno suave", id: `${id}-dica`, text: "Conte, com as suas palavras, o que você leria diferente. É opcional. Não escreva nomes, telefones nem dados de ninguém." }),
    el("div", { class: "campo" }, [el("label", { for: `${id}-texto`, text: "O que você leria diferente?" }), campo, aviso]),
    el("label", { class: "escolha" }, [consentimento, " Entendo que o texto vai para um formulário privado, é lido por uma pessoa e não receberei resposta individual."]),
    erro,
    el("div", { class: "armadilha", "aria-hidden": "true" }, [el("label", {}, ["Deixe em branco ", armadilha])]),
    el("p", {}, [botao]),
    retorno,
  ]);
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    retorno.replaceChildren();
    if (armadilha.value) { retorno.append(el("p", { class: "mensagem ok", text: "Obrigado." })); return; }
    const { texto } = mascarar(campo.value);
    erro.hidden = true;
    if (texto.length > MAX) { erro.textContent = `Reduza o texto para até ${MAX} caracteres.`; erro.hidden = false; campo.focus(); return; }
    if (!consentimento.checked) { erro.textContent = "Marque a confirmação para enviar."; erro.hidden = false; consentimento.focus(); return; }
    if (estado.enviosDiscordancia >= MAX_ENVIOS_POR_VISITA) { retorno.append(el("p", { class: "mensagem aviso", text: "Você já enviou o máximo de comentários nesta visita. Obrigado!" })); return; }
    botao.disabled = true; botao.textContent = "Enviando…";
    try {
      const leitura = estado.respostas.get(f.id);
      const resp = await enviar({ tipo: "discordancia", frase: texto, frase_id: f.id, avaliacao: leitura && leitura !== "pulou" ? leitura : "", consentimento: "sim", armadilha: "" });
      estado.enviosDiscordancia += 1;
      campo.value = ""; consentimento.checked = false; aviso.hidden = true;
      retorno.append(el("p", { class: `mensagem ${resp.confirmado ? "ok" : "aviso"}`, text: resp.confirmado
        ? "Recebido. Uma pessoa vai ler. Se a leitura precisar mudar, o caso é corrigido e a página continua no mesmo endereço."
        : "Enviamos ao serviço, mas ele não permite confirmar o recebimento. Não podemos garantir que chegou." }));
    } catch (e) {
      const motivo = e instanceof ErroEnvio ? e.motivo : "rede";
      retorno.append(el("p", { class: "mensagem erro", text: ERROS[motivo] || ERROS.rede }));
    } finally {
      botao.disabled = false; botao.textContent = "Enviar para revisão";
    }
  });
  return el("details", { class: "detalhe discordo" }, [el("summary", { text: "Discordo da interpretação" }), form]);
}
