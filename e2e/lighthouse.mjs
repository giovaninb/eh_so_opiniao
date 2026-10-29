// Lighthouse em modo celular (padrão do Lighthouse: Moto G Power emulado, rede "Slow 4G" e CPU 4× mais lenta, ambos SIMULADOS).
// Roda 3 vezes por página e registra TODAS as execuções e a mediana. Nada é ajustado para melhorar a nota.
// Servidor local sem compressão e sem CDN: o resultado em produção (GitHub Pages, com gzip e cache) pode diferir.
import { spawn } from "node:child_process";
import { writeFileSync, mkdirSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { launch } from "chrome-launcher";
import lighthouse from "lighthouse";

const AQUI = fileURLToPath(new URL(".", import.meta.url));
const NAVEGADORES = process.env.ESO_BROWSERS_PATH || join(AQUI, ".browsers");
const pasta = readdirSync(NAVEGADORES).find((n) => /^chromium-\d+$/.test(n));
const chromePath = process.env.CHROME_PATH || join(NAVEGADORES, pasta, "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing");
const REPETICOES = Number(process.env.LH_REPETICOES || 3);

const servidores = [
  { porta: 4181, args: [], rotulo: "dados reais de site/data" },
  { porta: 4182, args: ["--fixture"], rotulo: "biblioteca de TESTE (169 frases)" },
];
const ALVOS = [
  { nome: "home", servidor: 4181, hash: "#/" },
  { nome: "explorar (dados reais)", servidor: 4181, hash: "#/explorar" },
  { nome: "frase", servidor: 4181, hash: "#/frase/FR-01" },
  { nome: "participar", servidor: 4181, hash: "#/participar" },
  { nome: "explorar (169 frases, pior caso)", servidor: 4182, hash: "#/explorar" },
];

const procs = servidores.map((s) => spawn("node", [join(AQUI, "servidor.mjs"), String(s.porta), ...s.args], { stdio: "ignore" }));
await new Promise((r) => setTimeout(r, 1200));
const mediana = (v) => [...v].sort((a, b) => a - b)[Math.floor(v.length / 2)];
const resultados = [];

try {
  for (const alvo of ALVOS) {
    const execs = [];
    for (let i = 0; i < REPETICOES; i++) {
      const chrome = await launch({ chromePath, chromeFlags: ["--headless=new", "--no-sandbox", "--disable-gpu"] });
      try {
        const url = `http://127.0.0.1:${alvo.servidor}/?semente=7${alvo.hash}`;
        const { lhr } = await lighthouse(url, { port: chrome.port, output: "json", logLevel: "error", onlyCategories: ["performance", "accessibility", "best-practices", "seo"] });
        const a = lhr.audits;
        execs.push({
          performance: Math.round(lhr.categories.performance.score * 100),
          acessibilidade: Math.round(lhr.categories.accessibility.score * 100),
          boas_praticas: Math.round(lhr.categories["best-practices"].score * 100),
          seo: Math.round(lhr.categories.seo.score * 100),
          lcp_ms: Math.round(a["largest-contentful-paint"].numericValue),
          cls: Number(a["cumulative-layout-shift"].numericValue.toFixed(4)),
          fcp_ms: Math.round(a["first-contentful-paint"].numericValue),
          tbt_ms: Math.round(a["total-blocking-time"].numericValue),
          transferido_kb: Math.round(a["total-byte-weight"].numericValue / 1024),
          falhas: Object.values(a).filter((x) => x.score !== null && x.score < 0.9 && x.scoreDisplayMode === "binary").map((x) => x.id),
          versao: lhr.lighthouseVersion, ambiente: lhr.configSettings.formFactor + " / " + (lhr.configSettings.throttlingMethod),
        });
      } finally { await chrome.kill(); }
    }
    const chaves = ["performance", "acessibilidade", "boas_praticas", "seo", "lcp_ms", "cls", "fcp_ms", "tbt_ms", "transferido_kb"];
    const med = Object.fromEntries(chaves.map((k) => [k, mediana(execs.map((e) => e[k]))]));
    resultados.push({ pagina: alvo.nome, url: alvo.hash, mediana: med, execucoes: execs });
    console.log(`${alvo.nome.padEnd(34)} perf ${med.performance} · a11y ${med.acessibilidade} · boas práticas ${med.boas_praticas} · seo ${med.seo} · LCP ${med.lcp_ms} ms · CLS ${med.cls} · TBT ${med.tbt_ms} ms · ${med.transferido_kb} KB`);
  }
} finally { procs.forEach((p) => p.kill()); }

mkdirSync(join(AQUI, "resultados"), { recursive: true });
writeFileSync(join(AQUI, "resultados/lighthouse.json"), JSON.stringify({ gerado_em: new Date().toISOString(), repeticoes: REPETICOES, metas: { performance: 90, acessibilidade: 95, boas_praticas: 90, lcp_ms: 2500, cls: 0.1 }, resultados }, null, 2));
const falhou = resultados.filter((r) => r.mediana.performance < 90 || r.mediana.acessibilidade < 95 || r.mediana.boas_praticas < 90 || r.mediana.lcp_ms > 2500 || r.mediana.cls >= 0.1);
console.log(falhou.length ? `\nABAIXO DA META: ${falhou.map((f) => f.pagina).join("; ")}` : "\nTodas as páginas atingiram as metas (mediana de cada página).");
process.exit(falhou.length ? 1 : 0);
