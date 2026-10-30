/* Desafio humano (Turnstile) só no envio, nunca na navegação. Sem innerHTML. A sitekey é pública. */
const SCRIPT = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
let carregando = null;
const widgets = new WeakMap();

export function usaCloudflare(config) {
  return !!(config && config.provedor === "cloudflare");
}

function carregarScript() {
  if (typeof window !== "undefined" && window.turnstile) return Promise.resolve();
  if (carregando) return carregando;
  carregando = new Promise((ok, falha) => {
    const ja = document.querySelector('script[data-desafio="1"]');
    if (ja) {
      ja.addEventListener("load", () => ok());
      ja.addEventListener("error", () => falha(new Error("turnstile")));
      return;
    }
    const s = document.createElement("script");
    s.src = SCRIPT;
    s.async = true;
    s.defer = true;
    s.dataset.desafio = "1";
    s.onload = () => ok();
    s.onerror = () => falha(new Error("turnstile"));
    document.head.append(s);
  });
  return carregando;
}

function chavePublica(caixa, sitekey) {
  return sitekey || (caixa && caixa.getAttribute("data-sitekey")) || "";
}

export async function prepararDesafio(caixa, sitekey) {
  sitekey = chavePublica(caixa, sitekey);
  if (!caixa || !sitekey) throw new Error("turnstile");
  caixa.hidden = false;
  await carregarScript();
  if (!window.turnstile) throw new Error("turnstile");
  const existente = widgets.get(caixa);
  if (existente != null) {
    try { window.turnstile.reset(existente); } catch { /* widget ainda válido */ }
    return existente;
  }
  const id = window.turnstile.render(caixa, {
    sitekey,
    action: "participacao",
    appearance: "always",
    size: "flexible",
    theme: "light",
    "refresh-expired": "auto",
  });
  widgets.set(caixa, id);
  return id;
}

export async function tokenDesafio(caixa, sitekey) {
  const id = await prepararDesafio(caixa, sitekey);
  const imediato = window.turnstile.getResponse(id);
  if (imediato) return imediato;
  return new Promise((ok, falha) => {
    const t = setTimeout(() => falha(new Error("turnstile")), 25000);
    const espera = setInterval(() => {
      const v = window.turnstile.getResponse(id);
      if (v) { clearInterval(espera); clearTimeout(t); ok(v); }
    }, 200);
  });
}

export function resetarDesafio(caixa) {
  const id = caixa && widgets.get(caixa);
  if (id == null || !window.turnstile) return;
  try { window.turnstile.reset(id); } catch { /* ignore */ }
}
