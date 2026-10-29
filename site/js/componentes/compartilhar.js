/* ShareBar: convite para compartilhar uma frase. Nada é enviado até a pessoa tocar num botão, não há rastreador
   e a mensagem é uma pergunta ("onde você coloca a linha?"), nunca um rótulo sobre alguém. */
import { el } from "../nucleo/dom.js";
import { mensagemCompartilhar, linkWhatsApp } from "../nucleo/logica.js";

export function urlDaFrase(id) {
  return `${location.origin}${location.pathname}#/frase/${encodeURIComponent(id)}`;
}

export function Compartilhar(f) {
  if (f.revisao && !f.revisao.por_humano) return null; // rascunho local nunca é compartilhável
  const url = urlDaFrase(f.id);
  const mensagem = mensagemCompartilhar(f, url);
  const retorno = el("p", { class: "pequeno suave retorno-compartilhar", role: "status" });
  const botoes = [];

  if (typeof navigator.share === "function") {
    botoes.push(el("button", {
      type: "button", class: "botao botao-claro", text: "Compartilhar",
      onclick: async () => {
        try { await navigator.share({ title: "É Só Opinião?", text: mensagem }); }
        catch (e) { if (!e || e.name !== "AbortError") retorno.textContent = "Não foi possível abrir o compartilhamento. Use “Copiar mensagem”."; }
      },
    }));
  }
  botoes.push(el("a", {
    class: "botao botao-claro", href: linkWhatsApp(mensagem), target: "_blank", rel: "noopener noreferrer",
    "aria-label": "Enviar no WhatsApp (abre em outra aba)", text: "WhatsApp",
  }));
  botoes.push(el("button", {
    type: "button", class: "botao botao-claro", text: "Copiar mensagem",
    onclick: async () => {
      try { await navigator.clipboard.writeText(mensagem); retorno.textContent = "Mensagem copiada. Cole onde quiser."; }
      catch { retorno.textContent = `Copie o link: ${url}`; }
    },
  }));

  return el("section", { class: "compartilhar", "aria-label": "Compartilhar esta frase" }, [
    el("p", { class: "compartilhar-titulo", text: "Quer ouvir outra pessoa sobre esta frase?" }),
    el("div", { class: "compartilhar-botoes" }, botoes),
    retorno,
  ]);
}
