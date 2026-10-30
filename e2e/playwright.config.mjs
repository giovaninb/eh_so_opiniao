import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

// Navegadores ficam em e2e/.browsers (instalados com `npx playwright install`), fora do Git.
process.env.PLAYWRIGHT_BROWSERS_PATH = process.env.ESO_BROWSERS_PATH || join(fileURLToPath(new URL(".", import.meta.url)), ".browsers");

const PORTA = 4173;
const base = `http://127.0.0.1:${PORTA}`;
const funcionais = /(navegacao|exploracao|descoberta|expansao|participacao|compartilhar|conteudo|layout|acessibilidade|produto|assuntos)\.spec\.mjs/;

/* EMULAÇÃO NÃO É DISPOSITIVO FÍSICO: estes projetos simulam tela, toque e user agent. Não reproduzem teclado virtual real,
   rolagem com inércia, barras dinâmicas do navegador, fontes do sistema nem leitores de tela. Veja docs/TESTES_MOBILE.md. */
export default defineConfig({
  testDir: "./tests",
  timeout: 45_000,
  expect: { timeout: 7_000, toHaveScreenshot: { maxDiffPixelRatio: 0.012, animations: "disabled" } },
  fullyParallel: true,
  retries: 0,
  reporter: [["list"], ["json", { outputFile: "resultados/ultimo-relatorio.json" }], ["html", { open: "never" }]],
  snapshotPathTemplate: "{testDir}/__baselines__/{testFilePath}/{arg}-{projectName}-{platform}{ext}",
  webServer: { command: `node servidor.mjs ${PORTA}`, url: base, reuseExistingServer: false, timeout: 20_000 },
  use: { baseURL: base, locale: "pt-BR", timezoneId: "America/Sao_Paulo", reducedMotion: "reduce", trace: "retain-on-failure" },
  projects: [
    { name: "chromium-movel", testMatch: funcionais, use: { ...devices["Pixel 7"] } },
    { name: "webkit-movel", testMatch: funcionais, use: { ...devices["iPhone 13"] } },
    { name: "firefox-movel", testMatch: funcionais, use: { browserName: "firefox", viewport: { width: 390, height: 844 }, hasTouch: false } },
    { name: "chromium-desktop", testMatch: funcionais, use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    { name: "visual", testMatch: /visual\.spec\.mjs/, use: { browserName: "chromium", viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 } },
  ],
});
