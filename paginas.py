"""Páginas estáticas por caso e por comparação, mais `sitemap.xml` e `robots.txt`.

Por quê: o GitHub Pages é estático e os rastreadores de WhatsApp e redes sociais não executam JavaScript. Para o link de
um caso mostrar uma prévia própria, cada caso APROVADO ganha `casos/<id>/index.html` com Open Graph, canonical e conteúdo
legível sem JS. Quem tem JavaScript é levado para a experiência interativa (`#/frase/<ID>`).

Regras:
- só entra o que `publicacao.exportar_frases` já considera publicável (Aprovado/Corrigido, ou Ambíguo liberado);
- nenhum texto de visitante vira metadado público (a origem `visitante_anonimizada` só passa se anonimizada e aprovada);
- a prévia social NÃO revela a leitura (o título é o mesmo para todos) e frase com aviso de conteúdo não é citada nela;
- um caso que já foi publicado e depois sai (rejeitado, corrigido para pendente, retirado) vira uma página "retirado",
  com `noindex`, e deixa o sitemap: o link antigo não quebra nem continua indexado. O histórico fica em
  `casos/registro_publicacao.json`, versionado, gravado só por este módulo.
"""

from __future__ import annotations

import html
import json
import os
import shutil
from pathlib import Path
from typing import Any

from . import paths

URL_BASE = os.environ.get("ESO_URL_BASE", "https://giovaninb.github.io/eh_so_opiniao/").rstrip("/") + "/"
REGISTRO = paths.CASOS / "registro_publicacao.json"
IMAGEM_PADRAO = "og/padrao.png"
NOME = "É Só Opinião?"
SUBTITULO = "Onde termina a opinião e começa a discriminação?"
DESCRICAO_SITE = "Leia frases do cotidiano, diga como você as interpreta e veja o contexto. Projeto educativo da exposição Quem Pode Pertencer?"
LIMITE_DESCRICAO = 190


def slug_caso(caso_id: str) -> str:
    return caso_id.lower()


def url_caso(caso_id: str) -> str:
    return f"{URL_BASE}casos/{slug_caso(caso_id)}/"


def url_par(slug: str) -> str:
    return f"{URL_BASE}comparar/{slug}/"


def url_assunto(assunto_id: str) -> str:
    return f"{URL_BASE}assuntos/{assunto_id}/"


def _e(texto: Any) -> str:
    return html.escape(str(texto), quote=True)


def _curto(texto: str, limite: int = LIMITE_DESCRICAO) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


def _cabecalho(titulo: str, descricao: str, canonica: str, profundidade: int, noindex: bool = False) -> str:
    raiz = "../" * profundidade
    robots = '<meta name="robots" content="noindex, follow">\n  ' if noindex else ""
    og = "" if noindex else f"""<link rel="canonical" href="{_e(canonica)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{_e(NOME)}">
  <meta property="og:locale" content="pt_BR">
  <meta property="og:title" content="{_e(titulo)}">
  <meta property="og:description" content="{_e(descricao)}">
  <meta property="og:url" content="{_e(canonica)}">
  <meta property="og:image" content="{_e(URL_BASE + IMAGEM_PADRAO)}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{_e(NOME + ' ' + SUBTITULO)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{_e(titulo)}">
  <meta name="twitter:description" content="{_e(descricao)}">
  <meta name="twitter:image" content="{_e(URL_BASE + IMAGEM_PADRAO)}">
  """
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#fbf8f2">
  <title>{_e(titulo)}</title>
  <meta name="description" content="{_e(descricao)}">
  {robots}{og}<link rel="stylesheet" href="{raiz}css/tokens.css">
  <link rel="stylesheet" href="{raiz}css/estilo.css">
