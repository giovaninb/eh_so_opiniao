import { test, expect, abrir } from "./fixtures.mjs";

test("sessão de cinco frases com progresso discreto e sem pontuação", async ({ page }) => {
  await abrir(page, "#/descobrir");
  const progresso = page.locator(".progresso");
  await expect(progresso).toContainText("1 de 5");
  const cartao = page.locator("#descobrir-corpo .cartao-frase");
  await expect(cartao.getByText("O que você acha desta frase?")).toBeVisible();
  await expect(cartao.locator(".revelacao")).toHaveCount(0);
  await cartao.getByRole("button", { name: "Não vejo problema" }).click();
  await expect(cartao.locator(".revelacao")).toBeVisible();
  await expect(page.locator("#descobrir-corpo")).not.toContainText(/pontos|ranking|acertou|errou|nota:/i);
  await cartao.getByRole("button", { name: "Próxima frase" }).click();
  await expect(progresso).toContainText("2 de 5");
  await expect(page.locator("#descobrir-corpo .cartao-frase")).toBeFocused();
});

test("é possível pular, e ninguém é obrigado a votar para ler a análise", async ({ page }) => {
  await abrir(page, "#/descobrir");
  await page.getByRole("button", { name: "Pular" }).click();
  await expect(page.locator(".progresso")).toContainText("2 de 5");
  await page.getByRole("button", { name: "Ver análise sem responder" }).click();
  await expect(page.locator(".revelacao")).toContainText("Você viu a análise sem responder.");
});

test("fim da sequência: resumo neutro e caminhos para continuar", async ({ page }) => {
  await abrir(page, "#/descobrir");
  const respostas = ["Não vejo problema", "Pode ser desrespeitosa ou discriminatória", "Preciso de mais contexto"];
  for (let i = 0; i < 5; i++) {
    if (i < 3) {
      await page.locator("#descobrir-corpo .cartao-frase").getByRole("button", { name: respostas[i] }).click();
      await page.getByRole("button", { name: i === 4 ? "Concluir" : "Próxima frase" }).click();
    } else {
      await page.getByRole("button", { name: "Pular" }).click();
    }
  }
  const fim = page.locator(".fim-sessao");
  await expect(fim).toContainText("Você leu 5 frases");
  await expect(fim).toContainText("2 puladas");
  await expect(fim).toContainText("Isso não é uma nota");
  await expect(fim.getByRole("link", { name: "Explorar a biblioteca" })).toBeVisible();
  await expect(fim.getByRole("link", { name: "Participar com uma frase" })).toBeVisible();
  await fim.getByRole("button", { name: "Mais cinco frases" }).click();
  await expect(page.locator(".progresso")).toContainText("1 de 5");
});

test("a sequência mistura casos e não é só de exclusão", async ({ page }) => {
  const tipos = new Set();
  for (let semente = 1; semente <= 6; semente++) {
    await abrir(page, "#/descobrir", { semente });
    for (let i = 0; i < 5; i++) {
      await page.getByRole("button", { name: "Ver análise sem responder" }).click();
      tipos.add(await page.locator(".leitura-humana").getAttribute("class"));
      const botao = page.getByRole("button", { name: /Próxima frase|Concluir/ });
      if (await botao.count()) await botao.click();
    }
  }
  expect(tipos.size).toBeGreaterThanOrEqual(3);
});

test("a primeira interação da home convida à reflexão, sem dizer quem acertou", async ({ page }) => {
  await abrir(page, "#/");
  const cartao = page.locator("#primeira-interacao .cartao-frase");
  await expect(cartao.getByText("O que você acha desta frase?")).toBeVisible();
  await expect(cartao.getByRole("button", { name: "Não vejo problema" })).toBeVisible();
  await expect(cartao.getByRole("button", { name: "Pode ser desrespeitosa ou discriminatória" })).toBeVisible();
  await expect(cartao.getByRole("button", { name: "Preciso de mais contexto" })).toBeVisible();
  await cartao.getByRole("button", { name: "Preciso de mais contexto" }).click();
  await expect(cartao.locator(".revelacao")).toContainText("A leitura da revisão pode ser diferente, e isso faz parte da discussão");
  await expect(cartao.locator(".revelacao")).not.toContainText(/acertou|errou/i);
});
