// Fixtures e helpers compartilhados pelos testes de interface.
import { test as base, expect } from "@playwright/test";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

export { expect };
const DADOS = join(fileURLToPath(new URL("..", import.meta.url)), ".dados");
export const ENDPOINT_TESTE = "https://formulario.exemplo.test/enviar";

/* `dados: "fixture"` (padrão) serve a biblioteca completa de TESTE (e2e/.dados, gerada por tools/gerar_dados_e2e.py).
   `dados: "real"` usa o que está em site/data (só o que foi aprovado por uma pessoa). */
export const test = base.extend({
  dados: ["fixture", { option: true }],
  page: async ({ page, dados }, use) => {
    if (dados === "fixture") {
      if (!existsSync(join(DADOS, "frases.json"))) throw new Error("rode `npm run preparar-dados` antes dos testes");
      await page.route("**/data/*.json", (route) => {
        const nome = new URL(route.request().url()).pathname.split("/").pop();
        const arquivo = join(DADOS, nome);
        if (!existsSync(arquivo)) return route.continue();
        return route.fulfill({ status: 200, contentType: "application/json", body: readFileSync(arquivo) });
      });
    }
    /* Os testes NUNCA falam com o serviço real de recebimento: por padrão o envio aparece como não
       configurado e qualquer requisição ao Formspree é bloqueada. `configurarEnvio` sobrepõe isto
       com um serviço simulado (rotas registradas depois têm prioridade). */
    await page.route("**/config_participacao.json", (r) => r.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ ativo: false, endpoint: "", modo_resposta: "cors", campos: {} }),
    }));
    await page.route(/^https:\/\/([^/]+\.)?formspree\.io\//, (r) => r.abort("blockedbyclient"));
    await page.route(/^https:\/\/[^/]+\.workers\.dev\//, (r) => r.abort("blockedbyclient"));
    await page.route(/^https:\/\/challenges\.cloudflare\.com\//, (r) => r.abort("blockedbyclient"));
    await use(page);
  },
});

export async function abrir(page, hash = "#/", { semente = 7, extras = "" } = {}) {
  await page.clock.setFixedTime(new Date("2026-10-29T12:00:00-03:00"));
  await page.goto(`/?semente=${semente}${extras}${hash}`);
  await page.waitForFunction(() => document.documentElement.dataset.pronto === "true");
}

export async function irPara(page, hash) {
  await page.evaluate((h) => { location.hash = h; }, hash);
  await page.waitForFunction((h) => location.hash.startsWith(h.split("?")[0]), hash);
}

/** Liga o envio com um serviço simulado. comportamento: ok | erro500 | recusa | rede | opaca | cota | suspenso. Devolve a lista de requisições. */
export async function configurarEnvio(page, comportamento = "ok") {
  const enviados = [];
  const cfg = {
    ativo: true,
    contribuicoes_abertas: comportamento !== "suspenso",
    endpoint: ENDPOINT_TESTE,
    modo_resposta: comportamento === "opaca" ? "opaca" : "cors",
    campos: { tipo: "tipo", frase: "frase", avaliacao: "avaliacao", frase_id: "frase_id", consentimento: "consentimento", armadilha: "site" },
  };
  await page.route("**/config_participacao.json", (r) => r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(cfg) }));
  await page.route(ENDPOINT_TESTE, async (route) => {
    enviados.push({ metodo: route.request().method(), corpo: route.request().postData(), cabecalhos: route.request().headers() });
    const cors = { "access-control-allow-origin": "*" };
    if (comportamento === "rede") return route.abort("failed");
    if (comportamento === "erro500") return route.fulfill({ status: 500, headers: cors, contentType: "application/json", body: '{"error":"falha interna"}' });
    if (comportamento === "recusa") return route.fulfill({ status: 422, headers: cors, contentType: "application/json", body: '{"ok":false,"error":"campo invalido"}' });
    if (comportamento === "cota") return route.fulfill({ status: 402, headers: cors, contentType: "application/json", body: '{"error":"form over quota"}' });
    return route.fulfill({ status: 200, headers: cors, contentType: "application/json", body: '{"ok":true}' });
  });
  return enviados;
}

