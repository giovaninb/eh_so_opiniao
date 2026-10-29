// Regressão visual. As referências (baselines) ficam versionadas em tests/__baselines__ e são específicas da plataforma
// em que foram geradas (fontes do sistema): hoje, macOS. Atualize só com revisão humana: `npm run visual:atualizar`.
// Os dados são os da biblioteca de TESTE, com semente e relógio fixos.
import { test, expect, abrir, configurarEnvio } from "./fixtures.mjs";

const LARGURAS = [
  { nome: "360", largura: 360, altura: 740, movel: true },
  { nome: "390", largura: 390, altura: 844, movel: true },
  { nome: "430", largura: 430, altura: 932, movel: true },
  { nome: "768", largura: 768, altura: 1024, movel: true },
  { nome: "1440", largura: 1440, altura: 900, movel: false },
];

/* Página inteira: a barra inferior fixa é escondida só aqui, porque numa captura de página inteira ela apareceria
   no meio do conteúdo (artefato da captura). A barra real é validada nas capturas da primeira tela (`dobra`). */
async function foto(page, nome, opcoes = {}) {
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({ content: ".barra-inferior{visibility:hidden !important}" });
  await expect(page).toHaveScreenshot(`${nome}.png`, { fullPage: true, ...opcoes });
}
async function dobra(page, nome) {
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect(page).toHaveScreenshot(`${nome}.png`);
}

for (const v of LARGURAS) {
  test.describe(`visual ${v.nome}`, () => {
    test.use({ viewport: { width: v.largura, height: v.altura } });

    test("home", async ({ page }) => {
      await abrir(page, "#/");
      await dobra(page, `home-dobra-${v.nome}`);
      await foto(page, `home-${v.nome}`);
    });

    test("menu aberto (celular e tablet)", async ({ page }) => {
      test.skip(!v.movel || v.largura >= 1024, "o menu em painel só existe abaixo de 960 px");
      await abrir(page, "#/");
      await page.getByRole("button", { name: /Menu/ }).click();
      await expect(page.locator("#painel-menu")).toBeVisible();
      await expect(page).toHaveScreenshot(`menu-aberto-${v.nome}.png`);
    });

    test("biblioteca com filtros", async ({ page }) => {
      await abrir(page, "#/explorar");
      await page.getByText("Filtros", { exact: true }).click();
      await page.locator("#filtro-tema").selectOption("racismo");
      await page.getByRole("button", { name: "Discriminação", exact: true }).click();
      await foto(page, `biblioteca-filtros-${v.nome}`);
    });

    test("cartão antes de responder", async ({ page }) => {
      await abrir(page, "#/frase/EX-61");
      await foto(page, `cartao-antes-${v.nome}`);
    });

    test("cartão depois de responder", async ({ page }) => {
      await abrir(page, "#/frase/EX-61");
      await page.getByRole("button", { name: "Depende do contexto" }).click();
      await page.locator(".revelacao").waitFor();
      await dobra(page, `cartao-depois-dobra-${v.nome}`);
      await foto(page, `cartao-depois-${v.nome}`);
    });

    test("análise revelada, com a sugestão automática aberta", async ({ page }) => {
      await abrir(page, "#/frase/EX-01");
      await page.getByRole("button", { name: "Ver análise sem responder" }).click();
      await page.locator("details.ia summary").click();
      await foto(page, `analise-${v.nome}`);
    });

    test("duas frases, uma diferença (revelada)", async ({ page }) => {
      await abrir(page, "#/comparar/p-03");
      await page.getByRole("button", { name: "Ver o que muda" }).click();
      await foto(page, `comparacao-${v.nome}`);
    });

    test("cartão de imagem gerado", async ({ page }) => {
      await abrir(page, "#/frase/EX-01");
      await page.locator("details.imagem-cartao summary").click();
      await page.getByRole("button", { name: /Stories e Status/ }).click();
      await page.locator("img.previa-stories").waitFor();
      await foto(page, `imagem-stories-${v.nome}`);
    });

    test("formulário de participação (envio indisponível, estado padrão)", async ({ page }) => {
      await abrir(page, "#/participar");
      await foto(page, `formulario-indisponivel-${v.nome}`);
    });

    test("formulário com serviço (simulado) e erros de validação", async ({ page }) => {
      await configurarEnvio(page);
      await abrir(page, "#/participar");
      await page.getByLabel("Escreva a frase").fill("curto");
      await page.getByRole("button", { name: "Enviar frase" }).click();
      await expect(page.locator("#erro-frase")).toBeVisible();
      await foto(page, `formulario-erros-${v.nome}`);
    });

    test("erro do serviço preserva o texto", async ({ page }) => {
      await configurarEnvio(page, "erro500");
      await abrir(page, "#/participar");
      await page.getByLabel("Escreva a frase").fill("Quem veio de fora devia ficar quieto sobre isso.");
      await page.getByLabel("Pode ser discriminação").check();
      await page.getByLabel(/Entendo como a minha frase/).check();
      await page.getByRole("button", { name: "Enviar frase" }).click();
      await expect(page.locator("#mensagem-envio .mensagem.erro")).toBeVisible();
      await foto(page, `formulario-erro-servico-${v.nome}`);
    });

    test("estado vazio da busca", async ({ page }) => {
      await abrir(page, "#/explorar");
      await page.getByRole("searchbox").fill("zzzzzz");
      await expect(page.locator("#explorar-lista .estado")).toBeVisible();
      await foto(page, `vazio-${v.nome}`);
    });

    test("estado de frase inexistente", async ({ page }) => {
      await abrir(page, "#/frase/NAO-EXISTE");
      await foto(page, `erro-frase-${v.nome}`);
    });
  });
}
