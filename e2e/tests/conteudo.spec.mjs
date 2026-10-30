// Testes de conteúdo e de privacidade. Rodam sobre os dados REAIS de site/data (só o que uma pessoa aprovou)
// e, quando indicado, sobre a biblioteca de TESTE (e2e/.dados), que nunca é publicada.
import { test as base, expect } from "@playwright/test";
import { test, abrir } from "./fixtures.mjs";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, extname } from "node:path";

const SITE = fileURLToPath(new URL("../../site", import.meta.url));
const lerJson = (nome) => JSON.parse(readFileSync(join(SITE, "data", nome), "utf8"));

function arquivos(dir) {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? (n === "_rascunho" ? [] : arquivos(p)) : [p];
  });
}

base.describe("pacote publicado (site/ inteiro)", () => {
  base("só contém frases aprovadas por uma pessoa, e nenhuma é rascunho", () => {
    const { frases } = lerJson("frases.json");
    expect(frases.length).toBeGreaterThanOrEqual(1);
    for (const f of frases) {
      expect(f.revisao.estado, f.id).toMatch(/^(Aprovado|Corrigido|Ambíguo)$/);
      expect(f.revisao.por_humano, f.id).toBe(true);
      expect(["ficticio", "adaptado", "documentado", "contribuicao"], f.id).toContain(f.natureza);
      expect(["sintetica_ilustrativa", "fornecida_pelo_operador", "visitante_anonimizada"], f.id).toContain(f.origem);
    }
    expect(JSON.stringify(lerJson("frases.json"))).not.toMatch(/RASCUNHO|Pendente|enviada_por_visitante/);
  });

  base("não há arquivos de corpora, jsonl, csv, sqlite ou parquet publicados", () => {
    const proibidas = [".jsonl", ".csv", ".tsv", ".sqlite", ".sqlite3", ".db", ".parquet", ".pkl", ".zip", ".gz"];
    const achados = arquivos(SITE).filter((p) => proibidas.includes(extname(p).toLowerCase()));
    expect(achados).toEqual([]);
    expect(arquivos(SITE).filter((p) => /(told|hatebr|olid)/i.test(p))).toEqual([]);
  });

  base("o catálogo cita as bases, mas nenhum arquivo publicado contém comentários dos corpora", () => {
    const catalogo = JSON.stringify(lerJson("catalogo.json"));
    expect(catalogo).toMatch(/ToLD-Br/);
    const todo = arquivos(SITE).filter((p) => /\.(json|js|html|css)$/.test(p)).map((p) => readFileSync(p, "utf8")).join("\n");
    expect(todo).not.toMatch(/\b(id_comentario|comment_id|tweet_id)\b/i);
  });

  base("o catálogo marca RacismoBR como aguardando fonte e MultiDomainYT como uso local sob condições, sem texto de amostra", () => {
    const cat = Object.fromEntries(lerJson("catalogo.json").map((d) => [d.id, d]));
    expect(Object.keys(cat).sort()).toEqual(["hatebr", "multidomain_yt_toxbr", "racismobr", "told_br", "tupye"]);
    expect(cat.racismobr.rotulo_uso).toBe("Aguardando fonte oficial");
    expect(cat.racismobr.registros).toBeNull();
    expect(cat.multidomain_yt_toxbr.rotulo_uso).toMatch(/condições de licença/);
    expect(cat.multidomain_yt_toxbr.licenca).toBe("não declarada");
    expect(cat.tupye.rotulo_uso).toBe("Só para medir sobreposição");
    for (const d of Object.values(cat)) expect(Object.keys(d)).not.toEqual(expect.arrayContaining(["texto"]));
    const refs = lerJson("referencias.json").referencias;
    const epn = refs.find((r) => r.id === "epn_psico_2025");
    expect(epn.tipo).toBe("referencia_teorica");
    expect(epn.eh_dataset_supervisionado).toBe(false);
  });

  base("o texto publicado não identifica pessoas nem lugares específicos", () => {
    const todo = [...arquivos(join(SITE, "data")), join(SITE, "index.html")].map((p) => readFileSync(p, "utf8")).join("\n");
    expect(todo).not.toMatch(/bento gon[cç]alves|festa da uva/i);
    expect(todo).not.toMatch(/[\w.+-]+@[\w-]+\.[a-z]{2,}/i); // e-mails
    expect(todo).not.toMatch(/\(\d{2}\)\s?\d{4,5}-\d{4}/); // telefones
    // crédito público da licença CC BY 4.0, não identificação de pessoas nas frases
  });

  base("o site não usa cookies, armazenamento local, analytics nem recursos de terceiros", () => {
    const semComentarios = (t) => t.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    const js = arquivos(join(SITE, "js")).map((p) => semComentarios(readFileSync(p, "utf8"))).join("\n");
    expect(js).not.toMatch(/document\.cookie|localStorage|sessionStorage|indexedDB|navigator\.sendBeacon/);
    expect(js).not.toMatch(/innerHTML|outerHTML|insertAdjacentHTML|eval\(|new Function\(|document\.write/);
    const html = readFileSync(join(SITE, "index.html"), "utf8") + readFileSync(join(SITE, "css/estilo.css"), "utf8");
    expect(html.replace(/https:\/\/www\.linkedin\.com\/in\/giovani-bettoni\//g, "")).not.toMatch(/(src|href)=["']https?:\/\/(?!giovaninb\.github\.io)/);
    expect(html).not.toMatch(/url\(["']?https?:/);
    expect(html).not.toMatch(/googletagmanager|google-analytics|gtag\(|fbq\(|hotjar|plausible/i);
  });

  base("a enquete só exibe números com o mínimo de respostas e, hoje, está vazia", () => {
    const p = lerJson("participacao.json");
    expect(p.minimo_para_exibir).toBeGreaterThanOrEqual(10);
    for (const r of Object.values(p.resultados)) expect(r.total).toBeGreaterThanOrEqual(p.minimo_para_exibir);
  });
});

test.describe("dados reais no navegador", () => {
  test.use({ dados: "real" });

  test("a biblioteca mostra exatamente o que está aprovado, com a etiqueta de natureza em cada cartão", async ({ page }) => {
    const { frases } = lerJson("frases.json");
    await abrir(page, "#/explorar");
    const paginado = frases.length > 12; // a lista mostra 12 por vez
    await expect(page.locator("#contagem-resultados")).toHaveText(paginado ? `Mostrando 12 de ${frases.length} frases` : `${frases.length} frases`);
    while (await page.getByRole("button", { name: /Mostrar mais/ }).count()) await page.getByRole("button", { name: /Mostrar mais/ }).click();
    await expect(page.locator("#contagem-resultados")).toHaveText(`${frases.length} frases`);
    for (const natureza of await page.locator("#explorar-lista .natureza").allTextContents()) {
      expect(natureza).toMatch(/Exemplo fictício|Exemplo adaptado|Caso documentado|Contribuição de visitante/);
    }
    await expect(page.locator("#explorar-lista .item-frase")).toHaveCount(frases.length);
  });

  test("a sugestão de IA fica separada, rotulada como hipótese, e só depois da leitura humana", async ({ page }) => {
    await abrir(page, "#/frase/FR-01");
    await expect(page.locator("details.ia")).toHaveCount(0); // antes de responder, nada de IA nem de análise
    await page.getByRole("button", { name: "Ver análise sem responder" }).click();
    const ia = page.locator("details.ia");
    await expect(ia).toHaveCount(1);
    await expect(ia).toHaveJSProperty("open", false);
    await expect(ia.locator("summary")).toHaveText("Sugestão automática (não é decisão humana)");
    await expect(ia).toContainText("É só uma hipótese");
    await expect(page.locator(".leitura-humana")).not.toContainText("Sugestão automática");
  });

  test("a enquete não exibe contagens quando não há dados reais suficientes", async ({ page }) => {
    await abrir(page, "#/frase/FR-01");
    await page.getByRole("button", { name: "Não vejo problema" }).click();
    await expect(page.locator(".enquete")).not.toContainText(/\d+ (pessoas|votos|leituras)/);
  });

  test("a vista Pesquisa mostra o estado de cada base e as referências, com a escala teórica identificada", async ({ page }) => {
    await abrir(page, "#/pesquisa");
    const lista = page.locator("#lista-catalogo");
    await expect(lista).toContainText("Aguardando fonte oficial");
    await expect(lista).toContainText("Em uso local, sob condições de licença");
    await expect(lista).toContainText("Só para medir sobreposição");
    await expect(page.locator("#lista-referencias a").first()).toHaveAttribute("href", /^https:\/\//);
    const outros = page.locator("#lista-referencias-outros");
    await expect(outros).toContainText("Escala de Preconceito contra Nordestinos");
    await expect(outros).toContainText("Referência teórica, não é base de dados");
    for (const a of await page.locator("#lista-referencias a, #lista-referencias-outros a").all()) await expect(a).toHaveAttribute("aria-label", /.+/);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
  });

  test("nenhuma tela afirma crime, culpa ou identifica autores", async ({ page }) => {
    for (const rota of ["#/", "#/entender", "#/pesquisa", "#/participar"]) {
      await abrir(page, rota);
      const texto = await page.locator("main").innerText();
      expect(texto).not.toMatch(/\b(é crime|cometeu crime|criminoso|culpado)\b/i);
    }
    await abrir(page, "#/participar");
    await expect(page.locator("#privacidade-resumo")).toContainText(/não/i);
  });
});

test.describe("biblioteca de teste (≥60 casos)", () => {
  test("cobre vários temas e inclui exemplos sem discriminação e ambíguos em proporção relevante", async ({ page }) => {
    await abrir(page, "#/explorar");
    const opcoes = await page.locator("#filtro-tema option").evaluateAll((os) => os.map((o) => o.value).filter(Boolean));
    expect(opcoes.length).toBeGreaterThanOrEqual(10);
    const { frases } = JSON.parse(readFileSync(join(fileURLToPath(new URL("..", import.meta.url)), ".dados/frases.json"), "utf8"));
    expect(frases.length).toBeGreaterThanOrEqual(60);
    const por = (t) => frases.filter((f) => f.tipo === t).length;
    expect(por("nao_discriminatoria")).toBeGreaterThanOrEqual(15);
    expect(por("ambigua")).toBeGreaterThanOrEqual(7);
    expect((por("nao_discriminatoria") + por("ambigua")) / frases.length).toBeGreaterThanOrEqual(0.25);
    for (const f of frases) expect(f.natureza, f.id).toBe("ficticio");
  });
});
