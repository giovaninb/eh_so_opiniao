/* ParticipationForm: valida no cliente (o servidor valida de novo), mantém o texto em qualquer erro recuperável
   e só diz "recebido" quando o serviço confirma de verdade. */
import { estado } from "../nucleo/estado.js";
import { mascarar } from "../nucleo/mascara.js";
import { LIMITE_MIN, LIMITE_MAX, MAX_ENVIOS_POR_VISITA } from "../nucleo/constantes.js";
import { SCHEMA_PARTICIPACAO, AVISO_VERSAO } from "../nucleo/sessaoContribuicao.js";
import { guardaInteracao } from "../nucleo/protecao.js";
import { envioAtivo, enviar, ErroEnvio, contribuicoesSuspensas, provedorCloudflare } from "./envio.js?v=14";
import { prepararDesafio, rotuloEnvio } from "./desafio.js?v=14";

const MENSAGEM_ERRO = {
  rede: "Não foi possível falar com o serviço de envio. Verifique a conexão e tente de novo. Seu texto continua aqui.",
  tempo_esgotado: "O envio demorou demais e foi interrompido. Tente de novo. Seu texto continua aqui.",
  servico_recusou: "O serviço recusou o envio. Seu texto continua aqui; tente de novo mais tarde.",
  cota: "O formulário atingiu o limite mensal de envios. Você pode continuar lendo as frases; as contribuições voltam quando a operadora reabrir.",
  payload: "O texto ficou grande demais para enviar. Encurte e tente de novo.",
  limite_visita: "Você já enviou o máximo nesta visita. O site continua funcionando; obrigado.",
  indisponivel: "O serviço está temporariamente indisponível. Seu texto continua aqui; você pode tentar de novo.",
  turnstile: "Marque “Confirme que é humano” e envie de novo. Seu texto continua aqui.",
  validacao: "Há um campo que precisa ser ajustado. Seu texto continua aqui.",
};
const NOME_LEITURA = {
  opiniao: "Não vejo problema",
  discriminacao: "Pode ser desrespeitosa ou discriminatória",
  contexto: "Preciso de mais contexto",
};

