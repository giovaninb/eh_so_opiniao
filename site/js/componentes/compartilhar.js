/* ShareBar: convite para compartilhar um caso ou uma comparação. Nada é enviado até a pessoa tocar num botão, não há
   rastreador, e a mensagem é uma pergunta ("onde você coloca a linha?"), nunca um rótulo sobre alguém.
   O link aponta para a página estática do caso (casos/<id>/), que tem prévia própria em redes sociais e leva à experiência interativa. */
import { el } from "../nucleo/dom.js";
import { mensagemCompartilhar, mensagemComparacao, linkWhatsApp, nomeArquivoImagem } from "../nucleo/logica.js";
import { FORMATOS, gerarImagem, textoAlternativo, textoAlternativoPar } from "../nucleo/cartaoCanvas.js?v=8";

/** Raiz do site (onde está o index.html), a partir deste módulo: funciona em qualquer subcaminho, inclusive no GitHub Pages. */
export function raizDoSite() {
  return new URL("../../", import.meta.url).href;
}
export function urlDaFrase(id) {
  return `${raizDoSite()}casos/${encodeURIComponent(String(id).toLowerCase())}/`;
}
export function urlDaComparacao(slug) {
  return `${raizDoSite()}comparar/${encodeURIComponent(slug)}/`;
}

function BotoesDeLink({ url, mensagem, retorno, titulo }) {
  const botoes = [];
  if (typeof navigator.share === "function") {
    botoes.push(el("button", {
      type: "button", class: "botao botao-claro", text: "Compartilhar",
      onclick: async () => {
        try { await navigator.share({ title: "É Só Opinião?", text: mensagem }); }
        catch (e) { if (!e || e.name !== "AbortError") retorno.textContent = "Não foi possível abrir o compartilhamento. Use “Copiar link”."; }
      },
    }));
  }
  botoes.push(el("a", {
    class: "botao botao-claro", href: linkWhatsApp(mensagem), target: "_blank", rel: "noopener noreferrer",
    "aria-label": `Enviar no WhatsApp (abre em outra aba)${titulo ? ": " + titulo : ""}`, text: "WhatsApp",
  }));
  const copiar = (texto, ok) => async () => {
    try { await navigator.clipboard.writeText(texto); retorno.textContent = ok; }
    catch { retorno.textContent = `Copie o link: ${url}`; }
  };
  botoes.push(el("button", { type: "button", class: "botao botao-claro", text: "Copiar link", onclick: copiar(url, "Link copiado.") }));
  botoes.push(el("button", { type: "button", class: "botao botao-claro", text: "Copiar mensagem", onclick: copiar(mensagem, "Mensagem copiada. Cole onde quiser.") }));
  return botoes;
}

