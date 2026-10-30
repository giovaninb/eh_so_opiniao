import { el, limpar, focar } from "../nucleo/dom.js";
import { estado } from "../nucleo/estado.js";
import { assuntoPorId, assuntosVisiveis, buscarAssuntos, frasesDoAssunto, paresValidos, linkWhatsApp } from "../nucleo/logica.js";
import { EstadoErro, EstadoVazio } from "../componentes/estados.js";

function catalogo() {
  return estado.camadaAssuntos || { grupos: [], assuntos: [], situacoes: [] };
}

function urlEstatica(id) {
  const base = `${location.origin}${location.pathname.replace(/index\.html$/, "")}`;
  return `${base}assuntos/${id}/`;
}

function ItemAssunto(a) {
  return el("a", { class: "item-assunto", href: a.url }, [
    el("strong", { text: a.nome }),
    el("span", { class: "contagem", text: `${a.n} exemplo${a.n === 1 ? "" : "s"}` }),
    el("span", { class: "suave pequeno", text: a.descricao }),
  ]);
}

function Grupos({ grupoAberto } = {}) {
  const visiveis = (catalogo().grupos || []).filter((g) => g.visivel);
  return visiveis.map((g) => {
    const itens = (catalogo().assuntos || []).filter((a) => g.assuntos.includes(a.id));
    return el("details", { class: "grupo-tematico", open: grupoAberto === g.id ? "" : null }, [
      el("summary", {}, [
        el("span", { class: "grupo-resumo" }, [
          el("strong", { text: g.nome }),
          el("span", { class: "suave pequeno", text: `${g.n_assuntos} assunto${g.n_assuntos === 1 ? "" : "s"}` }),
          g.descricao ? el("span", { class: "grupo-desc pequeno suave", text: g.descricao }) : null,
        ]),
      ]),
      el("div", { class: "lista-assuntos" }, itens.map(ItemAssunto)),
    ]);
  });
}

function Situacoes() {
  const lista = catalogo().situacoes || [];
  if (!lista.length) return null;
  return el("section", { class: "subbloco", "aria-labelledby": "t-situacoes" }, [
    el("h2", { id: "t-situacoes", class: "subsecao", text: "Situações do cotidiano" }),
    el("p", { class: "suave", text: "Outro jeito de chegar aos assuntos, sem precisar do nome técnico." }),
    el("div", { class: "chips" }, lista.map((s) => el("a", { class: "chip", href: s.url, text: s.nome }))),
  ]);
}

function Formatos() {
  return el("section", { class: "subbloco", "aria-labelledby": "t-formatos" }, [
    el("h2", { id: "t-formatos", class: "subsecao", text: "Formatos de exploração" }),
    el("div", { class: "chips" }, [
      el("a", { class: "chip", href: "#/descobrir", text: "Descobrir cinco frases" }),
      el("a", { class: "chip", href: "#/comparar", text: "Comparar duas frases" }),
      el("a", { class: "chip", href: "#/explorar", text: "Explorar a biblioteca" }),
      el("a", { class: "chip", href: "#/entender", text: "Entender uma expressão" }),
      el("a", { class: "chip", href: "#/assuntos/depende_contexto", text: "Conhecer casos ambíguos" }),
    ]),
  ]);
}

function lista() {
  const corpo = document.getElementById("assuntos-corpo");
  const titulo = document.getElementById("t-assuntos-vista");
  titulo.textContent = "Assuntos";
  limpar(corpo,
    el("p", { class: "suave", text: "Grupos temáticos, situações do cotidiano e o catálogo completo. Um assunto pode reunir vários rótulos científicos." }),
    ...Grupos(),
    Situacoes(),
    Formatos(),
    el("p", {}, [el("a", { class: "botao botao-claro", href: "#/explorar", text: "Ver o catálogo completo" })]),
  );
}

function paginaSituacao(id) {
  const s = (catalogo().situacoes || []).find((x) => x.id === id);
  const corpo = document.getElementById("assuntos-corpo");
  const titulo = document.getElementById("t-assuntos-vista");
  if (!s) { lista(); return; }
  titulo.textContent = s.nome;
  const itens = (catalogo().assuntos || []).filter((a) => s.assuntos.includes(a.id));
  limpar(corpo,
    el("p", { class: "suave", text: s.descricao }),
    el("div", { class: "lista-assuntos" }, itens.map(ItemAssunto)),
    el("p", {}, [el("a", { href: "#/assuntos", text: "Todos os assuntos" })]),
  );
}

