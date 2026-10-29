import { test, expect, abrir, configurarEnvio } from "./fixtures.mjs";

const FRASE = "Quem veio de fora devia ficar quieto sobre o que acontece aqui.";
const campo = (page) => page.getByLabel("Escreva a frase");

async function preencher(page, { texto = FRASE, leitura = "Pode ser discriminação", consentir = true } = {}) {
  if (texto !== null) await campo(page).fill(texto);
  if (leitura) await page.getByLabel(leitura).check();
  if (consentir) await page.getByLabel(/Entendo como a minha frase será tratada/).check();
}

test("a página começa pelo convite e logo mostra o formulário (sem muralha de avisos)", async ({ page }) => {
  await abrir(page, "#/participar");
  await expect(page.getByRole("heading", { level: 1, name: "Uma frase já fez você pensar?" })).toBeVisible();
  await expect(page.getByText("Compartilhe uma frase ou uma interpretação")).toBeVisible();
  const topoForm = await page.locator("#form-participar").boundingBox();
  const vh = page.viewportSize().height;
  expect(topoForm.y).toBeLessThan(vh * 0.75); // o formulário já aparece na primeira tela
  await expect(page.getByText("Como tratamos a sua contribuição")).toBeVisible();
  await expect(page.locator("details.detalhe")).toHaveJSProperty("open", false); // detalhes expansíveis, mas acessíveis antes do envio
  await expect(page.locator("#privacidade-resumo")).toContainText("endereço de IP"); // o essencial continua visível
});

test("sem serviço configurado, o envio fica indisponível e explica por quê (nada é simulado)", async ({ page }) => {
  await abrir(page, "#/participar");
  await expect(page.locator("#aviso-indisponivel")).toContainText("O envio ainda não está disponível");
  await expect(campo(page)).toBeDisabled();
  await expect(page.getByRole("button", { name: "Enviar frase" })).toBeDisabled();
  const requisicoes = [];
  page.on("request", (r) => { if (r.method() === "POST") requisicoes.push(r.url()); });
  await page.getByRole("button", { name: "Enviar frase" }).click({ force: true }).catch(() => {});
  expect(requisicoes).toEqual([]);
  await expect(page.locator("#mensagem-envio")).toBeEmpty();
});

test("contador de caracteres, aviso de máscara e exemplo do formato", async ({ page }) => {
  await configurarEnvio(page);
  await abrir(page, "#/participar");
  await expect(page.locator("#contador-frase")).toHaveText("0 de 280 caracteres");
  await campo(page).fill("Fale com @maria_x ou veja www.exemplo.com.br");
  await expect(page.locator("#aviso-mascara")).toContainText("link, usuário");
  await expect(page.locator("#contador-frase")).toHaveText(/^\d+ de 280 caracteres$/);
  await expect(page.locator("#dica-frase")).toContainText("Por exemplo");
});

test("validação: comprimento, leitura e consentimento, com mensagens acessíveis e foco no primeiro erro", async ({ page }) => {
  await configurarEnvio(page);
  await abrir(page, "#/participar");
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#erro-frase")).toContainText("Escreva pelo menos 10 caracteres");
  await expect(campo(page)).toHaveAttribute("aria-invalid", "true");
  await expect(campo(page)).toBeFocused();
  await expect(page.locator("#erro-avaliacao")).toContainText("Escolha como você lê");
  await expect(page.locator("#erro-consentimento")).toContainText("Marque que você entendeu");
  await campo(page).fill("x".repeat(300));
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#erro-frase")).toContainText("20 caracteres a mais");
  await expect(campo(page)).toHaveValue("x".repeat(300)); // o texto não some
});

test("caracteres especiais, acentos, emoji e HTML são enviados como texto", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/participar");
  const estranho = 'Ele disse: "<b>sai daqui</b>" & ainda riu 😀 — ação, coração; 100% ñ \\ ';
  await preencher(page, { texto: estranho });
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio .mensagem.ok")).toBeVisible();
  const corpo = new URLSearchParams(enviados[0].corpo);
  expect(corpo.get("frase")).toBe(estranho.trim());
  expect(corpo.get("tipo")).toBe("frase");
  expect(corpo.get("avaliacao")).toBe("discriminacao");
  expect(corpo.get("consentimento")).toBe("sim");
  expect(corpo.get("site")).toBe(""); // campo-armadilha vazio
  await expect(page.locator("b")).toHaveCount(0); // nada foi interpretado como HTML
});

