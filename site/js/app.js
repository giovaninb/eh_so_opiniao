/* É Só Opinião? — site estático. Sem IA no navegador, sem rastreamento, sem innerHTML com dados. */
(function () {
  "use strict";

  const params = new URLSearchParams(location.search);
  const rascunho = params.get("rascunho") === "1";
  const ROTULO_TIPO = { supervisionado: "supervisionada", exploratorio: "exploratória", salvaguarda: "salvaguarda" };
  const CLASSE_TIPO = { supervisionado: "sup", exploratorio: "exp", salvaguarda: "salv" };
  const NOME_TIPO_FRASE = { exclusao: "Exclusão", nao_discriminatoria: "Não discriminatória", ambigua: "Ambígua" };

  function el(tag, opts, filhos) {
    const e = document.createElement(tag);
    if (opts) {
      for (const k of Object.keys(opts)) {
        if (k === "text") e.textContent = opts[k];
        else if (k === "class") e.className = opts[k];
        else e.setAttribute(k, opts[k]);
      }
    }
    (filhos || []).forEach((f) => e.append(f));
    return e;
  }

  async function carregar(caminho) {
    const r = await fetch(caminho, { cache: "no-cache" });
    if (!r.ok) throw new Error(caminho + " → HTTP " + r.status);
    return r.json();
  }

  function etiquetas(lista) {
    const caixa = el("span");
    if (!lista || lista.length === 0) {
      caixa.append(el("span", { class: "etiqueta", text: "nenhuma categoria" }));
      return caixa;
    }
    lista.forEach((r) => caixa.append(el("span", { class: "etiqueta " + (CLASSE_TIPO[r.tipo] || ""), text: r.nome })));
    return caixa;
  }

  function cartaoFrase(f) {
    const revelacao = el("div", { class: "revelacao", hidden: "" });
    revelacao.append(
      el("p", {}, [el("strong", { text: "Leitura da revisão: " }), etiquetas(f.rotulos)]),
      el("p", { text: f.mecanismo || "" }),
      el("p", {}, [el("strong", { text: "A IA sugeriu: " }), etiquetas(f.ia.sinalizou)]),
      el("p", { class: "pequeno", text: f.ia.concorda_com_revisao
        ? "A sugestão da IA coincidiu com a revisão humana neste caso."
        : "A sugestão da IA foi diferente da revisão humana neste caso. Por isso toda classificação passa por revisão." }),
      el("p", { class: "pequeno", text: "Método: " + (f.ia.metodo || "—") + ". Pontuação de modelo não é prova nem conclui crime." })
    );
    const botoes = el("div", { class: "escolhas", role: "group", "aria-label": "Qual é a sua leitura?" });
    ["É só opinião", "É discriminação", "Depende do contexto"].forEach((rotulo) => {
      const b = el("button", { type: "button", text: rotulo });
      b.addEventListener("click", () => {
        revelacao.hidden = false;
        botoes.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        revelacao.scrollIntoView({ block: "nearest" });
      });
      botoes.append(b);
    });
    const topo = el("p", { class: "pequeno" }, [el("span", { class: "etiqueta", text: NOME_TIPO_FRASE[f.tipo] || f.tipo })]);
    if (f.par_espelho) topo.append(el("span", { class: "etiqueta espelho", text: "espelho de " + f.par_espelho }));
    if (f.revisao && !f.revisao.por_humano) topo.append(el("span", { class: "etiqueta exp", text: "RASCUNHO" }));
    return el("article", { class: "item", "data-tipo": f.tipo }, [topo, el("p", { class: "frase", text: f.texto }), botoes, revelacao]);
  }

  function mostrarFrases(dados) {
    const lista = document.getElementById("lista-frases");
    const status = document.getElementById("status-frases");
    const frases = dados.frases || [];
    const cartoes = frases.map(cartaoFrase);
    lista.replaceChildren(...cartoes);
    if (frases.length === 0) {
      lista.append(el("p", { class: "vazio", text: "Ainda não há frases aprovadas por revisão humana para exibir. Nada é publicado sem essa etapa." }));
    }
    status.textContent = frases.length + " frase(s) exibida(s).";
    document.querySelectorAll(".filtro").forEach((b) => {
      b.addEventListener("click", () => {
        const f = b.dataset.filtro;
        document.querySelectorAll(".filtro").forEach((x) => {
          x.classList.toggle("ativo", x === b);
          x.setAttribute("aria-pressed", String(x === b));
        });
        let n = 0;
        cartoes.forEach((c) => {
          const visivel = f === "todas" || c.dataset.tipo === f;
          c.hidden = !visivel;
          n += visivel ? 1 : 0;
        });
        status.textContent = n + " frase(s) exibida(s).";
      });
    });
  }

  function mostrarTaxonomia(t) {
    const lista = document.getElementById("lista-taxonomia");
    lista.replaceChildren(...t.rotulos.map((r) => el("article", { class: "cartao" }, [
      el("h3", { text: r.nome }),
      el("span", { class: "etiqueta " + CLASSE_TIPO[r.tipo], text: ROTULO_TIPO[r.tipo] }),
      el("p", { text: r.definicao }),
      r.nao_e ? el("p", { class: "pequeno", text: "Não é: " + r.nao_e }) : el("span"),
    ])));
  }

  function mostrarCatalogo(c) {
    const lista = document.getElementById("lista-catalogo");
    lista.replaceChildren(...c.map((d) => el("article", { class: "cartao" }, [
      el("h3", { text: d.nome }),
      el("p", { class: "pequeno", text: "Licença: " + d.licenca + " · " + d.plataforma }),
      el("span", { class: "etiqueta " + (d.status === "acessado" ? "sup" : "exp"), text: d.status === "acessado" ? "usada" : "pendente (" + d.status.replace(/_/g, " ") + ")" }),
    ])));
    const refs = document.getElementById("lista-referencias");
    refs.replaceChildren(...c.map((d) => el("li", {}, [
      document.createTextNode(d.referencia + " "),
      el("a", { href: d.url, rel: "noopener", text: "Fonte" }),
    ])));
  }

  function mostrarAchados(a) {
    const lista = document.getElementById("lista-achados");
    const itens = a.gerado_dos_relatorios || [];
    if (itens.length === 0) {
      lista.replaceChildren(el("p", { class: "vazio", text: "Os experimentos ainda não foram executados neste ambiente." }));
      return;
    }
    lista.replaceChildren(...itens.map((i) => el("article", { class: "cartao" }, [
      el("h3", { text: i.titulo }),
      el("p", { text: i.texto }),
      el("p", { class: "pequeno", text: "Experimento " + i.experimento }),
    ])));
  }

  async function iniciar() {
    if (rascunho) document.getElementById("faixa-rascunho").hidden = false;
    const falhas = [];
    const tentar = async (nome, fn) => { try { await fn(); } catch (e) { falhas.push(nome + ": " + e.message); } };
    let frases = null;
    await tentar("frases", async () => {
      frases = await carregar(rascunho ? "data/_rascunho/frases.json" : "data/frases.json");
      mostrarFrases(frases);
    });
    await tentar("taxonomia", async () => mostrarTaxonomia(await carregar("data/taxonomia.json")));
    await tentar("catálogo", async () => mostrarCatalogo(await carregar("data/catalogo.json")));
    await tentar("achados", async () => mostrarAchados(await carregar("data/achados.json")));
    const meta = document.getElementById("rodape-meta");
    if (frases) meta.textContent = "Taxonomia v" + frases.taxonomia_versao + " · dados gerados em " + frases.gerado_em;
    if (falhas.length) {
      const status = document.getElementById("status-frases");
      status.textContent = "Não foi possível carregar alguns dados (" + falhas.join("; ") + "). Abra o site por um servidor HTTP, não por arquivo local.";
    }
  }

  iniciar();
})();