const ENDPOINT_CF = "https://api.exemplo.test/api/v1/participacoes";
const SCRIPT_TURNSTILE = `
window.turnstile = {
  render(el, opts) {
    queueMicrotask(function () { if (opts && opts.callback) opts.callback("XXXX.DUMMY.TOKEN.XXXX"); });
    return 1;
  },
  reset: function () {},
  remove: function () {},
  getResponse: function () { return "XXXX.DUMMY.TOKEN.XXXX"; },
  ready: function (cb) { cb(); }
};
`;

/** Liga o envio Cloudflare com Turnstile simulado. Não fala com workers.dev nem com o Siteverify real. */
export async function configurarEnvioCloudflare(page, comportamento = "ok") {
  const enviados = [];
  const cfg = {
    ativo: true,
    contribuicoes_abertas: comportamento !== "suspenso",
    provedor: "cloudflare",
    endpoint: ENDPOINT_CF,
    turnstile_sitekey: "1x00000000000000000000AA",
    modo_resposta: "cors",
    campos: { tipo: "tipo", frase: "frase", avaliacao: "avaliacao", frase_id: "frase_id", consentimento: "consentimento", armadilha: "site" },
  };
  await page.route("**/config_participacao.json", (r) => r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(cfg) }));
  await page.route(/^https:\/\/challenges\.cloudflare\.com\/turnstile\/v0\/api\.js.*/, (route) =>
    route.fulfill({ status: 200, contentType: "application/javascript", body: SCRIPT_TURNSTILE }));
  await page.route(ENDPOINT_CF, async (route) => {
    enviados.push({ metodo: route.request().method(), corpo: route.request().postData(), cabecalhos: route.request().headers() });
    const cors = { "access-control-allow-origin": "http://127.0.0.1:4173", "access-control-allow-headers": "Content-Type" };
    if (route.request().method() === "OPTIONS") return route.fulfill({ status: 204, headers: cors });
    if (comportamento === "rede") return route.abort("failed");
    if (comportamento === "erro500") return route.fulfill({ status: 500, headers: cors, contentType: "application/json", body: '{"ok":false,"erro":"indisponivel"}' });
    if (comportamento === "recusa") return route.fulfill({ status: 422, headers: cors, contentType: "application/json", body: '{"ok":false,"erro":"validacao"}' });
    if (comportamento === "turnstile") return route.fulfill({ status: 403, headers: cors, contentType: "application/json", body: '{"ok":false,"erro":"turnstile"}' });
    return route.fulfill({ status: 200, headers: cors, contentType: "application/json", body: '{"ok":true,"submission_id":"550e8400-e29b-41d4-a716-446655440000"}' });
  });
  return enviados;
}

export const VIEWPORTS = [
  { nome: "320", largura: 320, altura: 640 },
  { nome: "360", largura: 360, altura: 740 },
  { nome: "375", largura: 375, altura: 667 },
  { nome: "390", largura: 390, altura: 844 },
  { nome: "430", largura: 430, altura: 932 },
  { nome: "768", largura: 768, altura: 1024 },
  { nome: "1024", largura: 1024, altura: 768 },
  { nome: "1440", largura: 1440, altura: 900 },
];
export const PAISAGEM = [
  { nome: "375-paisagem", largura: 667, altura: 375 },
  { nome: "390-paisagem", largura: 844, altura: 390 },
  { nome: "430-paisagem", largura: 932, altura: 430 },
];
export const ROTAS = ["#/", "#/descobrir", "#/explorar", "#/frase/EX-61", "#/participar", "#/entender", "#/pesquisa", "#/assuntos", "#/assuntos/racismo"];

/** Tecla para andar entre controles. No Safari/WebKit do macOS, Tab pula links por padrão (só Option+Tab os alcança): é
    comportamento do navegador, não do site, então o teste usa a tecla equivalente. */
export const teclaTab = (page) => (page.context().browser().browserType().name() === "webkit" && process.platform === "darwin" ? "Alt+Tab" : "Tab");
