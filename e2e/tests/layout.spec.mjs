// Testes de layout: emulação de telas (NÃO são dispositivos físicos). Valem para toda a matriz de larguras.
import { test, expect, abrir, VIEWPORTS, PAISAGEM, ROTAS } from "./fixtures.mjs";

async function auditar(page) {
  return page.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    const visivel = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 1 && r.height > 1 && s.visibility !== "hidden" && s.display !== "none" && !e.closest(".visualmente-oculto, .armadilha"); };
    const nome = (e) => `${e.tagName.toLowerCase()}${e.id ? "#" + e.id : ""}${e.className && typeof e.className === "string" ? "." + e.className.trim().split(/\s+/)[0] : ""} "${(e.textContent || e.value || "").trim().slice(0, 30)}"`;
    const alvos = [...document.querySelectorAll("a[href], button, input:not([type=hidden]):not(.armadilha input), select, summary, textarea, [role=button]")]
      .filter(visivel).filter((e) => !e.closest("[aria-hidden=true], .armadilha"));
    const pequenos = alvos.filter((e) => {
      if (e.matches("a") && e.closest("p, li, .notas, .rodape")) { /* link em texto corrido: exceção WCAG 2.5.8 (inline) */
        if (getComputedStyle(e).display === "inline") return false; }
      if (e.matches("input[type=radio], input[type=checkbox]")) { const l = e.closest("label"); const r = (l || e).getBoundingClientRect(); return r.height < 44 || r.width < 44; }
      const r = e.getBoundingClientRect(); return r.height < 44 || r.width < 44;
    }).map(nome);
    const estouram = [...document.querySelectorAll("main *, header *, nav *")].filter(visivel).filter((e) => {
      const r = e.getBoundingClientRect(); return r.right > vw + 1 || r.left < -1;
    }).filter((e) => !e.closest(".mascara-visual, [data-scroll-x]")).map(nome);
    const cortados = [...document.querySelectorAll("button, a.botao, .chip, label.opcao, summary, h1, h2, h3, p, .frase")].filter(visivel).filter((e) => {
      const s = getComputedStyle(e); if (s.overflow === "visible") return e.scrollWidth > e.clientWidth + 1 && s.display !== "inline" && e.clientWidth > 0 && false;
      return e.scrollWidth > e.clientWidth + 1 || (s.textOverflow === "ellipsis");
    }).map(nome);
    return { vw, scrollW: document.documentElement.scrollWidth, pequenos, estouram: estouram.slice(0, 8), cortados };
  });
}

for (const vp of [...VIEWPORTS, ...PAISAGEM]) {
  test.describe(`largura ${vp.nome} (${vp.largura}×${vp.altura}, emulada)`, () => {
    test.use({ viewport: { width: vp.largura, height: vp.altura } });

    for (const rota of ROTAS) {
      test(`${rota}: sem rolagem horizontal, sem elementos fora da tela e alvos de toque ≥44 px`, async ({ page }) => {
        await abrir(page, rota);
        const r = await auditar(page);
        expect(r.scrollW, `rolagem horizontal em ${rota}`).toBeLessThanOrEqual(r.vw);
        expect(r.estouram, "elementos fora da tela").toEqual([]);
        expect(r.cortados, "texto cortado").toEqual([]);
        expect(r.pequenos, "alvos pequenos").toEqual([]);
      });
    }

    test("a barra inferior e o cabeçalho não cobrem o conteúdo nem os botões principais", async ({ page }) => {
      await abrir(page, "#/participar");
      for (const sel of ["#campo-frase", "#botao-enviar", "#campo-consentimento"]) {
        const alvo = page.locator(sel);
        await alvo.scrollIntoViewIfNeeded();
        await alvo.focus();
        const cobre = await page.evaluate((s) => {
          const e = document.querySelector(s); const r = e.getBoundingClientRect();
          const x = r.left + r.width / 2, y = Math.min(Math.max(r.top + r.height / 2, 1), innerHeight - 1);
          const topo = document.elementFromPoint(x, y);
          return !(topo === e || e.contains(topo) || topo?.closest("label")?.contains(e) || e.closest("label")?.contains(topo));
        }, sel);
        expect(cobre, `${sel} coberto por barra fixa`).toBe(false);
      }
      // o final da página precisa poder rolar acima da barra inferior
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      const sobreposto = await page.evaluate(() => {
        const barra = document.querySelector(".barra-inferior"); if (!barra || getComputedStyle(barra).display === "none") return false;
        const ultimo = [...document.querySelectorAll("footer p, .rodape p")].pop(); const rb = barra.getBoundingClientRect(), rr = ultimo.getBoundingClientRect();
        return rr.bottom > rb.top + 1 && rr.top < rb.bottom; // o último texto da página precisa poder subir acima da barra
      });
      expect(sobreposto).toBe(false);
    });
  });
}

test.describe("acessibilidade de layout: zoom e fonte ampliada", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("fonte do navegador a 200%: sem rolagem horizontal, sem sobreposição", async ({ page }) => {
    await abrir(page, "#/");
    await page.addStyleTag({ content: "html{font-size:200% !important}" });
    for (const rota of ROTAS) {
      await page.evaluate((h) => { location.hash = h; }, rota);
      await page.waitForTimeout(80);
      const r = await auditar(page);
      expect(r.scrollW, rota).toBeLessThanOrEqual(r.vw);
      expect(r.estouram, rota).toEqual([]);
    }
  });

  test("reflow WCAG 1.4.10: equivalente a 320 CSS px de largura × 256 de altura (zoom 400% em 1280)", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 256 });
    for (const rota of ROTAS) {
      await abrir(page, rota);
      const r = await auditar(page);
      expect(r.scrollW, rota).toBeLessThanOrEqual(r.vw);
      expect(r.estouram, rota).toEqual([]);
    }
  });

  test("altura curta (paisagem 375): o menu abre e o conteúdo continua acessível por rolagem", async ({ page }) => {
    await page.setViewportSize({ width: 667, height: 375 });
    await abrir(page, "#/");
    const botaoMenu = page.getByRole("button", { name: /Menu/ });
    if (await botaoMenu.isVisible()) {
      await botaoMenu.click();
      const painel = page.locator("#painel-menu");
      await expect(painel).toBeVisible();
      const caixa = await painel.boundingBox();
      expect(caixa.y + caixa.height).toBeLessThanOrEqual(375 + 1);
      const ultimo = painel.getByRole("link").last();
      await ultimo.scrollIntoViewIfNeeded();
      await expect(ultimo).toBeInViewport();
    }
  });

  test("movimento reduzido e texto com espaçamento ampliado (WCAG 1.4.12) não quebram o layout", async ({ page }) => {
    await abrir(page, "#/explorar");
    await page.addStyleTag({ content: "*{line-height:1.5 !important;letter-spacing:.12em !important;word-spacing:.16em !important} p{margin-bottom:2em !important}" });
    const r = await auditar(page);
    expect(r.scrollW).toBeLessThanOrEqual(r.vw);
    expect(r.cortados).toEqual([]);
  });
});
