"""Páginas estáticas por caso (Open Graph sem JavaScript), sitemap, robots, retirados e comparações revisadas."""

from __future__ import annotations

import json
import re

import pytest

from eh_so_opiniao import casos, pares, paginas, paths, publicacao
from eh_so_opiniao.review import store


@pytest.fixture
def conn(tmp_path):
    c = store.abrir(tmp_path / "rev.sqlite3")
    yield c
    c.close()


def _frase(i="EX-61", texto="Quem é de fora não entende como as coisas funcionam aqui.", **extra):
    base = {"id": i, "texto": texto, "tipo": "ambigua", "tema": "depende_contexto", "natureza": "ficticio", "contexto": "Fala imaginada.",
            "razoes": ["Pode ser aviso gentil.", "Pode barrar quem chegou."], "muda_se": "O tom.", "mecanismo": "Pode ser barreira de pertencimento.",
            "aviso_conteudo": False}
    return {**base, **extra}


def _meta(html, chave):
    m = re.search(rf'<meta (?:property|name)="{re.escape(chave)}" content="([^"]*)"', html)
    return m.group(1) if m else None


# ------------------------------------------------------------------ página de um caso
def test_pagina_do_caso_tem_titulo_descricao_canonical_e_open_graph_sem_js():
    h = paginas.pagina_caso(_frase())
    url = "https://giovaninb.github.io/eh_so_opiniao/casos/ex-61/"
    assert "<title>Frase EX-61: opinião ou discriminação? — É Só Opinião?</title>" in h
    assert f'<link rel="canonical" href="{url}">' in h
    for chave in ("og:title", "og:description", "og:url", "og:image", "twitter:card", "twitter:image"):
        assert _meta(h, chave), chave
    assert _meta(h, "og:url") == url and _meta(h, "og:image").endswith("/og/padrao.png")
    assert _meta(h, "og:image:width") == "1200" and _meta(h, "og:image:height") == "630"
    assert "Quem é de fora não entende" in _meta(h, "og:description")
    # conteúdo utilizável sem JavaScript: a frase, a análise em <details> e o link para a versão interativa
    assert '<p class="frase"' in h and "<details" in h and 'href="../../#/frase/EX-61"' in h
    assert "Exemplo fictício" in h and '<html lang="pt-BR">' in h and "<h1>" in h


def test_o_titulo_nao_revela_a_leitura_e_e_igual_para_todos():
    t = {re.search(r"<title>(.*?)</title>", paginas.pagina_caso(_frase(tipo=t))).group(1).replace("EX-61", "") for t in ("exclusao", "ambigua", "nao_discriminatoria")}
    assert len(t) == 1
    h = paginas.pagina_caso(_frase(tipo="exclusao", tema="racismo"))
    assert "racismo" not in _meta(h, "og:title").lower() and "discriminação?" in _meta(h, "og:title")


def test_frase_com_aviso_nao_e_citada_na_previa_social():
    f = _frase("NX-326", "Chuta que é macumba, não deixa essa oferenda aí.", tipo="exclusao", aviso_conteudo=True)
    h = paginas.pagina_caso(f)
    for chave in ("description", "og:title", "og:description", "twitter:description", "twitter:title"):
        assert "macumba" not in (_meta(h, chave) or "").lower(), chave
    assert "macumba" not in re.search(r"<title>(.*?)</title>", h).group(1).lower()
    assert 'role="note"' in h and "Aviso de conteúdo" in h
    assert "aviso de conteúdo" in _meta(h, "og:description").lower()


def test_texto_com_html_e_escapado_nas_metatags_e_no_corpo():
    h = paginas.pagina_caso(_frase(texto='Ele disse "<script>alert(1)</script>" & saiu.'))
    assert "<script>alert(1)</script>" not in h
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in h and "&quot;" in _meta(h, "og:description") or "&quot;" in h
    assert h.count("<script>") == 1  # só o redirecionamento para a experiência interativa


