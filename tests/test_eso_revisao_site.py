"""Revisão humana, estudo de caso, publicação e site estático."""

from __future__ import annotations

import json
import re

import pytest

from eh_so_opiniao import casos, paths, publicacao, registry
from eh_so_opiniao.classifiers.rules import RegrasBaseline
from eh_so_opiniao.review import store

FRASE = {"id": "T-1", "origem": "sintetica_ilustrativa", "tipo": "exclusao", "texto": "Frase sintética de teste número um.",
         "mecanismo": "Mecanismo de teste.", "rotulos_propostos": ["exclusao_social_territorial"], "ia_rotulos": ["exclusao_social_territorial"],
         "ia_metodo": "A_regras", "pode_publicar_ambigua": False}


@pytest.fixture
def conn(tmp_path):
    c = store.abrir(tmp_path / "rev.sqlite3")
    yield c
    c.close()


def _publicadas(conn):
    return [f["id"] for f in publicacao.exportar_frases(conn)["frases"]]


# ------------------------------------------------------------------ revisão humana
def test_item_entra_pendente_e_nao_e_publicado(conn):
    assert store.adicionar(conn, FRASE) is True and store.adicionar(conn, FRASE) is False  # idempotente
    assert store.listar(conn)[0]["estado"] == "Pendente"
    assert _publicadas(conn) == []


def test_aprovar_exige_revisor_e_publica(conn):
    store.adicionar(conn, FRASE)
    with pytest.raises(store.RevisaoInvalida):
        store.aprovar(conn, "T-1", "   ")
    store.aprovar(conn, "T-1", "Revisora Teste", "ok")
    assert _publicadas(conn) == ["T-1"]
    pub = publicacao.exportar_frases(conn)["frases"][0]
    assert pub["revisao"] == {"estado": "Aprovado", "por_humano": True}
    assert "Revisora" not in json.dumps(pub, ensure_ascii=False)  # nome do revisor não vai ao público
    assert pub["rotulos"][0]["id"] == "exclusao_social_territorial" and pub["ia"]["concorda_com_revisao"] is True


def test_rejeitar_e_ambiguo_nao_publicam_sem_permissao(conn):
    store.adicionar(conn, FRASE)
    store.adicionar(conn, {**FRASE, "id": "T-2", "pode_publicar_ambigua": True})
    store.rejeitar(conn, "T-1", "R")
    store.marcar_ambiguo(conn, "T-2", "R")
    assert _publicadas(conn) == ["T-2"]  # ambíguo só aparece quando o item permite, e como 'ambigua'
    assert publicacao.exportar_frases(conn)["frases"][0]["rotulos"][0]["id"] == "ambigua"
    store.adicionar(conn, {**FRASE, "id": "T-3"})
    store.marcar_ambiguo(conn, "T-3", "R")
    assert "T-3" not in _publicadas(conn)


def test_corrigir_valida_taxonomia_e_registra_historico(conn):
    store.adicionar(conn, FRASE)
    with pytest.raises(store.RevisaoInvalida):
        store.corrigir(conn, "T-1", "R", ["categoria_inventada"])
    store.corrigir(conn, "T-1", "R", ["critica_politica_legitima"], "era crítica")
    pub = publicacao.exportar_frases(conn)["frases"][0]
    assert [r["id"] for r in pub["rotulos"]] == ["critica_politica_legitima"] and pub["ia"]["concorda_com_revisao"] is False
    store.aprovar(conn, "T-1", "R2")
    h = [(x["de_estado"], x["para_estado"]) for x in store.historico(conn, "T-1")]
    assert h == [("Pendente", "Corrigido"), ("Corrigido", "Aprovado")]
    assert set(store.ESTADOS) == {"Pendente", "Aprovado", "Rejeitado", "Ambíguo", "Corrigido"}


def test_texto_de_corpus_cientifico_nunca_entra_na_fila(conn):
    for ds in registry.listar_datasets():
        with pytest.raises(store.RevisaoInvalida):
            store.adicionar(conn, {**FRASE, "id": f"X-{ds}", "origem": ds})


