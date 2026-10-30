/* "Discordo da interpretação": comentário opcional e privado. Só existe com serviço real configurado.
   Nunca simula envio nem abre issue pública. O texto vai ao formulário privado, é mascarado e lido por uma pessoa. */
import { el, idUnico } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { mascarar } from "../nucleo/mascara.js";
import { MAX_ENVIOS_POR_VISITA } from "../nucleo/constantes.js";
import { SCHEMA_PARTICIPACAO, AVISO_VERSAO } from "../nucleo/sessaoContribuicao.js";
import { guardaInteracao } from "../nucleo/protecao.js";
import { enviar, envioAtivo, ErroEnvio, provedorCloudflare } from "./envio.js";
import { prepararDesafio } from "./desafio.js";

const MAX = 280;
const MOTIVOS = [
  ["falta_contexto", "Falta contexto"],
  ["discordo_classificacao", "Discordo da classificação"],
  ["explicacao_incompleta", "A explicação está incompleta"],
  ["interpretacao_excessiva", "A frase foi interpretada de maneira excessiva"],
  ["erro_no_texto", "Existe um erro no texto"],
  ["outro", "Outro motivo"],
];
const ERROS = {
  rede: "Não foi possível falar com o serviço de envio. Verifique a conexão e tente de novo. Seu texto continua aqui.",
  tempo_esgotado: "O envio demorou demais e foi interrompido. Tente de novo. Seu texto continua aqui.",
  servico_recusou: "O serviço recusou o envio. Seu texto continua aqui; tente de novo mais tarde.",
  cota: "O formulário atingiu o limite mensal de envios. Você pode continuar lendo; as contribuições voltam quando a operadora reabrir.",
  payload: "O texto ficou grande demais para enviar. Encurte e tente de novo.",
  limite_visita: "Você já enviou o máximo nesta visita. O site continua funcionando; obrigado.",
  indisponivel: "O serviço está temporariamente indisponível. Seu texto continua aqui; você pode tentar de novo.",
  turnstile: "Não foi possível confirmar a proteção. Tente de novo. Seu texto continua aqui.",
  validacao: "Há um campo que precisa ser ajustado. Seu texto continua aqui.",
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
  const desafio = el("div", { class: "desafio-humano", hidden: "" });
  if (provedorCloudflare() && estado.config.turnstile_sitekey) {
    desafio.hidden = false;
    prepararDesafio(desafio, estado.config.turnstile_sitekey).catch(() => {});
  }
  const radios = MOTIVOS.map(([valor, rotulo]) => el("label", { class: "escolha" }, [
    el("input", { type: "radio", name: `${id}-motivo`, value: valor }),
    ` ${rotulo}`,
  ]));

  const guarda = guardaInteracao(campo, ...radios.map((l) => l.querySelector("input")));
  campo.addEventListener("input", () => {
    const { tipos } = mascarar(campo.value);
    aviso.hidden = tipos.length === 0;
    aviso.textContent = tipos.length ? `Vamos trocar por marcadores: ${tipos.join(", ")}` : "";
  });

  const form = el("form", { class: "formulario discordancia", novalidate: "" }, [
    el("p", { class: "pequeno suave", id: `${id}-dica`, text: "Explique o que você leria diferente, escolha um motivo, ou os dois. Não escreva nomes, telefones, endereços nem dados de ninguém. Não publicamos isto e não enviamos resposta individual." }),
    el("fieldset", { class: "campo" }, [el("legend", { text: "Motivo (opcional)" }), ...radios]),
    el("div", { class: "campo" }, [el("label", { for: `${id}-texto`, text: "O que você leria diferente?" }), campo, aviso]),
    el("label", { class: "escolha" }, [consentimento, " Entendo que o texto vai para um formulário privado, é lido por uma pessoa e não receberei resposta individual."]),
    erro,
    el("div", { class: "armadilha", "aria-hidden": "true" }, [el("label", {}, ["Deixe em branco ", armadilha])]),
    desafio,
    el("p", {}, [botao]),
    retorno,
  ]);
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (botao.disabled) return;
    retorno.replaceChildren();
    if (armadilha.value) { retorno.append(el("p", { class: "mensagem ok", text: "Obrigado." })); return; }
    const { texto } = mascarar(campo.value);
    const motivoEl = form.querySelector(`input[name="${id}-motivo"]:checked`);
    const motivo = motivoEl ? motivoEl.value : "";
    erro.hidden = true;
    if (texto.length > MAX) { erro.textContent = `Reduza o texto para até ${MAX} caracteres.`; erro.hidden = false; campo.focus(); return; }
    if (!texto && !motivo) { erro.textContent = "Escreva o que você leria diferente ou escolha um motivo."; erro.hidden = false; campo.focus(); return; }
    if (!consentimento.checked) { erro.textContent = "Marque a confirmação para enviar."; erro.hidden = false; consentimento.focus(); return; }
    if (estado.enviosDiscordancia >= MAX_ENVIOS_POR_VISITA) { retorno.append(el("p", { class: "mensagem aviso", text: "Você já enviou o máximo de comentários nesta visita. Obrigado!" })); return; }
    if (!guarda.ok()) { retorno.append(el("p", { class: "mensagem ok", text: "Obrigado." })); return; }
    botao.disabled = true; botao.textContent = "Validando…";
    try {
      const leitura = estado.respostas.get(f.id);
      const payload = {
        schema_version: SCHEMA_PARTICIPACAO,
        tipo: "contestacao",
        frase_id: f.id,
        conteudo_versao: f.conteudo_versao || "desconhecida",
        aviso_versao: AVISO_VERSAO,
        consentimento: "sim",
        armadilha: "",
      };
      if (leitura && leitura !== "pulou") payload.avaliacao_contestada = leitura;
      if (motivo) payload.motivo = motivo;
      if (texto) payload.frase = texto;
      const resp = await enviar(payload, {
        interacao: guarda.ok(),
        caixaDesafio: desafio,
        onEstado(s) {
          botao.textContent = s === "verificando" ? "Verificando proteção…" : s === "validando" ? "Validando…" : "Enviando…";
        },
      });
      if (resp.descartado) { retorno.append(el("p", { class: "mensagem ok", text: "Obrigado." })); return; }
      estado.enviosDiscordancia += 1;
      guarda.reset();
      campo.value = ""; consentimento.checked = false; aviso.hidden = true;
      radios.forEach((l) => { l.querySelector("input").checked = false; });
      retorno.append(el("p", { class: `mensagem ${resp.confirmado ? "ok" : "aviso"}`, text: resp.confirmado
        ? "Contribuição recebida. Obrigado por ajudar a revisar o projeto."
        : "Enviamos ao serviço, mas ele não permite confirmar o recebimento. Não podemos garantir que chegou." }));
    } catch (e) {
      const motivoErro = e instanceof ErroEnvio ? e.motivo : "rede";
      retorno.append(el("p", { class: "mensagem erro", text: ERROS[motivoErro] || ERROS.rede }));
    } finally {
      botao.disabled = false; botao.textContent = "Enviar para revisão";
    }
  });
  return el("details", { class: "detalhe discordo" }, [el("summary", { text: "Discordo da interpretação" }), form]);
}
