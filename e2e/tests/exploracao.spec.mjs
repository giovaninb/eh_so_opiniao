import { test, expect, abrir, irPara } from "./fixtures.mjs";

const cartoes = (page) => page.locator("#explorar-lista .item-frase");

test("a biblioteca carrega os casos e pagina progressivamente (12 por vez)", async ({ page }) => {
  await abrir(page, "#/explorar");
  await expect(page.locator("#contagem-resultados")).toHaveText("Mostrando 12 de 592 frases");
  await expect(cartoes(page)).toHaveCount(12);
  await page.getByRole("button", { name: /Mostrar mais \(580 restantes\)/ }).click();
  await expect(cartoes(page)).toHaveCount(24);
  while (await page.getByRole("button", { name: /Mostrar mais/ }).count()) await page.getByRole("button", { name: /Mostrar mais/ }).click();
  await expect(page.locator("#contagem-resultados")).toHaveText("592 frases");
  await expect(page.getByRole("button", { name: /Mostrar mais/ })).toHaveCount(0);
});

test("o cartão da lista mostra só tema, natureza, frase e a ação principal", async ({ page }) => {
  await abrir(page, "#/explorar");
  const primeiro = cartoes(page).first();
  await expect(primeiro.locator(".meta .tema")).not.toBeEmpty();
  await expect(primeiro.locator(".meta .natureza")).toHaveText("Exemplo fictício");
  await expect(primeiro.locator(".frase")).not.toBeEmpty();
  await expect(primeiro.getByRole("link", { name: /Ler e responder/ })).toBeVisible();
  await expect(primeiro.locator(".revelacao, .opcoes")).toHaveCount(0); // sem análise nem três botões na lista
});

test("filtra por tema e por leitura, e limpa os filtros", async ({ page }) => {
  await abrir(page, "#/explorar");
  await page.getByText("Filtros", { exact: true }).click();
  await page.locator("#filtro-tema").selectOption("racismo");
  await expect(page.locator("#contagem-resultados")).toHaveText(/^(Mostrando \d+ de )?\d+ frases?$/);
  const n = await cartoes(page).count();
  expect(n).toBeGreaterThanOrEqual(5);
  for (const t of await cartoes(page).locator(".tema").allTextContents()) expect(t).toBe("Racismo");
  await page.getByRole("button", { name: "Ambíguas" }).click();
  await expect(page.locator("#explorar-lista .estado")).toContainText("Nenhuma frase encontrada"); // racismo não tem ambíguas
  await page.locator("#filtro-tema").selectOption("");
  await expect(cartoes(page).first()).toBeVisible();
  await expect(page.locator("#resumo-filtros")).toContainText("1 ativo");
  await page.getByRole("button", { name: "Limpar filtros" }).first().click();
  await expect(page.locator("#contagem-resultados")).toHaveText("Mostrando 12 de 592 frases");
  await expect(page.locator("#resumo-filtros")).toHaveText("Filtros");
  await expect(page.locator("#limpar-filtros")).toBeHidden();
});

test("filtros de casos ambíguos e de exemplos sem discriminação", async ({ page }) => {
  await abrir(page, "#/explorar");
  await page.getByText("Filtros", { exact: true }).click();
  await page.getByRole("button", { name: "Ambíguas" }).click();
  await expect(page.locator("#contagem-resultados")).toHaveText("Mostrando 12 de 76 frases"); // dados de teste: todas as 592 frases aprovadas pelo revisor fictício
  await page.getByRole("button", { name: "Sem discriminação" }).click();
  const total = Number((await page.locator("#contagem-resultados").textContent()).match(/\d+/g).pop());
  expect(total).toBeGreaterThanOrEqual(15);
});

test("busca ignora acentos e caixa, e mostra o estado sem resultados", async ({ page }) => {
  await abrir(page, "#/explorar");
  await page.getByRole("searchbox", { name: "Buscar nas frases" }).fill("PREGUICOSO");
  await expect(page.locator("#contagem-resultados")).toHaveText("1 frase");
  await expect(cartoes(page).first()).toContainText("preguiçoso");
  await page.getByRole("searchbox").fill("zzzzzz");
  await expect(page.locator("#contagem-resultados")).toHaveText("Nenhuma frase encontrada.");
  const vazio = page.locator("#explorar-lista .estado");
  await expect(vazio).toContainText("Tente outro termo");
  await vazio.getByRole("button", { name: "Limpar filtros" }).click();
  await expect(page.getByRole("searchbox")).toHaveValue("");
  await expect(cartoes(page).first()).toBeVisible();
});

