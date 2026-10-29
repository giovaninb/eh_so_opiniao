// Servidor estático mínimo para os testes (sem dependências): serve ../site.
// Com --fixture, /data/*.json vêm de e2e/.dados (biblioteca completa de TESTE). Nunca usado em produção.
import { createServer } from "node:http";
import { gzipSync } from "node:zlib";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = fileURLToPath(new URL(".", import.meta.url));
const SITE = resolve(AQUI, "../site");
const DADOS = resolve(AQUI, ".dados");
const porta = Number(process.argv.find((a) => /^\d+$/.test(a)) || 4173);
const fixture = process.argv.includes("--fixture");
const TIPOS = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon" };

createServer(async (req, res) => {
  try {
    let caminho = decodeURIComponent(new URL(req.url, "http://x").pathname);
    if (caminho.endsWith("/")) caminho += "index.html";
    const base = fixture && caminho.startsWith("/data/") && !caminho.includes("_rascunho") ? DADOS : SITE;
    const rel = fixture && base === DADOS ? caminho.replace("/data/", "/") : caminho;
    const arquivo = normalize(join(base, rel));
    if (!arquivo.startsWith(base)) { res.writeHead(403).end(); return; }
    await stat(arquivo);
    const corpo = await readFile(arquivo);
    // Compressão gzip de texto, como faz o GitHub Pages. Desligue com --sem-gzip para medir sem compressão.
    const tipo = TIPOS[extname(arquivo)] || "application/octet-stream";
    const gz = !process.argv.includes("--sem-gzip") && /(html|css|javascript|json|svg)/.test(tipo) && /gzip/.test(req.headers["accept-encoding"] || "");
    res.writeHead(200, { "Content-Type": tipo, "Cache-Control": "no-store", ...(gz ? { "Content-Encoding": "gzip", Vary: "Accept-Encoding" } : {}) });
    res.end(gz ? gzipSync(corpo) : corpo);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" }).end("não encontrado");
  }
}).listen(porta, "127.0.0.1", () => console.log(`site de teste em http://127.0.0.1:${porta} ${fixture ? "(dados de TESTE)" : "(dados reais de site/data)"}`));
