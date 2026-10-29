// Gera site/og/padrao.png (1200×630), a imagem padrão das prévias em redes sociais. Uso: node gerar-og.mjs
import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

process.env.PLAYWRIGHT_BROWSERS_PATH = process.env.ESO_BROWSERS_PATH || join(fileURLToPath(new URL(".", import.meta.url)), ".browsers");
const saida = fileURLToPath(new URL("../site/og/padrao.png", import.meta.url));
const html = `<!doctype html><meta charset="utf-8"><style>
  body{margin:0;width:1200px;height:630px;background:#fbf8f2;font-family:Georgia,"Times New Roman",serif;color:#1d1a17;position:relative}
  .faixa{position:absolute;left:0;top:0;width:100%;height:16px;background:#b53a1c}
  main{position:absolute;left:84px;right:84px;top:130px}
  .e{font:800 26px system-ui,sans-serif;letter-spacing:.08em;color:#b53a1c;text-transform:uppercase;margin:0 0 20px}
  h1{font-size:112px;margin:0;line-height:1.02}
  p.s{font:400 44px/1.25 system-ui,sans-serif;color:#5a524a;margin:28px 0 0;max-width:980px}
  .b{position:absolute;left:84px;bottom:48px;font:400 28px system-ui,sans-serif;color:#5a524a}
</style><div class="faixa"></div><main><p class="e">Exposição · Quem Pode Pertencer?</p><h1>É Só Opinião?</h1><p class="s">Onde termina a opinião e começa a discriminação?</p></main><div class="b">Frases de exemplo, contexto e análise revisada · conteúdo educativo</div>`;
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
await p.setContent(html);
await p.screenshot({ path: saida });
await b.close();
console.log("imagem gerada:", saida);