test("busca trata caracteres especiais como texto, sem quebrar nem executar nada", async ({ page }) => {
  await abrir(page, "#/explorar");
  const scriptsInline = await page.locator("script:not([src])").count(); // só o pequeno script do <head>
  for (const termo of ["<script>alert(1)</script>", "(((", "\\", "😀", "%"]) {
    await page.getByRole("searchbox").fill(termo);
    await expect(page.locator("#contagem-resultados")).toHaveText("Nenhuma frase encontrada.");
  }
  await expect(page.locator("script:not([src])")).toHaveCount(scriptsInline); // nenhum <script> novo foi injetado
  await expect(page.locator("#explorar-lista script, #contagem-resultados script")).toHaveCount(0);
});

test("ordenação: mais curtas primeiro", async ({ page }) => {
  await abrir(page, "#/explorar");
  await page.getByText("Filtros", { exact: true }).click();
  await page.locator("#filtro-ordem").selectOption("curtas");
  const tamanhos = (await cartoes(page).locator(".frase").allTextContents()).map((t) => t.length);
  expect([...tamanhos].sort((a, b) => a - b)).toEqual(tamanhos);
});

test("os filtros ficam na URL e podem ser compartilhados", async ({ page }) => {
  await abrir(page, "#/explorar?tema=racismo&tipo=exclusao&q=pessoa");
  await expect(page.locator("#filtro-tema")).toHaveValue("racismo");
  await expect(page.locator("#campo-busca")).toHaveValue("pessoa");
  await expect(page.locator("#filtros")).toHaveJSProperty("open", true);
  await page.locator("#filtro-tema").selectOption("misoginia");
  await expect(page).toHaveURL(/tema=misoginia/);
});

test("avaliar uma frase, revelar a leitura e avançar para a próxima", async ({ page }) => {
  await abrir(page, "#/explorar");
  await cartoes(page).first().getByRole("link", { name: /Ler e responder/ }).click();
  await expect(page).toHaveURL(/#\/frase\/EX-01$/);
  const cartao = page.locator("#frase-corpo .cartao-frase");
  await expect(cartao.locator(".frase")).toHaveText(/Gente do interior/);
  await expect(cartao.locator(".revelacao")).toHaveCount(0); // análise só depois da escolha
  await expect(cartao.getByText("O que você acha desta frase?")).toBeVisible();
  const opcao = cartao.getByRole("button", { name: "Pode ser desrespeitosa ou discriminatória" });
  await opcao.click();
  await expect(opcao).toHaveAttribute("aria-pressed", "true");
  const revelacao = cartao.locator(".revelacao");
  await expect(revelacao).toBeVisible();
  await expect(revelacao.getByRole("heading", { name: "A leitura da revisão" })).toBeFocused();
  await expect(revelacao).toContainText("Você marcou: pode ser desrespeitosa");
  await expect(revelacao).toContainText("Por que essa leitura");
  await expect(revelacao).toContainText("O que poderia mudar a leitura");
  await expect(revelacao).toContainText("Esta frase foi escrita pela equipe");
  await expect(revelacao).not.toContainText(/acertou|errou|parabéns|pontos/i);
  await revelacao.getByRole("button", { name: "Próxima frase" }).click();
  await expect(page).toHaveURL(/#\/frase\/EX-02$/);
  await expect(page.locator("#frase-corpo .revelacao")).toHaveCount(0);
});

test("a análise pode ser lida sem responder", async ({ page }) => {
  await abrir(page, "#/frase/EX-61");
  await page.getByRole("button", { name: "Ver análise sem responder" }).click();
  await expect(page.locator(".revelacao")).toContainText("Você viu a análise sem responder.");
  await expect(page.locator(".revelacao")).toContainText("A leitura depende de um contexto");
});

test("acesso direto por URL a uma frase e a uma frase inexistente", async ({ page }) => {
  await abrir(page, "#/frase/EX-33");
  await expect(page.locator(".cartao-frase .frase")).toContainText("Gente de direita não presta");
  await expect(page).toHaveTitle(/EX-33/);
  await irPara(page, "#/frase/NAO-EXISTE");
  await expect(page.locator("#frase-corpo .estado")).toContainText("Não encontramos essa frase");
  await page.getByRole("button", { name: "Ver a biblioteca" }).click();
  await expect(page).toHaveURL(/#\/explorar/);
});

test("o par espelho recebe a mesma leitura (teste de neutralidade na interface)", async ({ page }) => {
  const leituras = [];
  for (const id of ["EX-32", "EX-33"]) {
    await abrir(page, `#/frase/${id}`);
    await page.getByRole("button", { name: "Ver análise sem responder" }).click();
    leituras.push(await page.locator(".leitura-humana").textContent());
  }
  expect(leituras[0]).toBe(leituras[1]);
});
