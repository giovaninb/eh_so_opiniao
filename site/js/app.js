/* É Só Opinião? — ponto de entrada. Sem IA no navegador, sem rastreamento, sem innerHTML com dados.
   Módulos: nucleo/ (estado, dados, lógica pura, roteador) · componentes/ (peças de interface) · visoes/ (uma por rota). */
import { estado } from "./nucleo/estado.js";
import { carregarBase } from "./nucleo/dados.js";
import { iniciarRoteador } from "./nucleo/roteador.js";
import { iniciarNavegacao, marcarRotaAtiva } from "./componentes/navegacao.js";
import { inicio } from "./visoes/inicio.js";
import { descobrir } from "./visoes/descobrir.js";
import { explorar } from "./visoes/explorar.js";
import { frase } from "./visoes/frase.js";
import { comparar } from "./visoes/comparar.js";
import { participar } from "./visoes/participar.js";
import { entender, pesquisa } from "./visoes/saibaMais.js";

const visoes = { inicio, descobrir, explorar, frase, comparar, participar, entender, pesquisa };

async function iniciar() {
  const menu = iniciarNavegacao();
  if (estado.rascunho) document.getElementById("faixa-rascunho").hidden = false;
  await carregarBase();
  await iniciarRoteador(visoes, (rota) => marcarRotaAtiva(rota, menu.fechar));
  document.documentElement.dataset.pronto = "true"; // sinal para os testes automatizados
}

iniciar();