</head>"""


def _topo(profundidade: int) -> str:
    raiz = "../" * profundidade
    return f"""<body class="pagina-estatica">
  <a class="pular" href="#conteudo">Pular para o conteúdo</a>
  <header class="topo"><div class="pagina topo-interno"><a class="marca" href="{raiz}">{_e(NOME)}</a></div></header>"""


def _rodape(profundidade: int, script: str = "") -> str:
    raiz = "../" * profundidade
    return f"""  <footer class="rodape">
    <div class="rodape-interno">
      <section class="rodape-bloco" aria-labelledby="rodape-o-que-e">
        <h2 id="rodape-o-que-e" class="rodape-titulo">O que é</h2>
        <p>{_e(NOME)} é um material educativo e experimental. Não conclui crime, intenção ou identidade.</p>
      </section>
      <section class="rodape-bloco" aria-labelledby="rodape-responsavel">
        <h2 id="rodape-responsavel" class="rodape-titulo">Licença e responsabilidade</h2>
        <p>Conteúdo sob CC BY 4.0. Quem publica e revisa: <a href="https://www.linkedin.com/in/giovani-bettoni/" rel="noopener noreferrer">Giovani Bettoni</a>.</p>
      </section>
      <p class="rodape-meta"><a href="{raiz}#/entender">Por que este projeto existe</a> · <a href="{raiz}#/explorar">Explorar outras frases</a></p>
    </div>
  </footer>
  {script}
