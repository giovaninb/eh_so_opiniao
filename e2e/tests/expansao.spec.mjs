// Expansão 2026-10: temas de descoberta (Mulheres, Homens, Pessoas idosas, Religiões, Pessoas trans), avisos de conteúdo,
// dados de contexto e larguras de 320 a 768 px. Os dados vêm da fixture de TESTE (e2e/.dados): nada disso é publicação real.
import { test, expect, abrir } from "./fixtures.mjs";
import AxeBuilder from "@axe-core/playwright";

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const GRUPOS = ["Mulheres", "Homens e expectativas sociais", "Pessoas idosas", "Religiões", "Pessoas trans"];
const LARGURAS = [320, 360, 390, 430, 768];
const corpo = (page) => page.locator("#descobrir-corpo");

async function escolherTema(page, nome) {
  const resumo = page.locator("details.temas-descoberta > summary");
  if (!(await page.locator("details.temas-descoberta").evaluate((d) => d.open))) await resumo.click();
  await page.locator("details.temas-descoberta").getByRole("button", { name: new RegExp(`^${nome}`) }).click();
}

test("Descobrir oferece os cinco temas pedidos, mais 'Ao acaso', sem pontuação nem ranking", async ({ page }) => {
  await abrir(page, "#/descobrir");
  await page.locator("details.temas-descoberta > summary").click();
  const botoes = page.locator("details.temas-descoberta .chip");
  const nomes = await botoes.allTextContents();
  expect(nomes[0]).toBe("Ao acaso");
  for (const g of GRUPOS) expect(nomes.some((n) => n.startsWith(g)), g).toBe(true);
  await expect(page.locator("details.temas-descoberta .chip[aria-pressed=true]")).toHaveText("Ao acaso");
  await expect(corpo(page)).not.toContainText(/pontos|ranking|acertou|errou|nota:|placar/i);
});

for (const grupo of GRUPOS) {
  test(`tema "${grupo}": sessão de cinco frases só desse tema, com pular e análise sem votar`, async ({ page }) => {
    await abrir(page, "#/descobrir");
    await escolherTema(page, grupo);
    await expect(page.locator(".progresso")).toContainText("1 de 5");
    await expect(page.locator("details.temas-descoberta .chip[aria-pressed=true]")).toContainText(grupo);
    await expect(page.locator("details.temas-descoberta > summary")).toContainText(`Tema: ${grupo}`);
    // a frase vem antes da interpretação
    const cartao = corpo(page).locator(".cartao-frase");
    await expect(cartao.locator(".frase")).toBeVisible();
    await expect(cartao.locator(".revelacao")).toHaveCount(0);
    await page.getByRole("button", { name: "Pular" }).click();
    await expect(page.locator(".progresso")).toContainText("2 de 5");
    await page.getByRole("button", { name: "Ver análise sem responder" }).click();
    await expect(page.locator(".revelacao")).toContainText("Você viu a análise sem responder.");
  });
}

test("as cinco frases sorteadas pertencem ao tema escolhido", async ({ page }) => {
  await abrir(page, "#/descobrir");
  await escolherTema(page, "Pessoas idosas");
  const textos = [];
  for (let i = 0; i < 5; i++) {
    textos.push(await corpo(page).locator(".cartao-frase .frase").textContent());
    if (i < 4) await page.getByRole("button", { name: "Pular" }).click();
  }
  const grupos = await page.evaluate(async (lista) => {
    const d = await (await fetch("/data/frases.json")).json();
    return lista.map((t) => d.frases.find((f) => f.texto === t)?.grupo);
  }, textos);
  expect(grupos).toEqual(Array(5).fill("pessoas_idosas"));
});

