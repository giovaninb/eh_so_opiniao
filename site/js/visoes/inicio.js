import { el, limpar } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { fraseDeAbertura, paresValidos, assuntosVisiveis } from "../nucleo/logica.js";
import { CartaoFrase } from "../componentes/cartaoFrase.js?v=12";
import { EstadoErro, EstadoVazio } from "../componentes/estados.js";
import { ExploradorHome } from "./assuntos.js";

export function mostrarAtalhosComparar() {
  const comparacoes = paresValidos(estado.pares, estado.porId).length > 0;
  for (const id of ["atalho-comparar", "item-comparar-menu", "item-comparar-nav"]) {
    const n = document.getElementById(id);
    if (n) n.hidden = !comparacoes;
  }
}

function mostrarExplorador() {
  mostrarAtalhosComparar();
  const secao = document.getElementById("secao-assuntos");
  const alvo = document.getElementById("explorador-assuntos");
  const tem = assuntosVisiveis(estado.camadaAssuntos).length > 0;
  secao.hidden = !tem;
  if (!tem) { limpar(alvo); return; }
  limpar(alvo, ExploradorHome());
}

export const inicio = {
  titulo: "Início",
  rotaAtiva: "inicio",
  async montar() {
    const alvo = document.getElementById("primeira-interacao");
    if (estado.erro) { limpar(alvo, EstadoErro({ titulo: "Não foi possível carregar as frases", texto: "Abra o site por um servidor HTTP ou tente de novo.", aoTentarDeNovo: () => location.reload() })); alvo.setAttribute("aria-busy", "false"); return; }
    document.getElementById("texto-explorar").textContent = estado.frases.length
      ? `${estado.frases.length} frases com busca, filtros e links diretos.` : "Busque e filtre a biblioteca de frases.";
    mostrarExplorador();
    const f = fraseDeAbertura(estado.frases);
    if (!f) { limpar(alvo, EstadoVazio({ titulo: "Ainda não há frases revisadas", texto: "Nada é publicado antes da revisão por uma pessoa." })); alvo.setAttribute("aria-busy", "false"); return; }
    const cartao = CartaoFrase(f, { rotuloProxima: "Descobrir mais frases", aoProxima: () => { location.hash = "#/descobrir"; } });
    limpar(alvo, cartao.elemento);
    alvo.setAttribute("aria-busy", "false");
    if (estado.meta) {
      const meta = document.getElementById("rodape-meta");
      const iso = estado.meta.gerado_em || "";
      const data = iso ? new Date(iso) : null;
      const quando = data && !Number.isNaN(data.getTime())
        ? new Intl.DateTimeFormat("pt-BR", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(data)
        : iso;
      meta.textContent = `Taxonomia v${estado.meta.taxonomia_versao}. Atualizado em ${quando}.`;
      if (iso) meta.title = iso;
    }
  },
};