def test_origem_nao_permitida_nunca_e_publicada_mesmo_aprovada(conn):
    store.adicionar(conn, {**FRASE, "id": "T-9", "origem": "origem_desconhecida"})
    store.aprovar(conn, "T-9", "R")
    assert _publicadas(conn) == []


# ------------------------------------------------------------------ estudo de caso
def test_estudo_de_caso_valido_com_frases_sinteticas_e_ambiguas():
    dados = casos.carregar()
    assert len(dados["frases"]) >= 10
    assert {f["origem"] for f in dados["frases"]} == {"sintetica_ilustrativa"}
    tipos = {f["tipo"] for f in dados["frases"]}
    assert tipos == {"exclusao", "nao_discriminatoria", "ambigua"}
    assert sum(1 for f in dados["frases"] if f["tipo"] == "exclusao") == 5
    assert any("ambigua" in f["rotulos_editoriais"] for f in dados["frases"])
    assert "SINTÉTICAS" in casos.ARQUIVO.read_text(encoding="utf-8")


def test_par_espelho_recebe_a_mesma_leitura_de_regras():
    por_id = {f["id"]: f for f in casos.carregar()["frases"]}
    a, b = por_id["FR-03"], por_id["FR-04"]
    assert a["par_espelho"] == "FR-04" and b["par_espelho"] == "FR-03"
    assert a["rotulos_editoriais"] == b["rotulos_editoriais"]
    assert casos.sugestao_ia(a["texto"]) == casos.sugestao_ia(b["texto"])
    r = RegrasBaseline()
    assert r.prever(a["texto"]) == r.prever(b["texto"])


def test_enfileirar_casos_e_idempotente_e_tudo_pendente(conn):
    r1 = casos.enfileirar(conn)
    r2 = casos.enfileirar(conn)
    assert r1["novos"] == r1["total"] and r2["novos"] == 0
    assert {l["estado"] for l in store.listar(conn)} == {"Pendente"}
    assert _publicadas(conn) == []


# ------------------------------------------------------------------ publicação
def test_site_publica_so_o_que_foi_revisado(conn, tmp_path):
    casos.enfileirar(conn)
    store.aprovar(conn, "FR-06", "Revisora")
    store.rejeitar(conn, "FR-07", "Revisora")
    r = publicacao.construir_site(conn, destino=tmp_path / "data", incluir_rascunho=True, verificar_corpora=False)
    assert r["frases_publicadas"] == 1 and r["frases_rascunho_local"] >= 9  # rascunho exclui rejeitadas
    pub = json.loads((tmp_path / "data" / "frases.json").read_text(encoding="utf-8"))
    assert [f["id"] for f in pub["frases"]] == ["FR-06"]
    rasc = json.loads((tmp_path / "data" / "_rascunho" / "frases.json").read_text(encoding="utf-8"))
    assert "FR-07" not in {f["id"] for f in rasc["frases"]}
    assert all(f["revisao"]["estado"] == "RASCUNHO" for f in rasc["frases"] if f["id"] != "FR-06")
    assert "não conclui crime" in pub["aviso"]
    for nome in ("taxonomia.json", "catalogo.json", "achados.json", "referencias.json"):
        assert (tmp_path / "data" / nome).exists()


def test_varredura_bloqueia_vazamento_de_corpus(conn, tmp_path, monkeypatch):
    texto_do_corpus = "Texto longo de um corpus científico que jamais deveria ser publicado aqui"
    store.adicionar(conn, {**FRASE, "texto": texto_do_corpus})
    store.aprovar(conn, "T-1", "R")
    monkeypatch.setattr(publicacao, "_textos_dos_corpora_locais", lambda: [texto_do_corpus])
    with pytest.raises(publicacao.VazamentoDetectado):
        publicacao.construir_site(conn, destino=tmp_path / "data")
    assert not (tmp_path / "data" / "frases.json").exists()


def test_varredura_pega_variacao_de_caixa_e_pontuacao():
    conteudo = {"frases": [{"texto": "TEXTO do corpus, com outra caixa!"}]}
    assert publicacao.varrer_vazamento(conteudo, ["texto do corpus com outra caixa"])