test("Pessoas trans mostra dados de contexto com fonte, ano, metodologia e limites, e sem afirmar '35 anos'", async ({ page }) => {
  await abrir(page, "#/descobrir");
  await expect(page.locator("details.contexto-dados")).toHaveCount(0); // só aparece no tema Pessoas trans
  await escolherTema(page, "Pessoas trans");
  const ctx = page.locator("details.contexto-dados");
  await expect(ctx).toBeVisible();
  await expect(ctx.locator("dl").first()).toBeHidden(); // fechado por padrão
  await ctx.locator("summary").click();
  await expect(ctx).toContainText("80 assassinatos");
  for (const rotulo of ["Dado", "Fonte", "Ano", "Metodologia", "Limitações"]) await expect(ctx.locator("dt", { hasText: new RegExp(`^${rotulo}$`) }).first()).toBeVisible();
  await expect(ctx).toContainText(/subnotifica/i);
  await expect(ctx).toContainText("não afirma que “pessoas trans vivem até 35 anos”");
  const links = ctx.locator("a");
  expect(await links.count()).toBeGreaterThanOrEqual(2);
  for (const a of await links.all()) { await expect(a).toHaveAttribute("rel", "noopener noreferrer"); await expect(a).toHaveAttribute("target", "_blank"); }
  await escolherTema(page, "Mulheres");
  await expect(page.locator("details.contexto-dados")).toHaveCount(0);
});

test("aviso de conteúdo: aparece antes da frase, não bloqueia e deixa pular ou ver a análise", async ({ page }) => {
  await abrir(page, "#/frase/NX-326");
  const cartao = page.locator(".cartao-frase");
  const aviso = cartao.locator(".aviso-conteudo");
  await expect(aviso).toBeVisible();
  await expect(aviso).toHaveAttribute("role", "note");
  await expect(aviso).toContainText("Aviso de conteúdo");
  await expect(cartao.locator(".aviso-chip")).toHaveText("Aviso de conteúdo");
  await expect(cartao.locator(".frase")).toContainText("macumba");
  const posicoes = await page.evaluate(() => [document.querySelector(".aviso-conteudo"), document.querySelector(".cartao-frase .frase")].map((n) => n.getBoundingClientRect().top));
  expect(posicoes[0]).toBeLessThan(posicoes[1]);
  await cartao.getByRole("button", { name: "Ver análise sem responder" }).click();
  await expect(cartao.locator(".revelacao")).toBeVisible();
});

test("frases ambíguas ou sem termo pejorativo não recebem aviso de conteúdo", async ({ page }) => {
  for (const id of ["NX-397", "NX-385", "NX-422"]) {
    await abrir(page, `#/frase/${id}`);
    await expect(page.locator(".cartao-frase .frase")).toBeVisible();
    await expect(page.locator(".aviso-conteudo, .aviso-chip")).toHaveCount(0);
  }
});

test("título da página e compartilhamento não repetem o termo pejorativo", async ({ page }) => {
  await abrir(page, "#/frase/NX-326");
  expect(await page.title()).not.toMatch(/macumba/i);
  expect(await page.title()).toBe("NX-326 — É Só Opinião?");
  const href = await page.locator("section.compartilhar").getByRole("link", { name: /WhatsApp/ }).getAttribute("href");
  const mensagem = decodeURIComponent(href.split("text=")[1]);
  expect(mensagem).not.toMatch(/macumba/i);
  expect(mensagem).toMatch(/\/casos\/nx-326\/$/); // a prévia do link (página estática) é que mostra a frase, e ela omite a frase com aviso
});

test("o destaque da página inicial nunca é uma frase com aviso de conteúdo, em nenhum dia do ano", async ({ page }) => {
  await abrir(page, "#/");
  const r = await page.evaluate(async () => {
    const { fraseDeAbertura } = await import("/js/nucleo/logica.js");
    const d = await (await fetch("/data/frases.json")).json();
    const com = d.frases.filter((f) => f.aviso_conteudo).length;
    const escolhidas = [];
    for (let i = 0; i < 400; i++) escolhidas.push(fraseDeAbertura(d.frases, new Date(2026, 0, 1 + i)));
    return { com, algumaComAviso: escolhidas.some((f) => f && f.aviso_conteudo), nulas: escolhidas.filter((f) => !f).length,
      soAvisos: fraseDeAbertura(d.frases.filter((f) => f.aviso_conteudo)) };
  });
  expect(r.com).toBeGreaterThan(0);
  expect(r.algumaComAviso).toBe(false);
  expect(r.nulas).toBe(0);
  expect(r.soAvisos).toBeNull();
});

