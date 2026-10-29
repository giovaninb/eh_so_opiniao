/* ParticipationForm: valida no cliente (o servidor valida de novo), mantém o texto em qualquer erro recuperável
   e só diz "recebido" quando o serviço confirma de verdade. */
import { estado } from "../nucleo/estado.js";
import { mascarar } from "../nucleo/mascara.js";
import { LIMITE_MIN, LIMITE_MAX, MAX_ENVIOS_POR_VISITA } from "../nucleo/constantes.js";
import { envioAtivo, enviar, ErroEnvio } from "./envio.js";

const MENSAGEM_ERRO = {
  rede: "Não foi possível falar com o serviço de envio. Verifique a conexão e tente de novo. Seu texto continua aqui.",
  tempo_esgotado: "O envio demorou demais e foi interrompido. Tente de novo. Seu texto continua aqui.",
  servico_recusou: "O serviço recusou o envio. Seu texto continua aqui; tente de novo mais tarde.",
  indisponivel: "O envio não está disponível agora.",
};

export function iniciarFormulario() {
  const form = document.getElementById("form-participar");
  const campo = document.getElementById("campo-frase");
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
    return { invalidos, texto, avaliacao: avaliacao && avaliacao.value };
  }
  function nota(tipo, texto) {
    mensagem.replaceChildren();
    if (!texto) return;
    const p = document.createElement("p");
    p.className = `mensagem ${tipo}`;
    p.textContent = texto;
    mensagem.append(p);
  }

  campo.addEventListener("input", atualizarContador);
  campo.addEventListener("focus", () => setTimeout(() => campo.scrollIntoView({ block: "center", behavior: "auto" }), 250)); // teclado virtual
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (!envioAtivo()) return;
    nota("", "");
    if (document.getElementById("campo-armadilha").value) { nota("ok", "Obrigado."); return; }
    const { invalidos, texto, avaliacao } = validar();
    if (invalidos.length) { invalidos[0].focus(); return; }
    if (estado.enviosFrases >= MAX_ENVIOS_POR_VISITA) { nota("aviso", "Você já enviou o máximo de frases nesta visita. Obrigado!"); return; }
    botao.disabled = true;
    botao.textContent = "Enviando…";
    try {
      const resp = await enviar({ tipo: "frase", frase: texto, avaliacao, consentimento: "sim", armadilha: "" });
      estado.enviosFrases += 1;
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
      document.getElementById("aviso-indisponivel").hidden = ativo;
      form.querySelectorAll("textarea, input:not(#campo-armadilha), button[type=submit]").forEach((c) => { c.disabled = !ativo; });
    },
  };
}