def test_catalogo_publico_nao_tem_texto_de_amostra():
    cat = {d["id"]: d for d in publicacao.catalogo_publico()}
    assert set(cat) == {"told_br", "hatebr", "multidomain_yt_toxbr", "racismobr", "tupye"}
    assert cat["racismobr"]["status"] == "pendente_fonte" and cat["racismobr"]["registros"] is None
    assert cat["racismobr"]["rotulo_uso"] == "Aguardando fonte oficial"
    assert cat["tupye"]["rotulo_uso"] == "Só para medir sobreposição"
    assert cat["multidomain_yt_toxbr"]["rotulo_uso"].startswith("Em uso local") and cat["multidomain_yt_toxbr"]["licenca"] == "não declarada"
    assert cat["told_br"]["rotulo_uso"] == "Em uso nos experimentos"
    chaves = {k for d in cat.values() for k in d}
    assert not chaves & {"texto", "text", "amostras", "exemplos", "comentarios"}


def test_achados_dos_relatorios_vem_de_numeros_reais_ou_ficam_vazios(tmp_path):
    assert publicacao.achados_dos_relatorios(tmp_path) == []
    real = publicacao.achados_dos_relatorios()
    if (paths.RELATORIOS / "experimento_b.json").exists():
        assert {a["experimento"] for a in real} <= set("ABCDE") | {"AMP-E", "AMP-G"} and all(a["texto"] for a in real)


# ------------------------------------------------------------------ site estático
def _js_do_site() -> str:
    """Todo o JavaScript do site, sem comentários (eles podem citar as regras que proíbem certas práticas)."""
    codigo = "\n".join(p.read_text(encoding="utf-8") for p in sorted((paths.SITE / "js").rglob("*.js")))
    return re.sub(r"/\*.*?\*/|(?<!:)//[^\n]*", "", codigo, flags=re.S)


def test_site_tem_as_vistas_e_a_navegacao_adaptativa():
    html = (paths.SITE / "index.html").read_text(encoding="utf-8")
    vistas = {"inicio": "Início", "descobrir": "Descobrir", "explorar": "Explorar", "frase": "frase", "participar": "Participar",
              "entender": "Entender", "pesquisa": "Pesquisa", "assuntos": "Assuntos"}
    for vista in vistas:
        assert f'data-vista="{vista}"' in html, vista
    for rota in ("#/", "#/descobrir", "#/explorar", "#/participar", "#/entender", "#/pesquisa"):
        assert f'href="{rota}"' in html, rota
    # no celular a barra inferior tem no máximo quatro destinos e há um botão de menu com os demais
    barra = re.search(r'<nav class="barra-inferior".*?</nav>', html, flags=re.S).group(0)
    assert barra.count("<a ") <= 4
    assert 'id="botao-menu"' in html and 'aria-expanded="false"' in html and 'aria-controls="painel-menu"' in html
    assert "Quem Pode Pertencer?" in html and "Onde termina a opinião e começa a discriminação?" in html
    assert "Por que este projeto existe" in html and "Quem publica" in html
    assert 'class="rodape-titulo"' in html and "Licença e responsabilidade" in html
    assert "linkedin.com/in/giovani-bettoni</a>" not in html  # crédito pelo nome, não pela URL crua
    assert '<html lang="pt-BR">' in html and "Pular para o conteúdo" in html
    assert "O que você acha desta frase?" in (paths.SITE / "js" / "componentes" / "cartaoFrase.js").read_text(encoding="utf-8")


