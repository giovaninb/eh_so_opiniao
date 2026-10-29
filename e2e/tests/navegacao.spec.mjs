import { teclaTab, test, expect, abrir, irPara } from "./fixtures.mjs";

const ehDesktop = (page) => page.viewportSize().width >= 960;

test.beforeEach(async ({ page }) => {
  page.on("pageerror", (e) => { throw e; });
});

test("a página carrega sem erros de console e com o título esperado", async ({ page }) => {
  const erros = [];
  page.on("console", (m) => { if (m.type() === "error") erros.push(m.text()); });
  await abrir(page);
  await expect(page).toHaveTitle(/É Só Opinião\?/);
  await expect(page.getByRole("heading", { level: 1, name: "É Só Opinião?" })).toBeVisible();
  expect(erros).toEqual([]);
});

test("cabeçalho compacto: uma única linha no celular, sem oito links", async ({ page }) => {
  test.skip(ehDesktop(page), "regra do celular");
  await abrir(page);
  const caixa = await page.locator("#topo").boundingBox();
  expect(caixa.height).toBeLessThanOrEqual(64);
  await expect(page.locator(".nav-desktop")).toBeHidden();
  await expect(page.locator(".barra-inferior a")).toHaveCount(4);
});

test("menu do celular abre, fecha com Esc, com clique fora e ao escolher um destino", async ({ page }) => {
  test.skip(ehDesktop(page), "menu só existe no celular");
  await abrir(page);
  const botao = page.getByRole("button", { name: "Menu" });
  const painel = page.locator("#painel-menu");
  await expect(botao).toHaveAttribute("aria-expanded", "false");
  await botao.click();
  await expect(botao).toHaveAttribute("aria-expanded", "true");
  await expect(painel).toBeVisible();
  await expect(painel.getByRole("link")).toHaveCount(7); // inclui "Comparar" (os dados de teste têm comparações revisadas)
  await page.keyboard.press("Escape");
  await expect(painel).toBeHidden();
  await expect(botao).toBeFocused(); // fechamento previsível: o foco volta ao botão
  await botao.click();
  await page.locator("main").click({ position: { x: 10, y: 10 }, force: true });
  await expect(painel).toBeHidden();
  await botao.click();
  await painel.getByRole("link", { name: /Entender/ }).click();
  await expect(painel).toBeHidden();
  await expect(page).toHaveURL(/#\/entender$/);
  await expect(page.getByRole("heading", { level: 1, name: "Opinião ou discriminação?" })).toBeVisible();
});

test("destino atual é indicado (aria-current) e o foco vai para o título da vista", async ({ page }) => {
  await abrir(page);
  const alvo = ehDesktop(page) ? page.locator(".nav-desktop") : page.locator(".barra-inferior");
  await expect(alvo.locator('[aria-current="page"]')).toHaveText(/Início/);
  await alvo.getByRole("link", { name: "Explorar" }).click();
  await expect(page).toHaveURL(/#\/explorar/);
  await expect(alvo.locator('[aria-current="page"]')).toHaveText("Explorar");
  await expect(page.getByRole("heading", { level: 1, name: "Explorar as frases" })).toBeVisible();
  await alvo.getByRole("link", { name: "Participar" }).click();
  await expect(alvo.locator('[aria-current="page"]')).toHaveText("Participar");
  await expect(page).toHaveTitle(/Participar/);
});

test("todas as rotas e âncoras internas levam a uma vista visível", async ({ page }) => {
  await abrir(page);
  const hrefs = await page.locator('a[href^="#/"]').evaluateAll((as) => [...new Set(as.map((a) => a.getAttribute("href")))]);
  expect(hrefs.length).toBeGreaterThanOrEqual(6);
  for (const h of hrefs) {
    await irPara(page, h);
    await expect(page.locator("[data-vista]:not([hidden])")).toHaveCount(1);
  }
  await irPara(page, "#/rota-que-nao-existe");
  await expect(page.getByRole("heading", { level: 1, name: "É Só Opinião?" })).toBeVisible(); // cai no início
});

test("os botões principais da home levam a Descobrir e Entender", async ({ page }) => {
  await abrir(page);
  await page.getByRole("link", { name: "Entenda o projeto" }).click();
  await expect(page).toHaveURL(/#\/entender$/);
  await page.goBack();
  await page.getByRole("link", { name: "Explore uma frase" }).click();
  await expect(page).toHaveURL(/#\/descobrir$/);
});

test("teclado: pular para o conteúdo, ordem de tabulação e foco visível", async ({ page }) => {
  await abrir(page);
  await page.keyboard.press(teclaTab(page));
  const pular = page.getByRole("link", { name: "Pular para o conteúdo" });
  await expect(pular).toBeFocused();
  await expect(pular).toBeInViewport();
  await page.keyboard.press("Enter");
  await expect(page.locator("main")).toBeFocused();
  for (let i = 0; i < 6; i++) {
    await page.keyboard.press(teclaTab(page));
    const info = await page.evaluate(() => {
      const e = document.activeElement;
      const s = getComputedStyle(e);
      return { tag: e.tagName, estilo: s.outlineStyle, largura: parseFloat(s.outlineWidth) };
    });
    expect(info.estilo).not.toBe("none");
    expect(info.largura).toBeGreaterThanOrEqual(2);
  }
});

test("o menu abre pelo teclado (Enter) e navega sem mouse", async ({ page }) => {
  test.skip(ehDesktop(page), "menu só existe no celular");
  await abrir(page);
  const botao = page.getByRole("button", { name: "Menu" });
  await botao.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#painel-menu")).toBeVisible();
  await page.keyboard.press(teclaTab(page));
  await expect(page.locator("#painel-menu a").first()).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.locator("#painel-menu")).toBeHidden();
});

test("desktop: navegação horizontal com seis destinos e sem barra inferior", async ({ page }) => {
  test.skip(!ehDesktop(page), "regra do desktop");
  await abrir(page);
  await expect(page.locator(".nav-desktop a")).toHaveCount(6);
  await expect(page.locator(".barra-inferior")).toBeHidden();
  await expect(page.getByRole("button", { name: "Menu" })).toBeHidden();
});
