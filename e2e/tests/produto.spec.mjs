// Home, comparações, cartões de imagem, páginas estáticas de caso e matriz de larguras das novas telas.
import { test, expect, abrir, VIEWPORTS, configurarEnvio, ENDPOINT_TESTE } from "./fixtures.mjs";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";

const ehDesktop = (page) => (page.viewportSize()?.width ?? 0) >= 1000;
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

test.describe("home", () => {
  test("hierarquia: apresentação → primeira interação → outras formas → assuntos → participação", async ({ page }) => {
    await abrir(page, "#/");
    await expect(page.getByRole("heading", { level: 1, name: "É Só Opinião?" })).toBeVisible();
    await expect(page.locator("#v-inicio .sub")).toHaveText("Onde termina a opinião e começa a discriminação?");
    await expect(page.locator("#v-inicio .lead")).toHaveText("Existem frases que ouvimos a vida inteira sem questionar. Algumas criticam ideias. Outras podem reforçar estereótipos ou excluir pessoas. O contexto faz diferença.");
    await expect(page.getByRole("link", { name: "Explore uma frase" })).toHaveAttribute("href", "#/descobrir");
    await expect(page.getByRole("link", { name: "Entenda o projeto" })).toHaveAttribute("href", "#/entender");
    const ordem = await page.evaluate(() => {
      const pos = (sel) => document.querySelector(sel)?.getBoundingClientRect().top ?? Infinity;
      return [pos("#v-inicio .hero"), pos("#primeira-interacao"), pos("#secao-assuntos"), pos("#v-inicio .atalhos")];
    });
    expect([...ordem].sort((a, b) => a - b)).toEqual(ordem);
  });

  test("a primeira interação aparece já na primeira tela rolada do celular, sem pontuação", async ({ page }) => {
    test.skip(ehDesktop(page), "regra pensada para o celular");
    await abrir(page, "#/");
    await expect(page.locator("#primeira-interacao .frase")).toBeVisible();
    const topo = await page.locator("#primeira-interacao").evaluate((e) => e.getBoundingClientRect().top);
    expect(topo).toBeLessThan(900);
    await expect(page.locator("#v-inicio")).not.toContainText(/pontos|ranking|acertou|errou/i);
  });

  test("assuntos levam a cinco frases do assunto, com progresso \"1 de 5 situações\"", async ({ page }) => {
    await abrir(page, "#/");
    const chip = page.locator("#chips-assuntos a").first();
    const nome = await chip.textContent();
    expect(await page.locator("#chips-assuntos a").count()).toBeGreaterThanOrEqual(6);
    await chip.click();
    await expect(page).toHaveURL(/#\/descobrir\?tema=/);
    await expect(page.locator(".progresso")).toContainText("1 de 5 situações");
    await expect(page.locator("#v-descobrir")).toContainText(nome.trim());
    await expect(page.getByRole("button", { name: /Pular/ })).toBeVisible();
  });
});

test.describe("duas frases, uma diferença", () => {
  test("há atalho na home e no menu quando existem comparações revisadas", async ({ page }) => {
    await abrir(page, "#/");
    await expect(page.locator("#atalho-comparar")).toBeVisible();
    await page.locator("#atalho-comparar").click();
    await expect(page).toHaveURL(/#\/comparar$/);
    await expect(page.getByRole("heading", { level: 1, name: "Duas frases, uma diferença" })).toBeVisible();
    expect(await page.locator(".lista-pares a").count()).toBe(13);
  });

  test("cada comparação tem URL própria, mostra as duas frases e só revela a diferença sob demanda", async ({ page }) => {
    await abrir(page, "#/comparar/p-03");
    await expect(page).toHaveURL(/#\/comparar\/p-03$/);
    await expect(page.locator(".carta-par")).toHaveCount(2);
    await expect(page.locator(".carta-par .frase").first()).toContainText(/gosto de morar no interior/i);
    await expect(page.locator(".revelacao")).toHaveCount(0);
    await expect(page.locator(".carta-par details[open]")).toHaveCount(0);
    await page.getByRole("button", { name: "Ver o que muda" }).click();
    await expect(page.locator(".revelacao")).toContainText("Limite desta comparação");
    await expect(page.getByRole("button", { name: "Ver o que muda" })).toBeHidden();
    await expect(page.locator("#v-comparar")).not.toContainText(/certo|errado|pontos|nota/i);
  });

  test("layout: lado a lado quando há espaço, empilhadas no celular", async ({ page }) => {
    await abrir(page, "#/comparar/p-03");
    const [a, b] = await page.locator(".carta-par").evaluateAll((els) => els.map((e) => e.getBoundingClientRect()));
    if (ehDesktop(page)) { expect(Math.abs(a.top - b.top)).toBeLessThan(4); expect(b.left).toBeGreaterThan(a.right - 1); }
    else { expect(b.top).toBeGreaterThanOrEqual(a.bottom - 1); expect(Math.abs(a.left - b.left)).toBeLessThan(4); }
  });

  test("compartilhar a comparação usa o link estável e a mensagem em tom de pergunta", async ({ page }) => {
    await abrir(page, "#/comparar/p-03");
    const href = await page.locator("section.compartilhar").getByRole("link", { name: /WhatsApp/ }).getAttribute("href");
    const m = decodeURIComponent(href.split("text=")[1]);
    expect(m).toMatch(/O que muda de uma para a outra\?/);
    expect(m).toMatch(/\/comparar\/p-03\/$/);
  });

  test("comparação inexistente mostra estado de erro útil, sem quebrar", async ({ page }) => {
    await abrir(page, "#/comparar/nao-existe");
    await expect(page.getByText("Não encontramos essa comparação")).toBeVisible();
    await page.getByRole("button", { name: "Ver as comparações" }).click();
    await expect(page).toHaveURL(/#\/comparar$/);
  });

  test("sem comparações revisadas o atalho some e a rota explica por quê", async ({ page }) => {
    await page.route("**/data/pares.json", (r) => r.fulfill({ status: 200, contentType: "application/json", body: '{"pares":[]}' }));
    await abrir(page, "#/");
    await expect(page.locator("#atalho-comparar")).toBeHidden();
    await abrir(page, "#/comparar");
    await expect(page.getByText("Ainda não há comparações revisadas")).toBeVisible();
  });

  test("um par que aponta para frase não publicada é ignorado no navegador", async ({ page }) => {
    await page.route("**/data/pares.json", (r) => r.fulfill({ status: 200, contentType: "application/json",
      body: JSON.stringify({ pares: [{ id: "P-99", slug: "p-99", titulo: "X", a: "EX-01", b: "ZZ-404", diferenca: "d", limite: "l" }] }) }));
    await abrir(page, "#/comparar");
    await expect(page.getByText("Ainda não há comparações revisadas")).toBeVisible();
  });
});

test.describe("imagem para Status e Stories", () => {
  async function gerar(page, id, botao) {
    await abrir(page, `#/frase/${id}`);
    if (!(await page.locator("details.imagem-cartao[open]").count())) await page.locator("details.imagem-cartao summary").click();
    await page.getByRole("button", { name: botao }).click();
    const classe = String(botao).includes("Prévia") ? ".previa-previa" : ".previa-stories";
    await expect(page.locator(`.imagem-resultado img${classe}`)).toBeVisible();
    return page.locator(`.imagem-resultado img${classe}`);
  }

  test("Stories 1080×1920 e prévia 1200×630, com alternativa textual, salvas no aparelho", async ({ page }) => {
    const dim = (img) => img.evaluate((i) => i.complete ? [i.naturalWidth, i.naturalHeight] : new Promise((ok) => { i.onload = () => ok([i.naturalWidth, i.naturalHeight]); }));
    let img = await gerar(page, "EX-01", /Stories e Status/);
    expect(await dim(img)).toEqual([1080, 1920]);
    await expect(img).toHaveAttribute("alt", /Gente do interior é tudo atrasada/);
    const [download] = await Promise.all([page.waitForEvent("download"), page.getByRole("link", { name: "Salvar imagem" }).click()]);
    expect(download.suggestedFilename()).toBe("eh-so-opiniao-ex-01-stories.png");
    const bytes = readFileSync(await download.path());
    expect(bytes.subarray(1, 4).toString()).toBe("PNG");
    expect(bytes.readUInt32BE(16)).toBe(1080);
    expect(bytes.readUInt32BE(20)).toBe(1920);
    img = await gerar(page, "EX-01", /Prévia para redes/);
    expect(await dim(img)).toEqual([1200, 630]);
  });

  test("frase com aviso de conteúdo não é desenhada na imagem", async ({ page }) => {
    const img = await gerar(page, "NX-326", /Stories e Status/);
    const alt = await img.getAttribute("alt");
    expect(alt).not.toMatch(/macumba/i);
    expect(alt).toMatch(/aviso de conteúdo/);
  });

  test("com compartilhamento de arquivos disponível, oferece Compartilhar imagem; sem ele, só salvar", async ({ page }) => {
    await page.addInitScript(() => { window.__arq = null; navigator.canShare = (d) => !!(d && d.files && d.files.length); navigator.share = async (d) => { window.__arq = d.files[0].name; }; });
    await gerar(page, "EX-01", /Stories e Status/);
    await page.getByRole("button", { name: "Compartilhar imagem" }).click();
    expect(await page.evaluate(() => window.__arq)).toBe("eh-so-opiniao-ex-01-stories.png");
  });

  test("sem canShare só aparece Salvar imagem", async ({ page }) => {
    await page.addInitScript(() => { Object.defineProperty(navigator, "canShare", { value: undefined, configurable: true }); });
    await gerar(page, "EX-01", /Stories e Status/);
    await expect(page.getByRole("button", { name: "Compartilhar imagem" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Salvar imagem" })).toBeVisible();
  });

  test("a geração da imagem não faz nenhuma requisição externa", async ({ page }) => {
    const externas = [];
    page.on("request", (r) => { const u = new URL(r.url()); if (u.protocol.startsWith("http") && !["localhost", "127.0.0.1"].includes(u.hostname)) externas.push(r.url()); });
    await gerar(page, "EX-01", /Stories e Status/);
    expect(externas).toEqual([]);
  });
});

test.describe("páginas estáticas de caso (dados reais publicados)", () => {
  test.use({ dados: "real" });

  test("a página tem título, descrição, canonical e Open Graph e o conteúdo está legível sem JavaScript", async ({ browser, baseURL }) => {
    const ctx = await browser.newContext({ javaScriptEnabled: false, baseURL });
    const page = await ctx.newPage();
    await page.goto("/casos/ex-01/");
    await expect(page).toHaveTitle("Frase EX-01: opinião ou discriminação? — É Só Opinião?");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator("p.frase")).toContainText("Gente do interior é tudo atrasada");
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", "https://giovaninb.github.io/eh_so_opiniao/casos/ex-01/");
    await expect(page.locator('meta[property="og:image"]')).toHaveAttribute("content", /\/og\/padrao\.png$/);
    await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute("content", "summary_large_image");
    await expect(page.getByRole("link", { name: /interativ|Responder|Abrir/ }).first()).toHaveAttribute("href", /#\/frase\/EX-01$/);
    await ctx.close();
  });

  test("com JavaScript, o visitante é levado à experiência interativa da mesma frase", async ({ page }) => {
    await page.goto("/casos/ex-01/");
    await page.waitForURL(/#\/frase\/EX-01$/);
    await page.waitForFunction(() => document.documentElement.dataset.pronto === "true");
    await expect(page.locator(".cartao-frase .frase")).toContainText("Gente do interior");
  });

  test("a imagem padrão de prévia existe e tem 1200×630", async ({ request }) => {
    const r = await request.get("/og/padrao.png");
    expect(r.ok()).toBeTruthy();
    const b = await r.body();
    expect([b.readUInt32BE(16), b.readUInt32BE(20)]).toEqual([1200, 630]);
  });

  test("o sitemap lista só casos publicados e o robots aponta para ele", async ({ request }) => {
    const sm = await (await request.get("/sitemap.xml")).text();
    const ids = (await (await request.get("/data/frases.json")).json()).frases.map((f) => f.id.toLowerCase());
    const urls = [...sm.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
    expect(urls.length).toBe(ids.length + 1);
    for (const u of urls.slice(1)) expect(ids).toContain(u.replace(/\/$/, "").split("/").pop());
    expect(await (await request.get("/robots.txt")).text()).toContain("Sitemap:");
  });

  test("caso que não foi publicado (pendente, rejeitado ou ambíguo sem permissão) não tem página: 404, nunca conteúdo", async ({ request }) => {
    const publicados = new Set((await (await request.get("/data/frases.json")).json()).frases.map((f) => f.id));
    const todos = JSON.parse(readFileSync(new URL("../.dados/frases.json", import.meta.url))).frases.map((f) => f.id);
    const fora = todos.filter((id) => !publicados.has(id));
    expect(fora.length).toBeGreaterThan(0);
    for (const id of fora.slice(0, 25)) expect((await request.get(`/casos/${id.toLowerCase()}/`)).status(), id).toBe(404);
    const frases = (await (await request.get("/data/frases.json")).json()).frases;
    for (const f of frases) expect(["Aprovado", "Corrigido", "Ambíguo"], f.id).toContain(f.revisao.estado); // nada sem decisão humana
  });

  test("dados públicos não vazam revisor, corpus, rótulos humanos nem feedback", async ({ request }) => {
    // frases.json e pares.json são os arquivos por caso: nada de corpus, anotadores ou revisão interna
    for (const arq of ["frases.json", "pares.json"]) {
      const t = (await (await request.get(`/data/${arq}`)).text()).toLowerCase();
      for (const proibido of ["hatebr", "told", "origem_original", "rotulos_humanos", "fixture-e2e", "feedback", "revisor", "anotador"]) expect(t, `${arq}: ${proibido}`).not.toContain(proibido);
    }
  });
});

test.describe("matriz de larguras das telas novas", () => {
  for (const v of VIEWPORTS) {
    test(`${v.nome}px: home, comparação e frase sem rolagem horizontal e com alvos de toque ≥ 44px`, async ({ page }) => {
      await page.setViewportSize({ width: v.largura, height: v.altura });
      for (const rota of ["#/", "#/comparar", "#/comparar/p-03", "#/frase/EX-61", "#/descobrir?tema=pessoas_lgbt"]) {
        await abrir(page, rota);
        const sobra = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
        expect(sobra, `${rota} @${v.nome}`).toBeLessThanOrEqual(0);
        for (const alvo of await page.locator("main:visible .botao:visible, main:visible .chip:visible").all()) {
          const c = await alvo.boundingBox();
          expect(c.height, `${rota} @${v.nome}`).toBeGreaterThanOrEqual(43.5);
        }
      }
    });
  }

  for (const largura of [390, 1440]) {
    test(`axe @ ${largura}px: comparação revelada e imagem gerada`, async ({ page }) => {
      await page.setViewportSize({ width: largura, height: 900 });
      await abrir(page, "#/comparar/p-03");
      await page.locator(".carta-par details summary").first().click();
      await page.getByRole("button", { name: "Ver o que muda" }).click();
      await page.evaluate(() => window.scrollTo(0, 0)); // o cabeçalho fixo cobriria parcialmente alvos rolados para baixo dele
      let r = await new AxeBuilder({ page }).withTags(TAGS).analyze();
      expect(r.violations.map((x) => x.id + ": " + x.nodes.map((n) => n.target.join(" ")).join(" | "))).toEqual([]);
      await abrir(page, "#/frase/EX-01");
      await page.locator("details.imagem-cartao summary").click();
      await page.getByRole("button", { name: /Stories e Status/ }).click();
      await expect(page.locator(".imagem-resultado img")).toBeVisible();
      r = await new AxeBuilder({ page }).withTags(TAGS).analyze();
      expect(r.violations.map((x) => x.id + ": " + x.nodes.map((n) => n.target.join(" ")).join(" | "))).toEqual([]);
      await abrir(page, "#/");
      r = await new AxeBuilder({ page }).withTags(TAGS).analyze();
      expect(r.violations.map((x) => x.id + ": " + x.nodes.map((n) => n.target.join(" ")).join(" | "))).toEqual([]);
    });
  }
});

test.describe("Discordo da interpretação (canal privado e real)", () => {
  async function aberto(page, comportamento = "ok") {
    const enviados = await configurarEnvio(page, comportamento);
    await abrir(page, "#/frase/EX-01");
    await page.getByRole("button", { name: "Ver análise sem responder" }).click();
    await page.locator("details.discordo summary").click();
    return enviados;
  }

  test("sem serviço de recebimento configurado, o recurso nem aparece (nada de botão que só finge enviar)", async ({ page }) => {
    await abrir(page, "#/frase/EX-01");
    await page.getByRole("button", { name: "Ver análise sem responder" }).click();
    await expect(page.locator(".revelacao")).toBeVisible();
    await expect(page.getByText("Discordo da interpretação")).toHaveCount(0);
  });

  test("envia ao serviço privado com tipo, id da frase e texto mascarado, e só depois do consentimento", async ({ page }) => {
    const enviados = await aberto(page);
    await page.getByLabel("O que você leria diferente?").fill("Eu leria como crítica. Ligue para 11 98765-4321 ou escreva a maria@exemplo.com");
    await page.getByRole("button", { name: "Enviar para revisão" }).click();
    await expect(page.getByText("Marque a confirmação para enviar.")).toBeVisible();
    expect(enviados).toHaveLength(0);
    await page.getByLabel(/Entendo que o texto vai para um formulário privado/).check();
    await page.getByRole("button", { name: "Enviar para revisão" }).click();
    await expect(page.getByText(/Recebido\. Uma pessoa vai ler/)).toBeVisible();
    expect(enviados).toHaveLength(1);
    const corpo = new URLSearchParams(enviados[0].corpo);
    expect(corpo.get("tipo")).toBe("discordancia");
    expect(corpo.get("frase_id")).toBe("EX-01");
    expect(corpo.get("frase")).toContain("[telefone]");
    expect(corpo.get("frase")).toContain("[e-mail]");
    expect(corpo.get("frase")).not.toMatch(/98765|maria@/);
    expect(corpo.get("consentimento")).toBe("sim");
  });

  test("erro do serviço mantém o texto e não diz que enviou", async ({ page }) => {
    const enviados = await aberto(page, "erro500");
    await page.getByLabel("O que você leria diferente?").fill("Eu leria de outro modo.");
    await page.getByLabel(/Entendo que o texto/).check();
    await page.getByRole("button", { name: "Enviar para revisão" }).click();
    await expect(page.getByText(/O serviço recusou o envio/)).toBeVisible();
    await expect(page.getByLabel("O que você leria diferente?")).toHaveValue("Eu leria de outro modo.");
    await expect(page.getByText(/Recebido/)).toHaveCount(0);
    expect(enviados).toHaveLength(1);
  });

  test("modo sem confirmação (resposta opaca) avisa que não dá para garantir o recebimento", async ({ page }) => {
    await aberto(page, "opaca");
    await page.getByLabel(/Entendo que o texto/).check();
    await page.getByRole("button", { name: "Enviar para revisão" }).click();
    await expect(page.getByText(/não permite confirmar o recebimento/)).toBeVisible();
  });

  test("a única requisição externa é ao serviço configurado (nunca issue pública do GitHub)", async ({ page }) => {
    const externas = [];
    page.on("request", (r) => { const u = new URL(r.url()); if (u.protocol.startsWith("http") && !["localhost", "127.0.0.1"].includes(u.hostname)) externas.push(r.url()); });
    await aberto(page);
    await page.getByLabel(/Entendo que o texto/).check();
    await page.getByRole("button", { name: "Enviar para revisão" }).click();
    await expect(page.getByText(/Recebido/)).toBeVisible();
    expect(externas).toEqual([ENDPOINT_TESTE]);
  });

  test("a armadilha preenchida não gera envio", async ({ page }) => {
    const enviados = await aberto(page);
    await page.locator("details.discordo .armadilha input").evaluate((e) => { e.value = "robô"; });
    await page.getByLabel(/Entendo que o texto/).check();
    await page.getByRole("button", { name: "Enviar para revisão" }).click();
    expect(enviados).toHaveLength(0);
  });
});
