import { estado } from "./estado.js";

async function carregar(caminho) {
  const r = await fetch(caminho, { credentials: "same-origin" });
  if (!r.ok) throw new Error(`${caminho} → HTTP ${r.status}`);
  return r.json();
}

/** Frases, temas, configuração de envio e resultados da enquete. Falha das duas últimas não impede o uso. */
export async function carregarBase() {
  estado.erro = null;
  const arquivo = estado.rascunho ? "data/_rascunho/frases.json" : "data/frases.json";
  try {
    const dados = await carregar(arquivo);
    estado.frases = dados.frases || [];
    estado.temas = dados.temas || [];
    estado.grupos = dados.grupos || [];
    estado.meta = { gerado_em: dados.gerado_em, taxonomia_versao: dados.taxonomia_versao };
    estado.porId = new Map(estado.frases.map((f) => [f.id, f]));
  } catch (e) {
    estado.erro = e;
    return;
  }
  const [config, part, contexto, pares] = await Promise.allSettled([carregar("config_participacao.json"), carregar("data/participacao.json"), carregar("data/contexto.json"), carregar("data/pares.json")]);
  estado.pares = pares.status === "fulfilled" ? pares.value.pares || [] : [];
  estado.contexto = contexto.status === "fulfilled" ? contexto.value.itens || [] : [];
  estado.config = config.status === "fulfilled" ? config.value : null;
  if (part.status === "fulfilled") {
    estado.resultados = part.value.resultados || {};
    estado.minimoVotos = part.value.minimo_para_exibir || 10;
  }
}

let extras = null;
/** Taxonomia, catálogo, achados e referências: só quando o visitante abre "Entender" ou "Pesquisa". */
export function carregarExtras() {
  if (!extras) {
    extras = Promise.all([carregar("data/taxonomia.json"), carregar("data/catalogo.json"), carregar("data/achados.json"), carregar("data/referencias.json")])
      .then(([taxonomia, catalogo, achados, referencias]) => ({ taxonomia, catalogo, achados, referencias }))
      .catch((e) => { extras = null; throw e; });
  }
  return extras;
}