function paginaGrupo(id) {
  const g = (catalogo().grupos || []).find((x) => x.id === id && x.visivel);
  const corpo = document.getElementById("assuntos-corpo");
  const titulo = document.getElementById("t-assuntos-vista");
  if (!g) { lista(); return; }
  titulo.textContent = g.nome;
  const itens = (catalogo().assuntos || []).filter((a) => g.assuntos.includes(a.id));
  limpar(corpo,
    el("p", { class: "suave", text: g.descricao }),
    el("div", { class: "lista-assuntos" }, itens.map(ItemAssunto)),
    el("p", {}, [el("a", { href: "#/assuntos", text: "Todos os assuntos" })]),
  );
}

function paginaBusca(termo) {
  const corpo = document.getElementById("assuntos-corpo");
  const titulo = document.getElementById("t-assuntos-vista");
  titulo.textContent = "Busca de assuntos";
  const achados = buscarAssuntos(assuntosVisiveis(catalogo()), termo);
  limpar(corpo,
    el("p", { class: "suave", role: "status", text: achados.length ? `${achados.length} assunto${achados.length === 1 ? "" : "s"} para “${termo}”.` : `Nenhum assunto encontrado para “${termo}”.` }),
    achados.length ? el("div", { class: "lista-assuntos" }, achados.map(ItemAssunto)) : EstadoVazio({ titulo: "Nenhum assunto com esse nome", texto: "Tente outra palavra, ou abra os grupos temáticos.", acao: { rotulo: "Ver os grupos", aoClicar: () => { location.hash = "#/assuntos"; } } }),
    el("p", {}, [el("a", { href: "#/assuntos", text: "Todos os assuntos" })]),
  );
}

function CompartilharAssunto(a) {
  const url = urlEstatica(a.id);
  const texto = `Frases do cotidiano sobre ${a.nome}. Como você lê? Veja no É Só Opinião?: ${url}`;
  const status = el("p", { class: "retorno-compartilhar", role: "status" });
  const nativo = navigator.share ? el("button", { type: "button", class: "botao botao-claro", text: "Compartilhar", onclick: async () => {
    try { await navigator.share({ title: a.nome, text: `Frases do cotidiano sobre ${a.nome}.`, url }); status.textContent = "Compartilhado."; } catch (e) { if (e && e.name !== "AbortError") status.textContent = "Não foi possível compartilhar agora."; }
  } }) : null;
  return el("div", { class: "compartilhar" }, [
    el("p", { class: "compartilhar-titulo", text: "Levar este assunto" }),
    el("div", { class: "compartilhar-botoes" }, [
      el("a", { class: "botao botao-claro", href: linkWhatsApp(texto), target: "_blank", rel: "noopener noreferrer", text: "WhatsApp" }),
      nativo,
    ]),
    status,
  ]);
}

function paginaAssunto(id) {
  const a = assuntoPorId(catalogo(), id);
  const corpo = document.getElementById("assuntos-corpo");
  const titulo = document.getElementById("t-assuntos-vista");
  if (!a || !a.visivel) {
    titulo.textContent = "Assunto indisponível";
    limpar(corpo, EstadoVazio({ titulo: "Este assunto não tem exemplos publicados", texto: "Assuntos sem frases aprovadas não abrem uma experiência vazia.", acao: { rotulo: "Ver outros assuntos", aoClicar: () => { location.hash = "#/assuntos"; } } }));
    return;
  }
  titulo.textContent = a.nome;
  const n = Math.min(5, a.n);
  const relacionados = (a.relacionados || []).map((rid) => assuntoPorId(catalogo(), rid)).filter(Boolean);
  const pares = paresValidos(estado.pares, estado.porId).filter((p) => {
    const fa = estado.porId.get(p.a);
    const fb = estado.porId.get(p.b);
    return fa && fb && frasesDoAssunto([fa, fb], a).length === 2;
  });
  const acoes = [
    el("a", { class: "botao", href: a.descobrir, text: n === 1 ? "Descobrir 1 frase" : `Descobrir ${n} frases` }),
    el("a", { class: "botao botao-claro", href: a.explorar, text: "Explorar todas" }),
  ];
  if (pares.length) acoes.push(el("a", { class: "botao botao-claro", href: `#/comparar/${pares[0].slug}`, text: "Comparar duas frases" }));
  limpar(corpo,
    el("p", { class: "eyebrow", text: a.grupo_nome }),
    el("p", { text: a.descricao }),
    el("p", { class: "suave", text: `${a.n} exemplo${a.n === 1 ? "" : "s"} revisado${a.n === 1 ? "" : "s"}.` }),
    el("div", { class: "acoes" }, acoes),
    relacionados.length ? el("section", { class: "subbloco", "aria-labelledby": "t-relacionados" }, [
      el("h2", { id: "t-relacionados", class: "subsecao", text: "Assuntos relacionados" }),
      el("p", { class: "pequeno suave", text: "Sugestões editoriais, sem perfilar quem lê." }),
      el("div", { class: "lista-assuntos" }, relacionados.map(ItemAssunto)),
    ]) : null,
    CompartilharAssunto(a),
    el("p", {}, [el("a", { href: `#/assuntos?grupo=${encodeURIComponent(a.grupo)}`, text: `Voltar a ${a.grupo_nome}` })]),
  );
}

