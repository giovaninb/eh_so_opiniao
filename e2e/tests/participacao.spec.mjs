import { test, expect, abrir, configurarEnvio } from "./fixtures.mjs";

const FRASE = "Quem veio de fora devia ficar quieto sobre o que acontece aqui.";
const campo = (page) => page.getByLabel("Escreva a frase");

async function preencher(page, { texto = FRASE, leitura = "Pode ser desrespeitosa ou discriminatória", consentir = true } = {}) {
  if (texto !== null) await campo(page).fill(texto);
  if (leitura) await page.locator("#form-participar label.escolha").filter({ hasText: leitura }).click();
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
  const corpo = JSON.parse(enviados[0].corpo);
  expect(corpo.texto).toBe(estranho.trim());
  expect(corpo.tipo).toBe("sugestao_frase");
  expect(corpo.schema_version).toBe("3");
  expect(corpo.interpretacao_sugerida).toBe("discriminacao");
  expect(corpo.consentimento).toBe("sim");
  expect(corpo.armadilha).toBe("");
  expect(corpo.turnstile_token).toBeTruthy();
  await expect(page.locator("b")).toHaveCount(0); // nada foi interpretado como HTML
});

test("dados identificáveis são mascarados antes de sair do navegador", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/participar");
  await preencher(page, { texto: "Mande para ana@exemplo.com ou @ana_x, tel (54) 99999-1234, veja https://exemplo.test/p" });
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio .mensagem.ok")).toBeVisible();
  const frase = JSON.parse(enviados[0].corpo).texto;
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
    await expect(page.getByLabel("Pode ser desrespeitosa ou discriminatória")).toBeChecked();
    await expect(page.getByRole("button", { name: "Enviar frase" })).toBeEnabled();
    await page.unroute("**/config_participacao.json");
    await page.unroute("https://api.exemplo.test/api/v1/participacoes");
  }
});

test("campo-armadilha preenchido não envia nada", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/participar");
  await preencher(page);
  await page.locator("#campo-armadilha").evaluate((e) => { e.value = "spam"; });
  await page.getByRole("button", { name: "Enviar frase" }).click();
  expect(enviados).toHaveLength(0);
});

test("preencher os campos só por script, sem digitação, não fala com o serviço", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/participar");
  await page.evaluate((frase) => {
    document.getElementById("campo-frase").value = frase;
    document.querySelector('#form-participar input[name="avaliacao"][value="discriminacao"]').checked = true;
    document.getElementById("campo-consentimento").checked = true;
    document.getElementById("form-participar").requestSubmit();
  }, FRASE);
  await expect(page.locator("#mensagem-envio")).toContainText("Obrigado.");
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

test("responder uma frase não envia nada ao formulário", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/frase/EX-01");
  await page.getByRole("button", { name: "Não vejo problema" }).click();
  expect(enviados).toHaveLength(0);
  await expect(page.getByRole("button", { name: /Contar minha leitura na enquete/ })).toHaveCount(0);
  await page.getByRole("button", { name: "Preciso de mais contexto" }).click();
  expect(enviados).toHaveLength(0);
});

async function concluirDescobrir(page, responder = 5) {
  const respostas = ["Não vejo problema", "Pode ser desrespeitosa ou discriminatória", "Preciso de mais contexto"];
  for (let i = 0; i < 5; i++) {
    const cartao = page.locator("#descobrir-corpo .cartao-frase");
    if (i < responder) {
      await cartao.getByRole("button", { name: respostas[i % 3] }).click();
      await page.getByRole("button", { name: i === 4 ? "Concluir" : "Próxima frase" }).click();
    } else {
      await page.getByRole("button", { name: "Pular" }).click();
    }
  }
}

test("navegar e responder em Descobrir não envia nada até o lote voluntário", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/descobrir");
  await concluirDescobrir(page, 5);
  expect(enviados).toHaveLength(0);
  const lote = page.locator(".contribuicao-lote");
  await expect(lote).toContainText("Contribuir com minhas avaliações");
  await lote.getByRole("button", { name: "Enviar minhas avaliações" }).click();
  await expect(lote.getByText("Marque que você entendeu")).toBeVisible();
  expect(enviados).toHaveLength(0);
});

test("lote voluntário envia até cinco avaliações numa única submissão, com consentimento", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/descobrir");
  await concluirDescobrir(page, 5);
  const lote = page.locator(".contribuicao-lote");
  await lote.getByLabel(/Entendo o que será enviado/).check();
  await lote.getByRole("button", { name: "Enviar minhas avaliações" }).click();
  await expect(lote).toContainText("Contribuição recebida. Obrigado por ajudar a revisar o projeto.");
  expect(enviados).toHaveLength(1);
  const corpo = JSON.parse(enviados[0].corpo);
  expect(corpo.tipo).toBe("avaliacoes");
  expect(corpo.schema_version).toBe("3");
  expect(corpo.consentimento).toBe("sim");
  const itens = corpo.avaliacoes;
  expect(itens.length).toBeLessThanOrEqual(5);
  expect(itens.length).toBeGreaterThan(0);
  expect(itens.every((a) => a.frase_id && a.avaliacao && a.conteudo_versao)).toBeTruthy();
});

test("duplo clique no lote não gera duas submissões", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/descobrir");
  await concluirDescobrir(page, 5);
  const lote = page.locator(".contribuicao-lote");
  await lote.getByLabel(/Entendo o que será enviado/).check();
  await lote.getByRole("button", { name: "Enviar minhas avaliações" }).dblclick();
  await expect(lote).toContainText("Contribuição recebida");
  await expect.poll(() => enviados.length).toBe(1);
});

test("cota mensal do formulário: mensagem clara e texto/lote preservados", async ({ page }) => {
  const enviados = await configurarEnvio(page, "cota");
  await abrir(page, "#/participar");
  await preencher(page);
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio")).toContainText("limite mensal");
  await expect(page.locator("#mensagem-envio")).not.toContainText("Recebido");
  await expect(campo(page)).toHaveValue(FRASE);
  expect(enviados).toHaveLength(1);
});

test("contribuições suspensas não enviam e o site educativo continua", async ({ page }) => {
  const enviados = await configurarEnvio(page, "suspenso");
  await abrir(page, "#/participar");
  await expect(page.locator("#aviso-indisponivel")).toContainText("temporariamente suspensas");
  await expect(campo(page)).toBeDisabled();
  await abrir(page, "#/descobrir");
  await expect(page.locator("#descobrir-corpo .cartao-frase")).toBeVisible();
  await page.getByRole("button", { name: "Não vejo problema" }).click();
  await expect(page.locator(".revelacao")).toBeVisible();
  expect(enviados).toHaveLength(0);
});

test("sugestão de frase inclui contexto opcional e pré-visualização", async ({ page }) => {
  const enviados = await configurarEnvio(page);
  await abrir(page, "#/participar");
  await preencher(page);
  await page.getByLabel("Contexto (opcional)").fill("Pergunta feita a uma pessoa recém-chegada, sem nome.");
  await expect(page.locator("#previsualizacao-envio")).toContainText("sugestão de frase");
  await expect(page.locator("#previsualizacao-envio")).toContainText("Pergunta feita");
  await page.getByRole("button", { name: "Enviar frase" }).click();
  await expect(page.locator("#mensagem-envio .mensagem.ok")).toBeVisible();
  const corpo = JSON.parse(enviados[0].corpo);
  expect(corpo.contexto).toContain("Pergunta feita");
  expect(corpo.tipo).toBe("sugestao_frase");
});
