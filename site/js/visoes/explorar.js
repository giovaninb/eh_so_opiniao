import { el, limpar } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { PAGINA } from "../nucleo/constantes.js";
import { filtrarFrases } from "../nucleo/logica.js";
import { LerControles, EscreverControles, PreencherTemas, ResumoFiltros } from "../componentes/filtros.js";
import { MetaFrase } from "../componentes/cartaoFrase.js";
import { EstadoErro, EstadoVazio } from "../componentes/estados.js";

let ligado = false;
let visiveis = PAGINA;

function filtrosDaUrl(consulta) {
  const tipo = consulta.get("tipo") || "";
  return { q: consulta.get("q") || "", tipo: ["exclusao", "nao_discriminatoria", "ambigua"].includes(tipo) ? tipo : "", tema: consulta.get("tema") || "", ord: consulta.get("ord") || "" };
}

function sincronizarUrl(f) {
  const q = new URLSearchParams(Object.entries(f).filter(([, v]) => v)).toString();
  history.replaceState(null, "", `${location.pathname}${location.search}#/explorar${q ? "?" + q : ""}`);
}

function ItemFrase(f) {
  const id = `item-${f.id}`;
  const respondida = estado.respostas.has(f.id);
  return el("li", { class: "item-frase" }, [
    MetaFrase(f),
    el("p", { class: "frase", id, text: f.texto }),
    respondida ? el("span", { class: "respondida", text: "Você já leu esta" }) : null,
    el("a", { class: "ir", href: `#/frase/${encodeURIComponent(f.id)}`, "aria-describedby": id, text: "Ler e responder →" }),
  ]);
}

function desenhar() {
  const filtros = LerControles();
  const ativos = ResumoFiltros(filtros);
  const resultado = filtrarFrases(estado.frases, filtros);
  estado.ordemBiblioteca = resultado.map((f) => f.id);
  sincronizarUrl(filtros);
  document.getElementById("limpar-filtros").hidden = ativos === 0;
  const lista = document.getElementById("explorar-lista");
  const contagem = document.getElementById("contagem-resultados");
  if (!resultado.length) {
    contagem.textContent = "Nenhuma frase encontrada.";
    limpar(lista, EstadoVazio({ titulo: "Nenhuma frase encontrada", texto: "Tente outro termo ou remova algum filtro.", acao: { rotulo: "Limpar filtros", aoClicar: limparFiltros } }));
    return;
  }
  const mostradas = resultado.slice(0, visiveis);
  contagem.textContent = mostradas.length < resultado.length ? `Mostrando ${mostradas.length} de ${resultado.length} frases` : `${resultado.length} frase${resultado.length > 1 ? "s" : ""}`;
  const ul = el("ul", { class: "lista-frases" }, mostradas.map(ItemFrase));
  const resto = resultado.length - mostradas.length;
  limpar(lista, ul, resto > 0 ? el("div", { class: "mais" }, [el("button", { type: "button", class: "botao botao-claro", text: `Mostrar mais (${resto} restante${resto > 1 ? "s" : ""})`, onclick: () => { visiveis += PAGINA; desenhar(); } })]) : null);
}

function limparFiltros() {
  EscreverControles({});
  visiveis = PAGINA;
  desenhar();
  document.getElementById("campo-busca").focus();
}

function ligarControles() {
  if (ligado) return;
  ligado = true;
  const mudou = () => { visiveis = PAGINA; desenhar(); };
  let tempo;
  document.getElementById("campo-busca").addEventListener("input", () => { clearTimeout(tempo); tempo = setTimeout(mudou, 150); });
  document.getElementById("form-busca").addEventListener("submit", (e) => { e.preventDefault(); mudou(); });
  document.getElementById("filtro-tema").addEventListener("change", mudou);
  document.getElementById("filtro-ordem").addEventListener("change", mudou);
  document.getElementById("segmentos-tipo").addEventListener("click", (e) => {
    const b = e.target.closest(".segmento");
    if (!b) return;
    document.querySelectorAll("#segmentos-tipo .segmento").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    mudou();
  });
  document.getElementById("limpar-filtros").addEventListener("click", limparFiltros);
}

export const explorar = {
  titulo: "Explorar",
  rotaAtiva: "explorar",
  async montar({ consulta }) {
    const lista = document.getElementById("explorar-lista");
    lista.setAttribute("aria-busy", "false");
    if (estado.erro) { limpar(lista, EstadoErro({ titulo: "Não foi possível carregar as frases", texto: "Tente de novo em instantes.", aoTentarDeNovo: () => location.reload() })); return; }
    ligarControles();
    PreencherTemas(estado.temas, estado.frases);
    const f = filtrosDaUrl(consulta);
    EscreverControles(f);
    if (f.tipo || f.tema || f.ord) document.getElementById("filtros").open = true;
    visiveis = PAGINA;
    desenhar();
  },
};