export function iniciarFormulario() {
  const form = document.getElementById("form-participar");
  const campo = document.getElementById("campo-frase");
  const contexto = document.getElementById("campo-contexto");
  const preview = document.getElementById("previsualizacao-envio");
  const contador = document.getElementById("contador-frase");
  const aviso = document.getElementById("aviso-mascara");
  const botao = document.getElementById("botao-enviar");
  const mensagem = document.getElementById("mensagem-envio");
  const consent = document.getElementById("campo-consentimento");
  const erros = {
    frase: document.getElementById("erro-frase"),
    avaliacao: document.getElementById("erro-avaliacao"),
    consentimento: document.getElementById("erro-consentimento"),
  };

  function mostrarErro(chave, texto, controle) {
    erros[chave].hidden = !texto;
    erros[chave].textContent = texto || "";
    if (controle) controle.setAttribute("aria-invalid", texto ? "true" : "false");
  }
  function atualizarContador() {
    const { texto, tipos } = mascarar(campo.value);
    const n = texto.length;
    contador.textContent = `${n} de ${LIMITE_MAX} caracteres`;
    contador.classList.toggle("perto", n > LIMITE_MAX - 30);
    aviso.hidden = tipos.length === 0;
    aviso.textContent = tipos.length ? `Vamos trocar por marcadores: ${tipos.join(", ")}` : "";
    atualizarPreview();
  }
  function atualizarPreview() {
    if (!preview) return;
    const { texto } = mascarar(campo.value);
    const ctx = mascarar(contexto ? contexto.value : "").texto;
    const av = form.querySelector('input[name="avaliacao"]:checked');
    if (!texto && !ctx && !av) { preview.hidden = true; preview.replaceChildren(); return; }
    preview.hidden = false;
    preview.replaceChildren();
    const h = document.createElement("p");
    h.textContent = "O que será enviado, se você confirmar:";
    const lista = document.createElement("ul");
    const item = (rotulo, valor) => {
      if (!valor) return;
      const li = document.createElement("li");
      li.textContent = `${rotulo}: ${valor}`;
      lista.append(li);
    };
    item("Tipo", "sugestão de frase");
    item("Frase", texto || "(ainda vazia)");
    item("Interpretação", av ? NOME_LEITURA[av.value] : "(não escolhida)");
    item("Contexto", ctx || "(nenhum)");
    item("Consentimento", consent.checked ? "marcado" : "ainda não marcado");
    preview.append(h, lista);
  }
  function validar() {
    const { texto } = mascarar(campo.value);
    const avaliacao = form.querySelector('input[name="avaliacao"]:checked');
    const invalidos = [];
    if (texto.length < LIMITE_MIN) { mostrarErro("frase", `Escreva pelo menos ${LIMITE_MIN} caracteres (você tem ${texto.length}).`, campo); invalidos.push(campo); }
    else if (texto.length > LIMITE_MAX) { mostrarErro("frase", `A frase tem ${texto.length - LIMITE_MAX} caracteres a mais que o limite de ${LIMITE_MAX}. Encurte e envie de novo.`, campo); invalidos.push(campo); }
    else mostrarErro("frase", "", campo);
    if (!avaliacao) { mostrarErro("avaliacao", "Escolha como você lê essa frase."); invalidos.push(form.querySelector('input[name="avaliacao"]')); }
    else mostrarErro("avaliacao", "");
    if (!consent.checked) { mostrarErro("consentimento", "Marque que você entendeu como a frase será tratada.", consent); invalidos.push(consent); }
    else mostrarErro("consentimento", "", consent);
    return { invalidos, texto, avaliacao: avaliacao && avaliacao.value, contexto: mascarar(contexto ? contexto.value : "").texto };
  }
  function nota(tipo, texto) {
    mensagem.replaceChildren();
    if (!texto) return;
    const p = document.createElement("p");
    p.className = `mensagem ${tipo}`;
    p.textContent = texto;
    mensagem.append(p);
  }

  const guarda = guardaInteracao(campo, contexto);
  campo.addEventListener("input", atualizarContador);
  campo.addEventListener("focus", () => setTimeout(() => campo.scrollIntoView({ block: "center", behavior: "auto" }), 250));
  if (contexto) contexto.addEventListener("input", atualizarPreview);
  form.addEventListener("change", atualizarPreview);
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (botao.disabled) return;
    if (!envioAtivo()) return;
    nota("", "");
    if (document.getElementById("campo-armadilha").value) { nota("ok", "Obrigado."); return; }
    const { invalidos, texto, avaliacao, contexto: ctx } = validar();
    if (invalidos.length) { invalidos[0].focus(); return; }
    if (estado.enviosFrases >= MAX_ENVIOS_POR_VISITA) { nota("aviso", "Você já enviou o máximo de frases nesta visita. Obrigado!"); return; }
    if (!guarda.ok()) { nota("ok", "Obrigado."); return; }
    botao.disabled = true;
    botao.textContent = "Validando…";
    try {
      const payload = {
        schema_version: SCHEMA_PARTICIPACAO,
        tipo: "sugestao_frase",
        frase: texto,
        avaliacao,
        aviso_versao: AVISO_VERSAO,
        consentimento: "sim",
        armadilha: "",
      };
      if (ctx) payload.contexto = ctx.slice(0, LIMITE_MAX);
      const resp = await enviar(payload, {
        interacao: guarda.ok(),
        onEstado(s) { botao.textContent = rotuloEnvio(s); },
      });
      if (resp.descartado) { nota("ok", "Obrigado."); return; }
      estado.enviosFrases += 1;
      guarda.reset();
      form.reset();
      atualizarContador();
      nota(resp.confirmado ? "ok" : "aviso",
        resp.confirmado ? "Recebido. Uma pessoa vai ler antes de qualquer publicação, e só mostramos o que estiver anonimizado e aprovado."
          : "Enviamos ao serviço, mas ele não permite confirmar o recebimento. Não podemos garantir que chegou.");
    } catch (e) {
      const motivo = e instanceof ErroEnvio ? e.motivo : "rede";
      nota("erro", MENSAGEM_ERRO[motivo] || MENSAGEM_ERRO.rede);
    } finally {
      botao.disabled = false;
      botao.textContent = "Enviar frase";
    }
  });
  atualizarContador();

  return {
    atualizarDisponibilidade() {
      const ativo = envioAtivo();
      const suspenso = contribuicoesSuspensas();
      const avisoInd = document.getElementById("aviso-indisponivel");
      avisoInd.hidden = ativo;
      const titulo = avisoInd.querySelector("strong");
      const corpo = avisoInd.querySelector("[data-aviso-corpo]");
      if (suspenso) {
        if (titulo) titulo.textContent = "As contribuições estão temporariamente suspensas.";
        if (corpo) corpo.textContent = "O limite mensal do formulário gratuito foi atingido. Você pode continuar lendo as frases; nada é enviado até a operadora reabrir as contribuições.";
      } else {
        if (titulo) titulo.textContent = "O envio ainda não está disponível.";
        if (corpo) corpo.textContent = "Este site ainda não tem um serviço de recebimento configurado, então nada é enviado nem guardado. Você pode ler como o tratamento funcionará abaixo e voltar mais tarde.";
      }
      form.querySelectorAll("textarea, input:not(#campo-armadilha), button[type=submit]").forEach((c) => { c.disabled = !ativo; });
      const campoDesafio = document.getElementById("campo-desafio");
      const desafio = document.getElementById("desafio-envio");
      if (campoDesafio) campoDesafio.hidden = !(ativo && provedorCloudflare());
      if (desafio && ativo && provedorCloudflare() && estado.config.turnstile_sitekey) {
        prepararDesafio(desafio, estado.config.turnstile_sitekey).catch(() => {});
      }
    },
  };
}
