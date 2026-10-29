/* É Só Opinião? — ponto de entrada. Sem IA no navegador, sem rastreamento, sem innerHTML com dados.
   Módulos: nucleo/ (estado, dados, lógica pura, roteador) · componentes/ (peças de interface) · visoes/ (uma por rota). */
import { estado } from "./nucleo/estado.js";
import { carregarBase } from "./nucleo/dados.js";
import { analisarHash, iniciarRoteador } from "./nucleo/roteador.js";
import { iniciarNavegacao, marcarRotaAtiva } from "./componentes/navegacao.js";
import { inicio, mostrarAtalhosComparar } from "./visoes/inicio.js";
import { descobrir } from "./visoes/descobrir.js";
import { explorar } from "./visoes/explorar.js";
import { frase } from "./visoes/frase.js";
import { comparar } from "./visoes/comparar.js?v=6";
import { participar } from "./visoes/participar.js";
import { entender, pesquisa } from "./visoes/saibaMais.js";

const visoes = { inicio, descobrir, explorar, frase, comparar, participar, entender, pesquisa };

function revelar(rotaPedida, fecharMenu) {
  const rota = visoes[rotaPedida] ? rotaPedida : "inicio";
  document.documentElement.classList.toggle("rota-interna", rota !== "inicio");
  document.querySelectorAll("[data-vista]").forEach((s) => { s.hidden = s.dataset.vista !== rota; });
  document.title = `${visoes[rota].titulo} — É Só Opinião?`;
  marcarRotaAtiva(visoes[rota].rotaAtiva || rota, fecharMenu);
}

async function iniciar() {
  const menu = iniciarNavegacao();
  if (estado.rascunho) document.getElementById("faixa-rascunho").hidden = false;
  const casca = () => revelar(analisarHash().rota, menu.fechar);
  casca();
  window.addEventListener("hashchange", casca);
  await carregarBase();
  mostrarAtalhosComparar();
  window.removeEventListener("hashchange", casca);
  await iniciarRoteador(visoes, (rota) => marcarRotaAtiva(rota, menu.fechar));
  document.documentElement.dataset.pronto = "true"; // sinal para os testes automatizados
}

iniciar().catch(() => {
  const aviso = document.createElement("p");
  aviso.className = "pagina";
  aviso.setAttribute("role", "alert");
  aviso.textContent = "Não foi possível carregar esta página. Atualize com Shift+Recarregar.";
  document.getElementById("conteudo").prepend(aviso);
});
