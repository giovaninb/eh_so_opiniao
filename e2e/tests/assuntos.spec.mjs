import { test, expect, abrir } from "./fixtures.mjs";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const SITE = fileURLToPath(new URL("../../site", import.meta.url));
const DADOS = join(fileURLToPath(new URL("..", import.meta.url)), ".dados");
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const LARGURAS = [320, 360, 375, 390, 430, 768, 1024, 1440];

function lerAssuntos(dir) {
  return JSON.parse(readFileSync(join(dir, "assuntos.json"), "utf8"));
}

test("o JSON de assuntos só conta frases aprovadas e esconde os vazios", () => {
  const pub = JSON.parse(readFileSync(join(SITE, "data", "frases.json"), "utf8"));
  const camada = JSON.parse(readFileSync(join(SITE, "data", "assuntos.json"), "utf8"));
  const ids = new Set(pub.frases.map((f) => f.id));
  expect(pub.frases.every((f) => /^(Aprovado|Corrigido|Ambíguo)$/.test(f.revisao.estado))).toBe(true);
  for (const a of camada.assuntos) {
    if (a.visivel) expect(a.n).toBeGreaterThan(0);
    else expect(a.n).toBe(0);
  }
  expect(camada.assuntos.find((a) => a.id === "assedio_eleitoral")?.visivel).toBe(false);
  expect(ids.size).toBe(pub.frases.length);
});

test("busca encontra sinônimos sem perfilar", async ({ page }) => {
  await abrir(page, "#/");
  const campo = page.getByLabel("Qual assunto você procura?");
  const casos = [
    ["Nordeste", /nordestin|regional|xenofobia/i],
    ["Cabelo crespo", /racismo/i],
    ["Bissexual", /bissexual|orientação/i],
    ["Girassol", /não aparente/i],
    ["Velho", /idos|etarismo/i],
    ["Umbanda", /matriz africana|religi/i],
    ["Relacionamento aberto", /não monogâm/i],
    ["Eleitor", /polític/i],
  ];
  for (const [termo, padrao] of casos) {
    await campo.fill(termo);
    const itens = page.locator("#resultado-busca-assuntos a");
    await expect(itens.first(), termo).toBeVisible();
    const textos = await itens.allTextContents();
    expect(textos.some((t) => padrao.test(t)), `${termo} → ${textos.join(" | ")}`).toBe(true);
  }
});

test("grupo abre assuntos e o link direto salta as camadas", async ({ page }) => {
  await abrir(page, "#/assuntos/racismo");
  await expect(page.getByRole("heading", { level: 1, name: "Racismo" })).toBeVisible();
  const vista = page.locator("#v-assuntos");
  await expect(vista.getByRole("link", { name: /Descobrir \d/ })).toBeVisible();
  await expect(vista.getByRole("link", { name: /Explorar todas/ })).toBeVisible();
  await vista.getByRole("link", { name: /Explorar todas/ }).click();
  await expect(page).toHaveURL(/assunto=racismo/);
  await expect(page.locator("#faixa-assunto")).toContainText("Racismo");
});

test("assunto sem exemplos publicados não oferece ação falsa", async ({ page }) => {
  await abrir(page, "#/assuntos/assedio_eleitoral");
  await expect(page.getByRole("heading", { level: 1, name: "Assunto indisponível" })).toBeVisible();
  await expect(page.locator("#v-assuntos").getByRole("link", { name: /Descobrir \d/ })).toHaveCount(0);
});

test("Descobrir por assunto usa só frases publicadas e no máximo cinco", async ({ page }) => {
  await abrir(page, "#/descobrir?assunto=ateismo");
  const progresso = page.locator(".progresso");
  const texto = await progresso.textContent();
  expect(texto).toMatch(/1 de [12] situações?/);
  expect(texto).not.toMatch(/de 5/);
  const frases = [];
  const n = Number(texto.match(/de (\d+)/)[1]);
  for (let i = 0; i < n; i++) {
    frases.push(await page.locator("#descobrir-corpo .cartao-frase .frase").textContent());
    if (i < n - 1) await page.getByRole("button", { name: "Pular" }).click();
  }
  const dados = JSON.parse(readFileSync(join(DADOS, "frases.json"), "utf8"));
  const camada = lerAssuntos(DADOS);
  const assunto = camada.assuntos.find((a) => a.id === "ateismo");
  for (const t of frases) {
    const f = dados.frases.find((x) => `“${x.texto}”` === t || x.texto === t.replace(/^[“"]|[”"]$/g, ""));
    expect(f, t).toBeTruthy();
    expect(f.revisao.estado).toMatch(/Aprovado|Corrigido|Ambíguo/);
  }
  expect(assunto.n).toBeGreaterThanOrEqual(n);
});

test("bissexualidade também pertence à orientação sexual", async ({ page }) => {
  const camada = lerAssuntos(join(SITE, "data"));
  const bi = camada.assuntos.find((a) => a.id === "bissexualidade");
  const ori = camada.assuntos.find((a) => a.id === "orientacao_sexual");
  expect(bi.pai).toBe("orientacao_sexual");
  expect(bi.n).toBeGreaterThan(0);
  expect(ori.n).toBeGreaterThan(bi.n);
});

for (const w of LARGURAS) {
  test(`sem rolagem horizontal em ${w}px`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: 740 });
    await abrir(page, "#/");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `home ${w}`).toBeLessThanOrEqual(1);
    await abrir(page, "#/assuntos");
    const overflow2 = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow2, `assuntos ${w}`).toBeLessThanOrEqual(1);
  });
}

test("assuntos: axe wcag 2.2 aa na home e na página de um assunto", async ({ page }) => {
  await abrir(page, "#/");
  const home = await new AxeBuilder({ page }).withTags(TAGS).exclude(".cartao-frase").analyze();
  expect(home.violations, JSON.stringify(home.violations, null, 2)).toEqual([]);
  await abrir(page, "#/assuntos/racismo");
  const assunto = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  expect(assunto.violations, JSON.stringify(assunto.violations, null, 2)).toEqual([]);
});
