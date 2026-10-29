/* CategoryFilter: liga os controles estáticos do HTML (busca, tipo, tema, ordem) ao estado da biblioteca. */
export function LerControles() {
  return {
    q: document.getElementById("campo-busca").value.trim(),
    tipo: document.querySelector("#segmentos-tipo [aria-pressed='true']")?.dataset.tipo || "",
    tema: document.getElementById("filtro-tema").value,
    ord: document.getElementById("filtro-ordem").value,
  };
}

export function EscreverControles({ q = "", tipo = "", tema = "", ord = "" }) {
  document.getElementById("campo-busca").value = q;
  document.querySelectorAll("#segmentos-tipo .segmento").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tipo === tipo)));
  document.getElementById("filtro-tema").value = tema;
  document.getElementById("filtro-ordem").value = ord;
}

export function PreencherTemas(temas, frases) {
  const select = document.getElementById("filtro-tema");
  const atual = select.value;
  const contagem = {};
  frases.forEach((f) => { contagem[f.tema] = (contagem[f.tema] || 0) + 1; });
  select.replaceChildren(new Option("Todos os temas", ""), ...temas.map((t) => new Option(`${t.nome} (${contagem[t.id] || 0})`, t.id)));
  select.value = atual;
}

export function ResumoFiltros(filtros) {
  const n = ["tipo", "tema", "ord"].filter((k) => filtros[k]).length;
  document.getElementById("resumo-filtros").textContent = n ? `Filtros (${n} ativo${n > 1 ? "s" : ""})` : "Filtros";
  return n + (filtros.q ? 1 : 0);
}
