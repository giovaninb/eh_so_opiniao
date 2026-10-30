import { limpar, focar } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { proximaFrase } from "../nucleo/logica.js";
import { CartaoFrase } from "../componentes/cartaoFrase.js?v=12";
import { EstadoErro, EstadoVazio } from "../componentes/estados.js";

export const frase = {
  titulo: "Frase",
  rotaAtiva: "explorar",
  async montar({ param }) {
    const corpo = document.getElementById("frase-corpo");
    corpo.setAttribute("aria-busy", "false");
    if (estado.erro) { limpar(corpo, EstadoErro({ titulo: "Não foi possível carregar as frases", texto: "Tente de novo em instantes.", aoTentarDeNovo: () => location.reload() })); return; }
    const f = estado.porId.get(param);
    if (!f) {
      document.title = "Frase não encontrada — É Só Opinião?";
      limpar(corpo, EstadoVazio({ titulo: "Não encontramos essa frase", texto: "O link pode estar errado, ou a frase ainda não foi aprovada pela revisão.", acao: { rotulo: "Ver a biblioteca", aoClicar: () => { location.hash = "#/explorar"; } } }));
      return;
    }
    document.title = `${f.id} — É Só Opinião?`;
    const ids = estado.ordemBiblioteca.includes(f.id) ? estado.ordemBiblioteca : estado.frases.map((x) => x.id);
    const proxima = proximaFrase(ids, f.id);
    const cartao = CartaoFrase(f, {
      rotuloProxima: "Próxima frase",
      aoProxima: ids.length > 1 ? () => { location.hash = `#/frase/${encodeURIComponent(proxima)}`; } : null,
    });
    limpar(corpo, cartao.elemento);
  },
};
