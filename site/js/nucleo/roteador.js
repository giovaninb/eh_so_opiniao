/* Roteador por hash: #/ · #/descobrir · #/explorar?tema=... · #/frase/ID · #/participar · #/entender · #/pesquisa
   Hash funciona no GitHub Pages sem configuração e deixa cada frase com link compartilhável. */

export function analisarHash(hash = location.hash) {
  const bruto = hash.replace(/^#\/?/, "");
  const [caminho, consulta = ""] = bruto.split("?");
  const partes = caminho.split("/").filter(Boolean);
  let param = null;
  try { param = partes[1] ? decodeURIComponent(partes[1]) : null; } catch { param = null; }
  return { rota: partes[0] || "inicio", param, consulta: new URLSearchParams(consulta) };
}

export function montarHash(rota, params = {}) {
  const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
  return `#/${rota === "inicio" ? "" : rota}${q ? "?" + q : ""}`;
}

export function iniciarRoteador(visoes, aoMudar) {
  let primeira = true;
  async function ir() {
    const alvo = analisarHash();
    const visao = visoes[alvo.rota] || visoes.inicio;
    const rota = visoes[alvo.rota] ? alvo.rota : "inicio";
    document.documentElement.classList.toggle("rota-interna", rota !== "inicio"); // a classe só existe para o 1º paint; sem isto, voltar à Início deixava a home em branco
    document.querySelectorAll("[data-vista]").forEach((s) => { s.hidden = s.dataset.vista !== rota; });
    document.title = `${visao.titulo} — É Só Opinião?`;
    aoMudar(visao.rotaAtiva || rota);
    if (!primeira) window.scrollTo(0, 0);
    await visao.montar({ ...alvo, primeira });
    primeira = false;
  }
  window.addEventListener("hashchange", ir);
  return ir();
}