def test_pagina_retirada_tem_noindex_e_nao_mostra_conteudo():
    h = paginas.pagina_retirada("caso", "EX-99")
    assert 'name="robots" content="noindex' in h and "canonical" not in h and "og:title" not in h
    assert "EX-99" in h and "<blockquote" not in h and 'class="frase"' not in h


# ------------------------------------------------------------------ geração, sitemap, robots e retirados
def test_gerar_escreve_so_o_que_foi_publicado_sitemap_e_robots(tmp_path):
    r = paginas.gerar([_frase("EX-01"), _frase("EX-02")], [], tmp_path, registro=None)
    assert r == {"casos": 2, "pares": 0, "retirados": 0, "urls_no_sitemap": 3}
    assert sorted(p.parent.name for p in (tmp_path / "casos").glob("*/index.html")) == ["ex-01", "ex-02"]
    sm = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert sm.count("<loc>") == 3 and "casos/ex-01/" in sm and "NX-" not in sm
    robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: https://giovaninb.github.io/eh_so_opiniao/sitemap.xml" in robots and "Disallow" not in robots


def test_caso_que_saiu_vira_pagina_retirada_fora_do_sitemap_e_o_link_nao_quebra(tmp_path):
    registro = tmp_path / "registro.json"
    paginas.gerar([_frase("EX-01"), _frase("EX-02")], [], tmp_path, registro=registro)
    paginas.gerar([_frase("EX-01")], [], tmp_path, registro=registro)  # EX-02 foi retirado
    h = (tmp_path / "casos" / "ex-02" / "index.html").read_text(encoding="utf-8")
    assert "noindex" in h and "Quem é de fora" not in h
    assert "casos/ex-02/" not in (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert json.loads(registro.read_text(encoding="utf-8"))["casos"] == ["EX-01", "EX-02"]  # o histórico não perde ids
    again = paginas.gerar([_frase("EX-01"), _frase("EX-02")], [], tmp_path, registro=registro)  # voltou: página normal
    assert again["retirados"] == 0 and "noindex" not in (tmp_path / "casos" / "ex-02" / "index.html").read_text(encoding="utf-8")


def test_geracao_e_idempotente_e_apaga_paginas_antigas_sem_registro(tmp_path):
    paginas.gerar([_frase("EX-01"), _frase("EX-02")], [], tmp_path, registro=None)
    a = (tmp_path / "casos" / "ex-01" / "index.html").read_text(encoding="utf-8")
    paginas.gerar([_frase("EX-01")], [], tmp_path, registro=None)
    assert (tmp_path / "casos" / "ex-01" / "index.html").read_text(encoding="utf-8") == a
    assert not (tmp_path / "casos" / "ex-02").exists()  # sem registro, nada de resíduo


def test_pendente_e_rejeitado_nao_ganham_pagina(conn, tmp_path):
    antes = (paths.CASOS / "registro_publicacao.json").read_bytes()
    casos.enfileirar(conn)
    store.aprovar(conn, "EX-61", "revisora-teste")
    store.rejeitar(conn, "EX-62", "revisora-teste")
    r = publicacao.construir_site(conn, destino=tmp_path / "site" / "data", verificar_corpora=False, paginas_estaticas=True)
    assert r["paginas"]["casos"] == 1
    pastas = [p.name for p in (tmp_path / "site" / "casos").iterdir()]
    assert pastas == ["ex-61"]
    assert (paths.CASOS / "registro_publicacao.json").read_bytes() == antes  # destino de teste não toca o registro real


def test_construir_site_com_destino_de_teste_nao_gera_paginas_por_padrao(conn, tmp_path):
    casos.enfileirar(conn)
    store.aprovar(conn, "EX-61", "revisora-teste")
    r = publicacao.construir_site(conn, destino=tmp_path / "data", verificar_corpora=False)
    assert r["paginas"] == {} and not (tmp_path / "casos").exists() and (tmp_path / "data" / "pares.json").exists()


# ------------------------------------------------------------------ o que está de fato no site
def test_paginas_do_site_real_batem_com_o_que_esta_publicado():
    publicadas = {f["id"] for f in json.loads((paths.SITE / "data" / "frases.json").read_text(encoding="utf-8"))["frases"]}
    pastas = {p.parent.name for p in (paths.SITE / "casos").glob("*/index.html")}
    historico = {i.lower() for i in json.loads((paths.CASOS / "registro_publicacao.json").read_text(encoding="utf-8"))["casos"]}
    assert {i.lower() for i in publicadas} <= pastas and pastas == historico
    sm = (paths.SITE / "sitemap.xml").read_text(encoding="utf-8")
    assert sm.count("<loc>") == len(publicadas) + 1
    for i in publicadas:
        h = (paths.SITE / "casos" / i.lower() / "index.html").read_text(encoding="utf-8")
        assert "noindex" not in h and f"/casos/{i.lower()}/" in sm
    for retirada in pastas - {i.lower() for i in publicadas}:
        assert "noindex" in (paths.SITE / "casos" / retirada / "index.html").read_text(encoding="utf-8")
    assert not any(p.startswith("nx-") for p in pastas), "NX-* só ganha página depois de revisão humana"


def test_nenhuma_pagina_publicada_cita_dado_de_revisao_ou_corpus():
    for arq in (paths.SITE / "casos").glob("*/index.html"):
        t = arq.read_text(encoding="utf-8").lower()
        for proibido in ("revisor", "hatebr", "told", "origem_original", "rotulos_humanos", "fixture-e2e"):
            assert proibido not in t, (arq, proibido)


# ------------------------------------------------------------------ comparações
def test_pares_do_repositorio_sao_validos_e_usam_frases_existentes():
    todos = {f["id"] for f in casos.carregar_todos()["frases"]}
    lista = pares.carregar(ids_validos=todos)
    assert len(lista) >= 10 and len({p["id"] for p in lista}) == len(lista)
    assert all(p["limite"] and p["diferenca"] for p in lista)


def test_par_com_frase_inexistente_ou_igual_e_recusado(tmp_path):
    arq = tmp_path / "p.yaml"
    arq.write_text('pares:\n  - {id: P-1, titulo: "t", a: EX-01, b: EX-01, diferenca: "d", limite: "l"}\n', encoding="utf-8")
    with pytest.raises(pares.ParInvalido, match="mesma"):
        pares.carregar(arq)
    arq.write_text('pares:\n  - {id: P-1, titulo: "t", a: EX-01, b: ZZ-99, diferenca: "d", limite: "l"}\n', encoding="utf-8")
    with pytest.raises(pares.ParInvalido, match="inexistente"):
        pares.carregar(arq, ids_validos={"EX-01"})


def test_par_so_e_publicado_se_revisado_e_com_as_duas_frases_publicadas():
    lista = [{"id": "P-1", "titulo": "t", "a": "EX-01", "b": "EX-02", "diferenca": "d", "limite": "l"}]
    assert pares.exportar({"EX-01", "EX-02"}, lista, revisados=set())["pares"] == []           # sem revisão do par
    assert pares.exportar({"EX-01"}, lista, revisados={"P-1"})["pares"] == []                   # uma frase não publicada
    ok = pares.exportar({"EX-01", "EX-02"}, lista, revisados={"P-1"})["pares"]
    assert [p["slug"] for p in ok] == ["p-1"] and "revisor" not in json.dumps(ok)


def test_aprovar_par_exige_revisor_e_nao_aprova_sozinho(tmp_path):
    arq = tmp_path / "rev.json"
    with pytest.raises(pares.ParInvalido, match="revisor"):
        pares.aprovar("P-01", "  ", caminho=arq)
    pares.aprovar("P-01", "revisora-teste", caminho=arq)
    assert pares.revisoes(arq)["P-01"]["revisor"] == "revisora-teste"
    pares.retirar("P-01", caminho=arq)
    assert pares.revisoes(arq) == {}


def test_nenhum_par_aprovado_automaticamente_no_repositorio():
    assert pares.revisoes() == {}, "pares só podem ser aprovados por uma pessoa (python -m eh_so_opiniao pares aprovar)"
    publicado = json.loads((paths.SITE / "data" / "pares.json").read_text(encoding="utf-8"))
    assert publicado == {"pares": []}