test("Explorar mostra o chip de aviso nas frases marcadas e filtra por Transfobia", async ({ page }) => {
  await abrir(page, "#/explorar");
  await page.getByRole("searchbox", { name: "Buscar nas frases" }).fill("Chuta que é macumba");
  const item = page.locator("#explorar-lista .item-frase").first();
  await expect(item.locator(".aviso-chip")).toHaveText("Aviso de conteúdo");
  await page.getByRole("searchbox").fill("");
  await page.getByText("Filtros", { exact: true }).click();
  await page.locator("#filtro-tema").selectOption("transfobia");
  await expect(page.locator("#explorar-lista .item-frase").first()).toBeVisible();
  const temas = await page.locator("#explorar-lista .item-frase .meta .tema").allTextContents();
  expect(temas.length).toBeGreaterThan(0);
  expect(new Set(temas)).toEqual(new Set(["Transfobia"]));
});

for (const largura of LARGURAS) {
  test(`sem rolagem horizontal em ${largura}px: temas, contexto trans e frase com aviso`, async ({ page }) => {
    await page.setViewportSize({ width: largura, height: largura < 500 ? 800 : 1024 });
    const sobra = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    await abrir(page, "#/descobrir");
    await page.locator("details.temas-descoberta > summary").click();
    expect(await sobra()).toBeLessThanOrEqual(0);
    for (const alvo of await page.locator("details.temas-descoberta .chip").all()) {
      const b = await alvo.boundingBox();
      expect(b.height, "alvo de toque ≥ 44 px").toBeGreaterThanOrEqual(43.5);
      expect(b.x + b.width).toBeLessThanOrEqual(largura + 0.5);
    }
    await escolherTema(page, "Pessoas trans");
    await page.locator("details.contexto-dados summary").click();
    expect(await sobra()).toBeLessThanOrEqual(0);
    await abrir(page, "#/frase/NX-326");
    expect(await sobra()).toBeLessThanOrEqual(0);
    await expect(page.locator(".aviso-conteudo:visible")).toBeVisible();
  });
}

test("fonte a 200%: temas e aviso continuam legíveis, sem rolagem horizontal", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await abrir(page, "#/descobrir");
  await page.addStyleTag({ content: "html{font-size:200% !important}" });
  await page.locator("details.temas-descoberta > summary").click();
  await escolherTema(page, "Religiões");
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(0);
  await abrir(page, "#/frase/NX-326");
  await page.addStyleTag({ content: "html{font-size:200% !important}" });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(0);
});

test("teclado: os temas são botões com estado (aria-pressed) e o foco é visível", async ({ page }) => {
  await abrir(page, "#/descobrir");
  await page.locator("details.temas-descoberta > summary").focus();
  await page.keyboard.press("Enter");
  const chip = page.locator("details.temas-descoberta .chip", { hasText: "Religiões" });
  await chip.focus();
  const contorno = await chip.evaluate((e) => getComputedStyle(e).outlineStyle + "|" + getComputedStyle(e).outlineWidth);
  expect(contorno).not.toMatch(/^none/);
  await page.keyboard.press("Enter");
  await expect(page.locator("details.temas-descoberta .chip[aria-pressed=true]")).toContainText("Religiões");
  await expect(page.locator("details.temas-descoberta .chip[aria-pressed=false]").first()).toBeVisible();
});

test("axe: tema escolhido, contexto trans aberto e frase com aviso, sem violações WCAG 2.2 AA", async ({ page }) => {
  const resumo = (v) => v.map((x) => `${x.id} (${x.impact}): ${x.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
  await abrir(page, "#/descobrir");
  await escolherTema(page, "Pessoas trans");
  await page.locator("details.contexto-dados summary").click();
  expect(resumo((await new AxeBuilder({ page }).withTags(TAGS).analyze()).violations)).toEqual([]);
  await abrir(page, "#/frase/NX-326");
  expect(resumo((await new AxeBuilder({ page }).withTags(TAGS).analyze()).violations)).toEqual([]);
});