/** Imagem para Status e Stories (9:16) e prévia 1200×630, gerada no navegador quando a pessoa pede. */
function ImagemDoCartao({ id, url, retorno, pedido, alt }) {
  const area = el("div", { class: "imagem-resultado", "aria-live": "polite" });
  let urls = [];
  function soltar() { urls.forEach((u) => URL.revokeObjectURL(u)); urls = []; }
  async function copiarPng(blob) {
    if (!navigator.clipboard || typeof ClipboardItem !== "function") throw new Error("clipboard");
    await navigator.clipboard.write([new ClipboardItem({ "image/png": Promise.resolve(blob) })]);
  }
  async function gerar(formato) {
    retorno.textContent = "Gerando a imagem…";
    try {
      const gerada = await gerarImagem({ formato, url, ...pedido });
      soltar();
      const hrefArquivo = URL.createObjectURL(gerada.arquivo);
      const hrefPrevia = URL.createObjectURL(gerada.previa);
      urls = [hrefArquivo, hrefPrevia];
      const nome = nomeArquivoImagem(id, formato.sufixo);
      const arquivo = typeof File === "function" ? new File([gerada.arquivo], nome, { type: "image/png" }) : null;
      const acoes = [
        el("a", { class: "botao", href: hrefArquivo, download: nome, text: "Salvar imagem" }),
        el("button", {
          type: "button", class: "botao botao-claro", text: "Copiar imagem",
          onclick: async () => {
            try { await copiarPng(gerada.arquivo); retorno.textContent = "Imagem copiada. Cole no Status ou no Stories."; }
            catch { retorno.textContent = "Neste aparelho a cópia manda duas imagens. Use “Salvar imagem” e anexe o arquivo."; }
          },
        }),
      ];
      if (arquivo && navigator.canShare && navigator.canShare({ files: [arquivo] })) {
        acoes.push(el("button", {
          type: "button", class: "botao botao-claro", text: "Compartilhar imagem",
          onclick: async () => {
            try { await navigator.share({ files: [arquivo] }); } // só o arquivo: título/texto fariam o WhatsApp anexar também a prévia do link
            catch (e) { if (!e || e.name !== "AbortError") retorno.textContent = "Não foi possível compartilhar a imagem. Use “Salvar imagem”."; }
          },
        }));
      }
      area.replaceChildren(
        el("img", {
          class: `previa-cartao previa-${formato.id}`, src: hrefPrevia, alt: alt(formato),
          draggable: "false",
        }),
        el("div", { class: "compartilhar-botoes" }, acoes),
      );
      retorno.textContent = `Imagem ${gerada.largura}×${gerada.altura} pronta. A miniatura é só para conferir.`;
    } catch {
      retorno.textContent = "Não foi possível gerar a imagem neste navegador. Use “Copiar link”.";
    }
  }
  return el("details", { class: "detalhe imagem-cartao" }, [
    el("summary", { text: "Imagem para Status ou Stories" }),
    el("p", { class: "pequeno suave", text: "A imagem é criada no seu aparelho. Frases com aviso de conteúdo não aparecem nela. Para Status ou Stories, use Salvar, Copiar imagem ou Compartilhar imagem — copiar a miniatura da página manda duas imagens." }),
    el("div", { class: "compartilhar-botoes" }, Object.values(FORMATOS).map((fm) => el("button", { type: "button", class: "botao botao-claro", "data-formato": fm.id, text: fm.rotulo, onclick: () => gerar(fm) }))),
    area,
  ]);
}

export function Compartilhar(f) {
  if (f.revisao && !f.revisao.por_humano) return null; // rascunho local nunca é compartilhável
  const url = urlDaFrase(f.id);
  const mensagem = mensagemCompartilhar(f, url);
  const retorno = el("p", { class: "pequeno suave retorno-compartilhar", role: "status" });
  return el("section", { class: "compartilhar", "aria-label": "Compartilhar esta frase" }, [
    el("p", { class: "compartilhar-titulo", text: "Quer ouvir outra pessoa sobre esta frase?" }),
    el("div", { class: "compartilhar-botoes" }, BotoesDeLink({ url, mensagem, retorno, titulo: f.id })),
    ImagemDoCartao({ id: f.id, url, retorno, pedido: { frase: f }, alt: (fm) => textoAlternativo(f, fm) }),
    retorno,
  ]);
}

export function CompartilharComparacao(par, a, b) {
  const url = urlDaComparacao(par.slug);
  const mensagem = mensagemComparacao(url);
  const retorno = el("p", { class: "pequeno suave retorno-compartilhar", role: "status" });
  return el("section", { class: "compartilhar", "aria-label": "Compartilhar esta comparação" }, [
    el("p", { class: "compartilhar-titulo", text: "Quer comparar com outra pessoa?" }),
    el("div", { class: "compartilhar-botoes" }, BotoesDeLink({ url, mensagem, retorno, titulo: par.titulo })),
    ImagemDoCartao({
      id: par.slug, url, retorno, pedido: { par, a, b },
      alt: (fm) => textoAlternativoPar(par, a, b, fm),
    }),
    retorno,
  ]);
}
