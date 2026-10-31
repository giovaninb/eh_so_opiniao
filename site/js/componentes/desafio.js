/* Desafio humano (Turnstile) só no envio, nunca na navegação. Sem innerHTML. A sitekey é pública.
   Não reinicie o widget na hora de enviar: no celular isso apaga o visto e o POST nunca sai. */
const SCRIPT = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
const ESPERA_MS = 90000;
let carregando = null;
const widgets = new WeakMap();
const emPreparacao = new WeakMap();

export function usaCloudflare(config) {
  return !!(config && config.provedor !== "formspree" && config.turnstile_sitekey);
}

export function rotuloEnvio(s) {
  if (s === "aguardando") return "Confirme que é humano…";
  if (s === "verificando") return "Verificando proteção…";
  if (s === "validando") return "Validando…";
  return "Enviando…";
}

function carregarScript() {
  if (typeof window !== "undefined" && window.turnstile) return Promise.resolve();
  if (carregando) return carregando;
  const p = new Promise((ok, falha) => {
    const t = setTimeout(() => falha(new Error("turnstile")), 12000);
    const pronto = () => {
      clearTimeout(t);
      if (window.turnstile) ok();
      else falha(new Error("turnstile"));
    };
    const ja = document.querySelector('script[data-desafio="1"]');
    if (ja) {
      if (window.turnstile) return pronto();
      ja.addEventListener("load", pronto);
      ja.addEventListener("error", () => { clearTimeout(t); falha(new Error("turnstile")); });
      return;
    }
    const s = document.createElement("script");
    s.src = SCRIPT;
    s.async = true;
    s.defer = true;
    s.dataset.desafio = "1";
    s.onload = pronto;
    s.onerror = () => { clearTimeout(t); falha(new Error("turnstile")); };
    document.head.append(s);
  });
  carregando = p;
  p.catch(() => { if (carregando === p) carregando = null; });
  return p;
}

function chavePublica(caixa, sitekey) {
  return sitekey || (caixa && caixa.getAttribute("data-sitekey")) || "";
}

function guardar(caixa, patch) {
  widgets.set(caixa, { ...(widgets.get(caixa) || {}), ...patch });
}

function lerToken(caixa, id) {
  const st = widgets.get(caixa);
  if (st && st.token) return st.token;
  try {
    return (window.turnstile && window.turnstile.getResponse(id)) || "";
  } catch {
    return "";
  }
}

export async function prepararDesafio(caixa, sitekey) {
  sitekey = chavePublica(caixa, sitekey);
  if (!caixa || !sitekey) throw new Error("turnstile");
  caixa.hidden = false;
  const existente = widgets.get(caixa);
  if (existente && existente.id != null) return existente.id;
  const pendente = emPreparacao.get(caixa);
  if (pendente) return pendente;
  const trabalho = (async () => {
    await carregarScript();
    if (!window.turnstile) throw new Error("turnstile");
    const deNovo = widgets.get(caixa);
    if (deNovo && deNovo.id != null) return deNovo.id;
    const id = window.turnstile.render(caixa, {
      sitekey,
      action: "participacao",
      appearance: "always",
      size: "flexible",
      theme: "light",
      "refresh-expired": "auto",
      callback(token) { guardar(caixa, { token: token || "", erro: false }); },
      "expired-callback"() { guardar(caixa, { token: "" }); },
      "error-callback"() { guardar(caixa, { token: "", erro: true }); },
      "timeout-callback"() { guardar(caixa, { token: "", erro: true }); },
    });
    if (id == null) throw new Error("turnstile");
    widgets.set(caixa, { id, token: "", erro: false });
    return id;
  })();
  emPreparacao.set(caixa, trabalho);
  try { return await trabalho; }
  finally { emPreparacao.delete(caixa); }
}

export async function tokenDesafio(caixa, sitekey, { onEspera } = {}) {
  const id = await prepararDesafio(caixa, sitekey);
  const ja = lerToken(caixa, id);
  if (ja) return ja;
  if (onEspera) onEspera();
  try { caixa.scrollIntoView({ block: "center", behavior: "smooth" }); } catch { /* viewport sem scroll */ }
  return new Promise((ok, falha) => {
    const t = setTimeout(() => falha(new Error("turnstile")), ESPERA_MS);
    const espera = setInterval(() => {
      const v = lerToken(caixa, id);
      const st = widgets.get(caixa);
      if (v) { clearInterval(espera); clearTimeout(t); ok(v); }
      else if (st && st.erro) { clearInterval(espera); clearTimeout(t); falha(new Error("turnstile")); }
    }, 200);
  });
}

export function resetarDesafio(caixa) {
  const st = caixa && widgets.get(caixa);
  if (!st || st.id == null || !window.turnstile) return;
  st.token = "";
  st.erro = false;
  try { window.turnstile.reset(st.id); } catch { /* ignore */ }
}