test("dados identificáveis são mascarados antes de sair do navegador", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/participar");
  await preencher(page, { texto: "Mande para ana@exemplo.com ou @ana_x, tel (54) 99999-1234, veja https://exemplo.test/p" });
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio .mensagem.ok")).toBeVisible();
  const frase = new URLSearchParams(enviados[0].corpo).get("frase");
  expect(frase).toBe("Mande para [e-mail] ou [usuário], tel [telefone], veja [link]");
});

test("sucesso só aparece com confirmação real do serviço", async ({ page }) => {
  const enviados = await configurarEnvio(page, "ok");
  await abrir(page, "#/participar");
  await preencher(page);
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio")).toContainText("Recebido. Uma pessoa vai ler antes de qualquer publicação");
  expect(enviados).toHaveLength(1);
  expect(enviados[0].cabecalhos["accept"]).toContain("application/json");
  await expect(campo(page)).toHaveValue(""); // só limpa depois de confirmado
});

test("indisponibilidade do serviço: erro claro, texto preservado e nova tentativa possível", async ({ page }) => {
  for (const comportamento of ["erro500", "recusa", "rede"]) {
    await configurarEnvio(page, comportamento);
    await abrir(page, "#/participar");
    await preencher(page);
    await page.getByRole("button", { name: "Enviar frase" }).click();
    await expect(page.locator("#mensagem-envio .mensagem.erro")).toBeVisible();
    await expect(page.locator("#mensagem-envio")).not.toContainText("Recebido");
    await expect(campo(page)).toHaveValue(FRASE); // erro recuperável não apaga o texto
    await expect(page.getByLabel("Pode ser discriminação")).toBeChecked();
    await expect(page.getByRole("button", { name: "Enviar frase" })).toBeEnabled();
    await page.unroute("**/config_participacao.json");
    await page.unroute("https://formulario.exemplo.test/enviar");
  }
});

test("serviço sem CORS (modo opaca): o site avisa que não consegue confirmar, em vez de dizer 'recebido'", async ({ page }) => {
  await configurarEnvio(page, "opaca");
  await abrir(page, "#/participar");
  await preencher(page);
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio .mensagem.aviso")).toContainText("não permite confirmar o recebimento");
  await expect(page.locator("#mensagem-envio")).not.toContainText("Recebido");
});

test("campo-armadilha preenchido não envia nada", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/participar");
  await preencher(page);
  await page.locator("#campo-armadilha").evaluate((e) => { e.value = "spam"; });
  await page.getByRole("button", { name: "Enviar frase" }).click();
  expect(enviados).toHaveLength(0);
});

test("limite de envios por visita", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/participar");
  for (let i = 0; i < 3; i++) {
    await preencher(page, { texto: `${FRASE} Variação ${i}.` });
    await page.getByRole("button", { name: "Enviar frase" }).click();
    await expect.poll(() => enviados.length).toBe(i + 1); // espera o envio terminar antes de preencher de novo
    await expect(page.getByRole("button", { name: "Enviar frase" })).toBeEnabled();
  }
  await preencher(page);
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio")).toContainText("máximo de frases");
  expect(enviados).toHaveLength(3);
});

test("voto na enquete só é enviado por ação explícita e com confirmação", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/frase/EX-01");
  await page.getByRole("button", { name: "É só opinião" }).click();
  expect(enviados).toHaveLength(0); // responder não envia nada
  await page.getByRole("button", { name: /Contar minha leitura na enquete/ }).click();
  await expect(page.locator(".enquete")).toContainText("Leitura enviada (é só opinião)");
  const corpo = new URLSearchParams(enviados[0].corpo);
  expect(Object.fromEntries(corpo)).toEqual({ tipo: "voto", frase_id: "EX-01", avaliacao: "opiniao", consentimento: "sim" });
});
