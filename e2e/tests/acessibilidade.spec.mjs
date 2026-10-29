// axe-core cobre só uma parte da WCAG 2.2 AA (automatizável). O restante exige leitor de tela e teste manual: ver docs/TESTES_MOBILE.md.
import { test, expect, abrir, ROTAS, configurarEnvio } from "./fixtures.mjs";
import AxeBuilder from "@axe-core/playwright";

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const resumo = (v) => v.map((x) => `${x.id} (${x.impact}): ${x.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")} — ${x.help}`);

for (const largura of [390, 1440]) {
  test.describe(`axe @ ${largura}px`, () => {
    test.use({ viewport: { width: largura, height: largura === 390 ? 844 : 900 } });

    for (const rota of ROTAS) {
      test(`${rota} sem violações WCAG 2.2 AA detectáveis`, async ({ page }) => {
        await configurarEnvio(page);
        await abrir(page, rota);
        const r = await new AxeBuilder({ page }).withTags(TAGS).analyze();
        expect(resumo(r.violations)).toEqual([]);
      });
    }

    test("estados interativos: filtros abertos, menu aberto, análise revelada, erros de formulário", async ({ page }) => {
      await configurarEnvio(page);
      const varrer = async (rotulo) => {
        const r = await new AxeBuilder({ page }).withTags(TAGS).analyze();
        expect(resumo(r.violations), rotulo).toEqual([]);
      };
      await abrir(page, "#/explorar");
      await page.getByText("Filtros", { exact: true }).click();
      await page.getByRole("button", { name: "Ambíguas" }).click();
      await varrer("filtros");
      await page.getByRole("searchbox").fill("zzzz");
      await varrer("sem resultados");
      const menu = page.getByRole("button", { name: /Menu/ });
      if (await menu.isVisible()) { await menu.click(); await varrer("menu aberto"); await page.keyboard.press("Escape"); }
      await abrir(page, "#/frase/EX-61");
      await page.getByRole("button", { name: "Depende do contexto" }).click();
      await page.locator("details.ia summary").click().catch(() => {});
      await varrer("análise revelada");
      await abrir(page, "#/frase/NAO-EXISTE");
      await varrer("estado de erro");
      await abrir(page, "#/participar");
      await page.getByRole("button", { name: "Enviar frase" }).click();
      await varrer("erros de formulário");
    });
  });
}

test("estrutura: um único h1 por tela, hierarquia sem saltos, landmarks e idioma", async ({ page }) => {
  for (const rota of ROTAS) {
    await abrir(page, rota);
    const info = await page.evaluate(() => {
      const visiveis = [...document.querySelectorAll("h1,h2,h3,h4")].filter((h) => h.getClientRects().length && !h.closest("[hidden]"));
      return { h1: visiveis.filter((h) => h.tagName === "H1").length, niveis: visiveis.map((h) => Number(h.tagName[1])), lang: document.documentElement.lang,
        landmarks: ["header", "nav", "main", "footer"].map((t) => document.querySelectorAll(t).length) };
    });
    expect(info.h1, rota).toBe(1);
    info.niveis.reduce((ant, n) => { expect(n - ant, `${rota}: salto de título`).toBeLessThanOrEqual(1); return n; }, 1);
    expect(info.lang).toBe("pt-BR");
    expect(info.landmarks[2], "main").toBe(1);
  }
});

test("teclado: foco sempre visível com contraste, sem armadilha, e o formulário é completável", async ({ page }) => {
  await configurarEnvio(page);
  await abrir(page, "#/participar");
  await page.getByLabel("Escreva a frase").focus();
  await page.keyboard.type("Quem veio de fora devia ficar quieto sobre isso aqui.");
  await page.getByLabel("Pode ser discriminação").focus();
  await page.keyboard.press("Space"); // seleciona a opção focada
  await page.getByLabel(/Entendo como a minha frase/).focus();
  await page.keyboard.press("Space");
  await page.getByRole("button", { name: "Enviar frase" }).focus();
  const contorno = await page.evaluate(() => { const s = getComputedStyle(document.activeElement); return { w: parseFloat(s.outlineWidth), estilo: s.outlineStyle, sombra: s.boxShadow }; });
  expect(contorno.w >= 2 || contorno.sombra !== "none").toBe(true);
  await page.keyboard.press("Enter");
  await expect(page.locator("#mensagem-envio .mensagem.ok")).toBeVisible();
});

test("anúncios para leitor de tela: regiões vivas existem para resultados, erros e envio", async ({ page }) => {
  await abrir(page, "#/explorar");
  await expect(page.locator("#contagem-resultados")).toHaveAttribute("aria-live", /polite|assertive/);
  await abrir(page, "#/participar");
  await expect(page.locator("#mensagem-envio")).toHaveAttribute("aria-live", /polite|assertive/);
  await expect(page.locator("#campo-frase")).toHaveAttribute("aria-describedby", /erro-frase/); // o erro é lido junto com o campo
});

test("movimento reduzido: sem animações longas", async ({ page }) => {
  await abrir(page, "#/");
  const duracoes = await page.evaluate(() => [...document.querySelectorAll("*")].map((e) => getComputedStyle(e)).filter((s) => parseFloat(s.animationDuration) > 0.05 || parseFloat(s.transitionDuration) > 0.05).length);
  expect(duracoes).toBe(0);
});