</body>
</html>
"""


def _lista_analise(f: dict[str, Any]) -> str:
    itens = []
    for classe, rotulo, valor in (
        ("bloco-contexto", "Contexto", f.get("contexto")),
        ("bloco-mecanismo", "O que a frase faz", f.get("mecanismo")),
        ("bloco-muda", "O que poderia mudar a leitura", f.get("muda_se")),
    ):
        if valor:
            itens.append(f'<div class="bloco-leitura {classe}"><dt>{_e(rotulo)}</dt><dd>{_e(valor)}</dd></div>')
    if f.get("razoes"):
        itens.append('<div class="bloco-leitura bloco-razoes"><dt>Por que essa leitura</dt><dd><ul>' + "".join(f"<li>{_e(r)}</li>" for r in f["razoes"]) + "</ul></dd></div>")
    return "<dl>" + "".join(itens) + "</dl>"


def _natureza(f: dict[str, Any]) -> str:
    return {"ficticio": "Exemplo fictício", "adaptado": "Exemplo adaptado", "contribuicao": "Contribuição anonimizada"}.get(f.get("natureza"), "Exemplo fictício")


def pagina_caso(f: dict[str, Any]) -> str:
    aviso = bool(f.get("aviso_conteudo"))
    titulo = f"Frase {f['id']}: opinião ou discriminação? — {NOME}"
    if aviso:
        descricao = "Frase de exemplo com aviso de conteúdo (linguagem pejorativa). Veja o contexto, diga como interpreta e leia a análise revisada. Exemplo fictício, conteúdo educativo."
    else:
        descricao = _curto(f"{_natureza(f)}: “{f['texto']}” Como você interpreta? Veja o contexto e a análise revisada.")
    destino = f"../../#/frase/{f['id']}"
    aviso_html = ('<p class="aviso-conteudo" role="note"><strong>Aviso de conteúdo:</strong> a frase abaixo usa ou cita linguagem pejorativa, só para estudo. '
                  "Você pode ir direto à análise.</p>") if aviso else ""
    script = f'<script>if(!/[?&]estatico=1/.test(location.search))location.replace("{_e(destino)}");</script>'
    return f"""{_cabecalho(titulo, descricao, url_caso(f['id']), 2)}
{_topo(2)}
  <main id="conteudo" class="pagina">
    <article class="cartao-frase" aria-labelledby="frase-{_e(f['id'])}">
      <p class="meta"><span class="natureza">{_e(_natureza(f))}</span>{'<span class="aviso-chip">Aviso de conteúdo</span>' if aviso else ''}</p>
      <h1>Opinião ou discriminação?</h1>
      {aviso_html}
      <p class="frase" id="frase-{_e(f['id'])}">“{_e(f['texto'])}”</p>
      <p><a class="botao" href="{_e(destino)}">Responder e ver o que a revisão observou</a></p>
      <details class="detalhe">
        <summary>Ver a análise sem responder</summary>
        <p class="sua-leitura">Leitura da revisão: {_e({'exclusao': 'pode reproduzir preconceito', 'nao_discriminatoria': 'sem discriminação identificável', 'ambigua': 'depende do contexto'}.get(f['tipo'], ''))}. É uma interpretação revisada por uma pessoa, não um diagnóstico nem uma conclusão jurídica.</p>
        {_lista_analise(f)}
      </details>
      <p class="aviso-natureza">{_e('Frase escrita para fins educativos; não é comentário real de uma pessoa verdadeira.' if f.get('natureza') == 'ficticio' else 'Veja a natureza do exemplo na versão interativa.')}</p>
    </article>
  </main>
{_rodape(2, script)}"""


def pagina_retirada(tipo: str, ident: str, profundidade: int = 2) -> str:
    titulo = f"{'Frase' if tipo == 'caso' else 'Comparação'} {ident}: conteúdo retirado — {NOME}"
    descricao = "Este conteúdo foi retirado ou está em nova revisão. Nada dele é exibido aqui."
    raiz = "../" * profundidade
    return f"""{_cabecalho(titulo, descricao, "", profundidade, noindex=True)}
{_topo(profundidade)}
  <main id="conteudo" class="pagina">
    <h1>Este conteúdo não está mais disponível</h1>
    <p>O exemplo <strong>{_e(ident)}</strong> foi retirado ou está passando por uma nova revisão. O link continua existindo para não quebrar quem o recebeu.</p>
    <p><a class="botao" href="{raiz}#/explorar">Ver outras frases revisadas</a></p>
  </main>
{_rodape(profundidade)}"""


def pagina_assunto(assunto: dict[str, Any]) -> str:
    titulo = f"{assunto['nome']} — {NOME}"
    descricao = _curto(assunto.get("descricao") or "Explore frases revisadas deste assunto.")
    destino = f"../../#/assuntos/{assunto['id']}"
    script = f'<script>if(!/[?&]estatico=1/.test(location.search))location.replace("{_e(destino)}");</script>'
    n = int(assunto.get("n") or 0)
    return f"""{_cabecalho(titulo, descricao, url_assunto(assunto['id']), 2)}
{_topo(2)}
  <main id="conteudo" class="pagina">
    <p class="eyebrow">{_e(assunto.get("grupo_nome") or "Assunto")}</p>
    <h1>{_e(assunto['nome'])}</h1>
    <p>{_e(assunto.get("descricao") or "")}</p>
    <p class="suave">{n} exemplo{"s" if n != 1 else ""} revisado{"s" if n != 1 else ""}.</p>
    <p><a class="botao" href="{_e(destino)}">Abrir este assunto</a></p>
    <p><a href="../../#/descobrir?assunto={_e(assunto['id'])}">Descobrir frases</a> · <a href="../../#/explorar?assunto={_e(assunto['id'])}">Explorar todas</a></p>
  </main>
{_rodape(2, script)}"""


def pagina_par(par: dict[str, Any], a: dict[str, Any], b: dict[str, Any]) -> str:
    aviso = bool(a.get("aviso_conteudo") or b.get("aviso_conteudo"))
    titulo = f"Duas frases, uma diferença: {par['titulo']} — {NOME}"
    descricao = "Compare duas frases e veja como uma pequena mudança de alvo ou de linguagem muda a interpretação. Exemplos fictícios, conteúdo educativo."
    destino = f"../../#/comparar/{par['slug']}"
    aviso_html = ('<p class="aviso-conteudo" role="note"><strong>Aviso de conteúdo:</strong> pelo menos uma das frases usa ou cita linguagem pejorativa, só para estudo.</p>') if aviso else ""
    script = f'<script>if(!/[?&]estatico=1/.test(location.search))location.replace("{_e(destino)}");</script>'
    return f"""{_cabecalho(titulo, descricao, url_par(par['slug']), 2)}
{_topo(2)}
  <main id="conteudo" class="pagina">
    <h1>Duas frases, uma diferença</h1>
    <p class="suave">{_e(par['titulo'])}</p>
    {aviso_html}
    <div class="comparacao">
      <blockquote class="frase"><span class="rotulo-par">Frase A</span> “{_e(a['texto'])}”</blockquote>
      <blockquote class="frase"><span class="rotulo-par">Frase B</span> “{_e(b['texto'])}”</blockquote>
    </div>
    <p><a class="botao" href="{_e(destino)}">Comparar e ver a diferença</a></p>
    <details class="detalhe"><summary>Ver a diferença sem responder</summary>
      <p>{_e(par['diferenca'])}</p>
      <p class="suave"><strong>Limite da comparação:</strong> {_e(par['limite'])}</p>
    </details>
  </main>
{_rodape(2, script)}"""


def _sitemap(urls: list[str]) -> str:
    corpo = "".join(f"  <url><loc>{_e(u)}</loc></url>\n" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{corpo}</urlset>\n'


def _robots() -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {URL_BASE}sitemap.xml\n"


def _ler_registro(caminho: Path | None) -> dict[str, list[str]]:
    if caminho and Path(caminho).exists():
        d = json.loads(Path(caminho).read_text(encoding="utf-8"))
        return {"casos": list(d.get("casos", [])), "pares": list(d.get("pares", []))}
    return {"casos": [], "pares": []}


def gerar(frases: list[dict[str, Any]], pares: list[dict[str, Any]], raiz_site: Path, registro: Path | None = REGISTRO,
          assuntos: list[dict[str, Any]] | None = None) -> dict[str, int]:
    """Escreve `casos/`, `comparar/`, `assuntos/`, `sitemap.xml` e `robots.txt` em `raiz_site`. Recria as pastas a cada execução."""
    por_id = {f["id"]: f for f in frases}
    historico = _ler_registro(registro)
    casos_hist = sorted(set(historico["casos"]) | set(por_id))
    pares_hist = sorted(set(historico["pares"]) | {p["slug"] for p in pares})
    for pasta in ("casos", "comparar", "assuntos"):
        alvo = raiz_site / pasta
        if alvo.exists():
            shutil.rmtree(alvo)
    n_retirados = 0
    for cid in casos_hist:
        pasta = raiz_site / "casos" / slug_caso(cid)
        pasta.mkdir(parents=True, exist_ok=True)
        if cid in por_id:
            conteudo = pagina_caso(por_id[cid])
        else:
            conteudo, n_retirados = pagina_retirada("caso", cid), n_retirados + 1
        (pasta / "index.html").write_text(conteudo, encoding="utf-8")
    atuais = {p["slug"]: p for p in pares}
    for slug in pares_hist:
        pasta = raiz_site / "comparar" / slug
        pasta.mkdir(parents=True, exist_ok=True)
        if slug in atuais:
            p = atuais[slug]
            conteudo = pagina_par(p, por_id[p["a"]], por_id[p["b"]])
        else:
            conteudo, n_retirados = pagina_retirada("comparacao", slug.upper()), n_retirados + 1
        (pasta / "index.html").write_text(conteudo, encoding="utf-8")
    visiveis = [a for a in (assuntos or []) if a.get("visivel") and a.get("n")]
    for a in visiveis:
        pasta = raiz_site / "assuntos" / a["id"]
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "index.html").write_text(pagina_assunto(a), encoding="utf-8")
    urls = [URL_BASE] + [url_caso(i) for i in sorted(por_id)] + [url_par(s) for s in sorted(atuais)] + [url_assunto(a["id"]) for a in visiveis]
    (raiz_site / "sitemap.xml").write_text(_sitemap(urls), encoding="utf-8")
    (raiz_site / "robots.txt").write_text(_robots(), encoding="utf-8")
    if registro is not None:
        Path(registro).write_text(json.dumps({"casos": casos_hist, "pares": pares_hist}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"casos": len(por_id), "pares": len(atuais), "assuntos": len(visiveis), "retirados": n_retirados, "urls_no_sitemap": len(urls)}
