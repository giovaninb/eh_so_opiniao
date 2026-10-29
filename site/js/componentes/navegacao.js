/* SiteHeader + MobileNavigation: menu em disclosure (não modal), com Esc, clique fora e foco previsível. */

export function iniciarNavegacao() {
  const botao = document.getElementById("botao-menu");
  const painel = document.getElementById("painel-menu");
  const topo = document.getElementById("topo");

  function abrir(aberto, devolverFoco = false) {
    botao.setAttribute("aria-expanded", String(aberto));
    painel.hidden = !aberto;
    if (!aberto && devolverFoco) botao.focus();
  }
  botao.addEventListener("click", () => abrir(painel.hidden));
  painel.addEventListener("click", (e) => { if (e.target.closest("a")) abrir(false); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !painel.hidden) { e.preventDefault(); abrir(false, true); }
  });
  document.addEventListener("click", (e) => { if (!painel.hidden && !topo.contains(e.target)) abrir(false); });
  // Sair do foco do menu com Tab fecha o painel, para ele não ficar aberto atrás do conteúdo.
  painel.addEventListener("focusout", (e) => {
    if (!painel.hidden && e.relatedTarget && !topo.contains(e.relatedTarget)) abrir(false);
  });
  window.matchMedia("(min-width: 960px)").addEventListener("change", (m) => { if (m.matches) abrir(false); });

  document.querySelector("[data-pular]").addEventListener("click", (e) => {
    e.preventDefault();
    const main = document.getElementById("conteudo");
    main.focus();
    main.scrollIntoView();
  });
  return { fechar: () => abrir(false) };
}

export function marcarRotaAtiva(rota, fecharMenu) {
  document.querySelectorAll("[data-rota]").forEach((a) => {
    if (a.dataset.rota === rota) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  fecharMenu();
}
