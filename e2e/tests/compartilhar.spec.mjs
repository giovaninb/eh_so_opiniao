import { test, expect, abrir } from "./fixtures.mjs";

const secao = (page) => page.locator("section.compartilhar");

test("o convite para compartilhar aparece já na frase, antes de responder", async ({ page }) => {
  await abrir(page, "#/frase/EX-01");
  await expect(secao(page)).toBeVisible();
  await expect(secao(page)).toContainText("Quer ouvir outra pessoa sobre esta frase?");
  await expect(page.locator("details.ia")).toHaveCount(0); // compartilhar não revela a análise
});

test("link do WhatsApp: mensagem em tom de pergunta, com a frase e o link direto, sem rótulos", async ({ page }) => {
  await abrir(page, "#/frase/EX-01");
  const link = secao(page).getByRole("link", { name: /WhatsApp/ });
  await expect(link).toHaveAttribute("target", "_blank");
  await expect(link).toHaveAttribute("rel", "noopener noreferrer");
  const href = await link.getAttribute("href");
  expect(href).toMatch(/^https:\/\/wa\.me\/\?text=/);
  const mensagem = decodeURIComponent(href.split("text=")[1]);
  expect(mensagem).toContain("Onde você coloca a linha?");
  expect(mensagem).toMatch(/\/casos\/ex-01\/$/); // link estável para a página estática, com prévia própria
  expect(mensagem).not.toContain("#/");
  expect(mensagem).not.toMatch(/preconceituos|racista|culpad|crime/i);
});

test("copiar mensagem usa a área de transferência e avisa a pessoa", async ({ page }) => {
  await page.addInitScript(() => { window.__copiado = null; Object.defineProperty(navigator, "clipboard", { value: { writeText: async (t) => { window.__copiado = t; } }, configurable: true }); });
  await abrir(page, "#/frase/EX-01");
  await secao(page).getByRole("button", { name: "Copiar link" }).click();
  await expect(secao(page).locator("[role=status]")).toHaveText("Link copiado.");
  expect(await page.evaluate(() => window.__copiado)).toMatch(/^http:\/\/[^/]+\/casos\/ex-01\/$/);
});

test("com Web Share disponível (celulares), o botão Compartilhar abre o menu do sistema", async ({ page }) => {
  await page.addInitScript(() => { window.__compartilhado = null; navigator.share = async (d) => { window.__compartilhado = d; }; });
  await abrir(page, "#/frase/EX-01");
  await secao(page).getByRole("button", { name: "Compartilhar", exact: true }).click();
  const dados = await page.evaluate(() => window.__compartilhado);
  expect(dados.title).toBe("É Só Opinião?");
  expect(dados.text).toContain("/casos/ex-01/");
});

test("sem Web Share (computador), não há botão Compartilhar, só WhatsApp e copiar", async ({ page }) => {
  await page.addInitScript(() => { Object.defineProperty(navigator, "share", { value: undefined, configurable: true }); });
  await abrir(page, "#/frase/EX-01");
  await expect(secao(page).getByRole("button", { name: "Compartilhar", exact: true })).toHaveCount(0);
  await expect(secao(page).getByRole("button", { name: "Copiar link" })).toBeVisible();
});

test("compartilhar não envia nada a ninguém: nenhuma requisição externa é feita ao abrir a frase", async ({ page }) => {
  const externas = [];
  page.on("request", (r) => { const u = new URL(r.url()); if (!["localhost", "127.0.0.1"].includes(u.hostname) && u.protocol.startsWith("http")) externas.push(r.url()); });
  await abrir(page, "#/frase/EX-01");
  expect(externas).toEqual([]);
});

test("a seção cabe em telas estreitas, sem rolagem horizontal, e os botões têm área de toque adequada", async ({ page }) => {
  await abrir(page, "#/frase/EX-01");
  const sobra = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(sobra).toBeLessThanOrEqual(0);
  for (const alvo of await secao(page).locator("a.botao, button.botao").all()) {
    const caixa = await alvo.boundingBox();
    expect(caixa.height).toBeGreaterThanOrEqual(44);
  }
});
