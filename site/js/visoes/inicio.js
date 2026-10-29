import { el, limpar } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { fraseDeAbertura, paresValidos } from "../nucleo/logica.js";
import { CartaoFrase } from "../componentes/cartaoFrase.js";
import { EstadoErro, EstadoVazio } from "../componentes/estados.js";

function mostrarAtalhos() {
  const comparacoes = paresValidos(estado.pares, estado.porId).length > 0;
  document.getElementById("atalho-comparar").hidden = !comparacoes;
  document.getElementById("item-comparar-menu").hidden = !comparacoes;
  const contagem = {};
  estado.frases.forEach((f) => { if (f.grupo) contagem[f.grupo] = (contagem[f.grupo] || 0) + 1; });
  const grupos = estado.grupos.filter((g) => contagem[g.id]);
  document.getElementById("secao-assuntos").hidden = !grupos.length;
  limpar(document.getElementById("chips-assuntos"), grupos.map((g) => el("a", { class: "chip", href: `#/descobrir?tema=${encodeURIComponent(g.id)}`, text: g.nome })));
}

export const inicio = {
  titulo: "Início",
  rotaAtiva: "inicio",
  async montar() {
    const alvo = document.getElementById("primeira-interacao");
    if (estado.erro) { limpar(alvo, EstadoErro({ titulo: "Não foi possível carregar as frases", texto: "Abra o site por um servidor HTTP ou tente de novo.", aoTentarDeNovo: () => location.reload() })); alvo.setAttribute("aria-busy", "false"); return; }
    document.getElementById("texto-explorar").textContent = estado.frases.length
      ? `${estado.frases.length} frases com busca, filtros e links diretos.` : "Busque e filtre a biblioteca de frases.";
    mostrarAtalhos();
    const f = fraseDeAbertura(estado.frases);
    if (!f) { limpar(alvo, EstadoVazio({ titulo: "Ainda não há frases revisadas", texto: "Nada é publicado antes da revisão por uma pessoa." })); alvo.setAttribute("aria-busy", "false"); return; }
    const cartao = CartaoFrase(f, { rotuloProxima: "Descobrir mais frases", aoProxima: () => { location.hash = "#/descobrir"; } });
    limpar(alvo, cartao.elemento);
    alvo.setAttribute("aria-busy", "false");
    if (estado.meta) document.getElementById("rodape-meta").textContent = `Taxonomia v${estado.meta.taxonomia_versao} · dados gerados em ${estado.meta.gerado_em}`;
  },
};
