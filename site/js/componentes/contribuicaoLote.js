/* Oferece envio voluntário de até cinco avaliações da sequência. Sem confirmação, nada sai do aparelho. */
import { el } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { NOME_AVALIACAO, MAX_ENVIOS_POR_VISITA } from "../nucleo/constantes.js";
import { avaliacoesDoLote, marcarLoteEnviado, SCHEMA_PARTICIPACAO, AVISO_VERSAO } from "../nucleo/sessaoContribuicao.js";
import { guardaInteracao } from "../nucleo/protecao.js";
import { enviar, envioAtivo, ErroEnvio, provedorCloudflare } from "./envio.js?v=14";
import { prepararDesafio, rotuloEnvio } from "./desafio.js?v=14";

const ERROS = {
  rede: "Não foi possível falar com o serviço. Nada foi registrado. Você pode tentar de novo enquanto esta página estiver aberta.",
  tempo_esgotado: "O envio demorou demais e foi interrompido. Nada foi registrado. Tente de novo.",
  servico_recusou: "O serviço recusou o envio. Nada foi registrado. Tente mais tarde.",
  cota: "O formulário atingiu o limite mensal de envios. Você pode continuar lendo as frases; as contribuições voltam quando a operadora reabrir.",
  indisponivel: "O serviço está temporariamente indisponível. Nada foi registrado. Você pode tentar de novo enquanto esta página estiver aberta.",
  payload: "Este lote ficou grande demais para enviar. Nada foi registrado.",
  limite_visita: "Você já enviou o máximo nesta visita. O site continua funcionando.",
  turnstile: "Marque “Confirme que é humano” e tente de novo. Nada foi registrado.",
  validacao: "Há um campo que precisa ser ajustado. Nada foi registrado.",
};

export function ContribuicaoLote(ids) {
  const itens = avaliacoesDoLote(ids);
  if (!itens.length || !envioAtivo()) return null;
  if ((estado.enviosLote || 0) >= MAX_ENVIOS_POR_VISITA) {
    return el("p", { class: "suave", text: "Você já enviou o máximo de lotes nesta visita. Obrigado." });
  }

  const retorno = el("div", { role: "status", "aria-live": "polite" });
  const consent = el("input", { type: "checkbox", id: "ok-lote" });
  const erro = el("p", { class: "erro-campo", hidden: "" });
  const botao = el("button", { type: "button", class: "botao botao-claro", text: "Enviar minhas avaliações" });
  const desafio = el("div", { class: "desafio-humano", hidden: "" });
  if (provedorCloudflare() && estado.config.turnstile_sitekey) {
    desafio.hidden = false;
    prepararDesafio(desafio, estado.config.turnstile_sitekey).catch(() => {});
  }
  const armadilha = el("input", { type: "text", tabindex: "-1", autocomplete: "off" });
  const guarda = guardaInteracao(consent);
  const lista = el("ul", { class: "resumo-lote" }, itens.map((a) => el("li", { text: `${a.frase_id}: ${NOME_AVALIACAO[a.avaliacao] || a.avaliacao}` })));

  botao.addEventListener("click", async () => {
    retorno.replaceChildren();
    erro.hidden = true;
    if (armadilha.value) { retorno.append(el("p", { class: "mensagem ok", text: "Obrigado." })); return; }
    if (!consent.checked) { erro.textContent = "Marque que você entendeu o que será enviado."; erro.hidden = false; consent.focus(); return; }
    if (!guarda.ok()) { retorno.append(el("p", { class: "mensagem ok", text: "Obrigado." })); return; }
    botao.disabled = true;
    botao.textContent = "Validando…";
    try {
      const resp = await enviar({
        schema_version: SCHEMA_PARTICIPACAO,
        tipo: "avaliacoes_voluntarias",
        n: String(itens.length),
        avaliacoes: JSON.stringify(itens),
        aviso_versao: AVISO_VERSAO,
        consentimento: "sim",
        armadilha: "",
      }, {
        interacao: guarda.ok(),
        caixaDesafio: desafio,
        onEstado(s) { botao.textContent = rotuloEnvio(s); },
      });
      if (resp.descartado) { retorno.append(el("p", { class: "mensagem ok", text: "Obrigado." })); botao.disabled = false; botao.textContent = "Enviar minhas avaliações"; return; }
      estado.enviosLote = (estado.enviosLote || 0) + 1;
      marcarLoteEnviado(itens.map((a) => a.frase_id));
      caixa.replaceChildren(el("p", { class: `mensagem ${resp.confirmado ? "ok" : "aviso"}`, text: resp.confirmado
        ? "Contribuição recebida. Obrigado por ajudar a revisar o projeto."
        : "Enviamos ao serviço, mas ele não permite confirmar o recebimento. Não podemos garantir que chegou." }));
    } catch (e) {
      const motivo = e instanceof ErroEnvio ? e.motivo : "rede";
      retorno.append(el("p", { class: "mensagem erro", text: ERROS[motivo] || ERROS.rede }));
      botao.disabled = false;
      botao.textContent = "Enviar minhas avaliações";
    }
  });

  const caixa = el("section", { class: "contribuicao-lote", "aria-labelledby": "t-lote" }, [
    el("h3", { id: "t-lote", text: "Contribuir com minhas avaliações" }),
    el("p", { text: "Se quiser, você pode enviar suas respostas para ajudar a revisar a clareza das análises. Não precisamos saber quem você é." }),
    el("p", { class: "pequeno suave", text: "Vai ao formulário privado: identificador e versão de cada frase, o tema, o modo (esta sequência), a leitura que você marcou e se a análise já estava visível. Sem nome, e-mail ou histórico de navegação. O serviço pode registrar dados técnicos, como o endereço de IP." }),
    lista,
    el("label", { class: "escolha" }, [consent, " Entendo o que será enviado e quero contribuir com este lote."]),
    erro,
    el("div", { class: "armadilha", "aria-hidden": "true" }, [el("label", {}, ["Deixe em branco ", armadilha])]),
    desafio,
    el("p", {}, [botao]),
    retorno,
  ]);
  return caixa;
}
