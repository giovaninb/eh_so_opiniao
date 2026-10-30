import { test, expect, abrir, configurarEnvioCloudflare } from "./fixtures.mjs";

const FRASE = "Quem veio de fora devia ficar quieto sobre o que acontece aqui.";

async function preencher(page) {
  await page.getByLabel("Escreva a frase").fill(FRASE);
  await page.locator("#form-participar label.escolha").filter({ hasText: "Pode ser desrespeitosa ou discriminatória" }).click();
  await page.getByLabel(/Entendo como a minha frase será tratada/).check();
}

test("sugestão via Cloudflare envia JSON com token e preserva o texto em erro de rede", async ({ page }) => {
  const enviados = await configurarEnvioCloudflare(page);
  await abrir(page, "#/participar");
  await preencher(page);
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio .mensagem.ok")).toBeVisible();
  expect(enviados.length).toBe(1);
  const corpo = JSON.parse(enviados[0].corpo);
  expect(corpo.tipo).toBe("sugestao_frase");
  expect(corpo.schema_version).toBe("3");
  expect(corpo.texto).toBe(FRASE);
  expect(corpo.interpretacao_sugerida).toBe("discriminacao");
  expect(corpo.turnstile_token).toBe("XXXX.DUMMY.TOKEN.XXXX");
  expect(corpo.consentimento).toBe("sim");
  expect(corpo.submission_id).toMatch(/^[0-9a-f-]{36}$/i);
});

test("falha temporária do Worker mantém o texto e permite nova tentativa", async ({ page }) => {
  await configurarEnvioCloudflare(page, "rede");
  await abrir(page, "#/participar");
  await preencher(page);
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio .mensagem.erro")).toContainText("conexão");
  await expect(page.getByLabel("Escreva a frase")).toHaveValue(FRASE);
  await expect(page.getByRole("button", { name: "Enviar frase" })).toBeEnabled();
});

test("serviço indisponível não afirma sucesso", async ({ page }) => {
  await configurarEnvioCloudflare(page, "erro500");
  await abrir(page, "#/participar");
  await preencher(page);
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio .mensagem.erro")).toContainText("indisponível");
  await expect(page.locator("#mensagem-envio .mensagem.ok")).toHaveCount(0);
});