def test_site_e_estatico_sem_cdn_sem_rastreamento_e_sem_innerhtml():
    html = (paths.SITE / "index.html").read_text(encoding="utf-8")
    css = (paths.SITE / "css" / "estilo.css").read_text(encoding="utf-8") + (paths.SITE / "css" / "tokens.css").read_text(encoding="utf-8")
    js = _js_do_site()
    for arq in (html, css, js):
        sem_namespace_svg = arq.replace("http://www.w3.org/2000/svg", "")  # xmlns de SVG não é requisição de rede
        # destinos externos só em clique: WhatsApp (compartilhar) e LinkedIn (crédito da autoria)
        sem_namespace_svg = sem_namespace_svg.replace("https://wa.me/?text=", "")
        sem_namespace_svg = sem_namespace_svg.replace("https://www.linkedin.com/in/giovani-bettoni/", "")
        # Turnstile só é carregado no envio (desafio.js), nunca na navegação
        sem_namespace_svg = sem_namespace_svg.replace("https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit", "")
        sem_namespace_svg = sem_namespace_svg.replace("https://challenges.cloudflare.com/turnstile/v0/api.js", "")
        # endereços absolutos só em metadados de prévia social (canonical, og:url, og:image): não são requisições da página
        sem_namespace_svg = re.sub(r'<(?:link rel="canonical"|meta property="og:(?:url|image)"|meta name="twitter:image")[^>]*>', "", sem_namespace_svg)
        assert not re.search(r"https?://(?!exemplo)", sem_namespace_svg), "site não deve chamar recursos externos"
    assert js.count("https://wa.me/") == 1 and 'rel: "noopener noreferrer"' in js  # compartilhar: um link de clique, sem carregar nada
    assert "innerHTML" not in js and "eval(" not in js and "document.write" not in js and "outerHTML" not in js
    for termo in ("analytics", "gtag", "localstorage", "sessionstorage", "document.cookie"):
        assert termo not in (html + js).lower(), termo
    assert (paths.SITE / ".nojekyll").exists()


def test_site_nao_executa_classificacao_nem_carrega_corpora():
    js = _js_do_site()
    for proibido in ("told", "hatebr", "tf-idf", "predict"):
        assert proibido not in js.lower()
    publicado = sorted(p.name for p in (paths.SITE / "data").glob("*.json")) if (paths.SITE / "data").exists() else []
    assert not any(n.endswith(".jsonl") or "bruto" in n for n in publicado)


def test_dados_publicados_no_site_passam_na_varredura_de_vazamento(conn):
    pasta = paths.SITE / "data"
    if not (pasta / "frases.json").exists():
        pytest.skip("site ainda não construído")
    frases = json.loads((pasta / "frases.json").read_text(encoding="utf-8"))
    assert publicacao.varrer_vazamento(frases, publicacao._textos_dos_corpora_locais()) == []
    assert all(f["revisao"]["por_humano"] for f in frases["frases"])


# ------------------------------------------------------------------ anonimização
def test_nenhum_nome_de_lugar_identificavel_no_conteudo_publicavel():
    """Cidade e evento locais não podem aparecer no estudo de caso, nas docs nem no site."""
    proibidos = re.compile("|".join(["ben" + "to g", "gon" + "[çc]alves", "festa da " + "uva", r"\bBG-\d"]), re.I)
    alvos = [*paths.CASOS.glob("*.yaml"), *paths.DOCS.glob("*.md"), paths.RAIZ / "README.md", *paths.SITE.rglob("*.json"),
             paths.SITE / "index.html", paths.SITE / "js" / "app.js"]
    for arq in alvos:
        if "_rascunho" in arq.parts:
            continue
        texto = arq.read_text(encoding="utf-8")
        for autor in ("Marcos André Gonçalves", "Gonçalves, M. A."):  # sobrenome de autor citado em referência bibliográfica, não é lugar
            texto = texto.replace(autor, "")
        assert not proibidos.search(texto), arq


def test_referencias_publicas_nao_tratam_escala_teorica_como_dataset():
    r = {x["id"]: x for x in publicacao.referencias_publicas()["referencias"]}
    assert r["epn_psico_2025"]["tipo"] == "referencia_teorica" and r["epn_psico_2025"]["eh_dataset_supervisionado"] is False
    assert {"hatebrxplain", "tupye"} <= set(r)
    proibidas = {"texto", "text", "amostras", "exemplos", "comentarios"}
    assert not {k for x in r.values() for k in x} & proibidas