export function ExploradorHome() {
  const cat = catalogo();
  const situacoes = cat.situacoes || [];
  const busca = el("form", { class: "busca-assuntos", role: "search", "aria-label": "Buscar assuntos" });
  const campo = el("input", { type: "search", id: "campo-busca-assuntos", placeholder: "Qual assunto você procura?", autocomplete: "off", enterkeyhint: "search", maxlength: "80", "aria-label": "Qual assunto você procura?" });
  const resultado = el("div", { id: "resultado-busca-assuntos", role: "status", "aria-live": "polite" });
  busca.append(el("label", { class: "busca" }, [campo]), resultado);
  const filtrar = () => {
    const termo = campo.value.trim();
    if (termo.length < 2) { limpar(resultado); return; }
    const achados = buscarAssuntos(assuntosVisiveis(cat), termo).slice(0, 8);
    if (!achados.length) { limpar(resultado, el("p", { class: "pequeno", text: `Nenhum assunto encontrado para “${termo}”.` })); return; }
    limpar(resultado, el("ul", { class: "lista-busca" }, achados.map((a) => el("li", {}, [el("a", { href: a.url, text: `${a.nome} (${a.n})` })]))));
  };
  campo.addEventListener("input", filtrar);
  busca.addEventListener("submit", (e) => {
    e.preventDefault();
    const termo = campo.value.trim();
    if (termo.length >= 2) location.hash = `#/assuntos?q=${encodeURIComponent(termo)}`;
  });
  return el("div", { class: "explorador-assuntos" }, [
    busca,
    el("div", { class: "grupos-tematicos" }, Grupos()),
    situacoes.length ? el("div", { class: "subbloco" }, [
      el("h3", { class: "subsecao", text: "Situações do cotidiano" }),
      el("div", { class: "chips" }, situacoes.map((s) => el("a", { class: "chip", href: s.url, text: s.nome }))),
    ]) : null,
    el("p", { class: "acoes" }, [
      el("a", { class: "botao botao-claro", href: "#/assuntos", text: "Ver todos os assuntos" }),
      el("a", { class: "botao-texto", href: "#/explorar", text: "Catálogo completo" }),
    ]),
  ]);
}

export const assuntos = {
  titulo: "Assuntos",
  rotaAtiva: "assuntos",
  async montar({ param, consulta } = {}) {
    const corpo = document.getElementById("assuntos-corpo");
    const titulo = document.getElementById("t-assuntos-vista");
    corpo.setAttribute("aria-busy", "false");
    if (estado.erro) { limpar(corpo, EstadoErro({ titulo: "Não foi possível carregar os assuntos", texto: "Tente de novo em instantes.", aoTentarDeNovo: () => location.reload() })); return; }
    if (!assuntosVisiveis(catalogo()).length) { limpar(corpo, EstadoVazio({ titulo: "Ainda não há assuntos publicados", texto: "Nada é publicado antes da revisão por uma pessoa." })); return; }
    if (param) paginaAssunto(param);
    else if (consulta && consulta.get("situacao")) paginaSituacao(consulta.get("situacao"));
    else if (consulta && consulta.get("grupo")) paginaGrupo(consulta.get("grupo"));
    else if (consulta && consulta.get("q")) paginaBusca(consulta.get("q"));
    else lista();
    focar(titulo);
  },
};
