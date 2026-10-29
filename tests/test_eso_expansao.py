"""Expansão editorial 2026-10 (mulheres, homens, pessoas idosas, religiões, pessoas trans): importação sem aprovar nada,
IDs preservados, dimensões independentes, casos de contexto e publicação só do que uma pessoa aprovou."""

from __future__ import annotations

import csv
import json
from collections import Counter

import pytest

from eh_so_opiniao import casos, expansao, paths, publicacao, registry
from eh_so_opiniao.review import store

NOVOS_TEMAS = {"transfobia", "idadismo", "estereotipos_masculinidade"}
TEMAS_DA_EXPANSAO = NOVOS_TEMAS | {"misoginia", "intolerancia_religiosa", "lgbtfobia", "depende_contexto", "sem_discriminacao"}


@pytest.fixture
def conn(tmp_path):
    c = store.abrir(tmp_path / "rev.sqlite3")
    yield c
    c.close()


@pytest.fixture(scope="module")
def novos():
    return expansao.carregar()["frases"]


def _por_id(frases):
    return {f["id"]: f for f in frases}


# ------------------------------------------------------------------ IDs e total preservados
def test_total_ids_unicos_e_ids_antigos_preservados(novos):
    todas = casos.carregar_todos()["frases"]
    ids = [f["id"] for f in todas]
    assert len(ids) == len(set(ids)) == 345
    assert len(novos) == 176 and all(f["id"].startswith("NX-") for f in novos)
    antigos = {f"EX-{i:02d}" for i in range(1, 159)} | {f"FR-{i:02d}" for i in range(1, 12)}
    assert antigos <= set(ids)  # nenhum ID anterior sumiu
    assert len(antigos) == 169


def test_textos_antigos_nao_foram_alterados_pela_expansao(novos):
    antes = {f["id"]: f["texto"] for f in casos.carregar_todos()["frases"] if not f["id"].startswith("NX-")}
    assert len(antes) == 169
    assert not (set(antes) & {f["id"] for f in novos})


def test_csv_diferencial_bate_com_o_jsonl(novos):
    with (paths.CASOS / "expansao_2026_10_diferencial.csv").open(encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    assert {l["id"] for l in linhas} == {f["id"] for f in novos}
    assert {l["texto"] for l in linhas} == {f["texto"] for f in novos}


def test_contagem_por_tema_da_expansao(novos):
    por_tema = Counter(f["tema"] for f in novos)
    assert set(por_tema) == TEMAS_DA_EXPANSAO
    assert sum(por_tema.values()) == 176
    assert {t for t in NOVOS_TEMAS} <= {t["id"] for t in casos.temas()}


# ------------------------------------------------------------------ nada é aprovado ou publicado automaticamente
def test_importacao_enfileira_tudo_como_pendente_e_e_idempotente(conn):
    r1 = casos.enfileirar(conn)
    assert r1["total"] == 345 and r1["novos"] == 345
    pendentes = {l["id"] for l in store.listar(conn, "Pendente")}
    assert {f"NX-{i}" for i in range(248, 424)} <= pendentes or len([i for i in pendentes if i.startswith("NX-")]) == 176
    assert not any(l["estado"] != "Pendente" for l in store.listar(conn) if l["id"].startswith("NX-"))
    r2 = casos.enfileirar(conn)
    assert r2["novos"] == 0  # idempotente
    assert len(store.listar(conn)) == 345


def test_reimportar_nao_sobrescreve_decisao_nem_correcao(conn):
    casos.enfileirar(conn)
    store.aprovar(conn, "NX-250", "revisora-teste", "ok")
    store.corrigir(conn, "NX-251", "revisora-teste", ["misoginia"], "ajuste humano")
    texto_antes = {l["id"]: l["texto"] for l in store.listar(conn)}
    casos.enfileirar(conn)
    estados = {l["id"]: l for l in store.listar(conn)}
    assert estados["NX-250"]["estado"] == "Aprovado" and estados["NX-250"]["revisor"] == "revisora-teste"
    assert estados["NX-251"]["estado"] == "Corrigido" and json.loads(estados["NX-251"]["rotulos_humanos"]) == ["misoginia"]
    assert {i: l["texto"] for i, l in estados.items()} == texto_antes


def test_nada_da_expansao_e_publicado_sem_aprovacao(conn):
    casos.enfileirar(conn)
    ids = {f["id"] for f in publicacao.exportar_frases(conn)["frases"]}
    assert not any(i.startswith("NX-") for i in ids)
    store.aprovar(conn, "NX-250", "revisora-teste")
    ids = {f["id"] for f in publicacao.exportar_frases(conn)["frases"]}
    assert "NX-250" in ids and "NX-251" not in ids


def test_nenhuma_frase_da_expansao_esta_aprovada_no_site_publicado():
    publicadas = json.loads((paths.RAIZ / "site" / "data" / "frases.json").read_text(encoding="utf-8"))["frases"]
    assert not any(f["id"].startswith("NX-") for f in publicadas), "NX-* só pode estar no site depois de revisão humana"


@pytest.mark.parametrize("mudanca", [{"estado_revisao": "Aprovado"}, {"pode_publicar": True}])
def test_entrada_aprovada_ou_publicavel_e_recusada(tmp_path, novos, mudanca):
    primeira = json.loads((paths.CASOS / "expansao_2026_10.jsonl").read_text(encoding="utf-8").splitlines()[0])
    primeira.update(mudanca)
    arq = tmp_path / "entrada.jsonl"
    arq.write_text(json.dumps(primeira, ensure_ascii=False) + "\n", encoding="utf-8")
    with pytest.raises(expansao.ExpansaoInvalida, match="Pendente"):
        expansao.carregar(arq)


def test_id_duplicado_na_entrada_e_recusado(tmp_path):
    linha = (paths.CASOS / "expansao_2026_10.jsonl").read_text(encoding="utf-8").splitlines()[0]
    arq = tmp_path / "dup.jsonl"
    arq.write_text(linha + "\n" + linha + "\n", encoding="utf-8")
    with pytest.raises(expansao.ExpansaoInvalida, match="duplicado"):
        expansao.carregar(arq)


# ------------------------------------------------------------------ dimensões independentes
def test_dimensoes_completas_e_com_valores_validos(novos):
    ids_grupo = {g["id"] for g in expansao.grupos()}
    for f in novos:
        d = f["dimensoes"]
        assert set(d) == {"grupo", "mecanismo", "gravidade", "contexto_de_uso", "certeza_rotulo"}, f["id"]
        assert d["grupo"] in ids_grupo
        assert d["gravidade"] in expansao.GRAVIDADES and d["certeza_rotulo"] in expansao.CERTEZAS
        assert d["mecanismo"] and d["contexto_de_uso"]


def test_gravidade_distingue_estereotipo_ofensa_exclusao_e_nao_declara_crime(novos):
    por_gravidade = Counter(f["dimensoes"]["gravidade"] for f in novos)
    assert por_gravidade["incitacao_violencia"] == 0  # nenhum exemplo foi marcado assim; só pessoa revisora pode fazê-lo
    assert {"estereotipo", "ofensa", "exclusao_material", "nao_se_aplica"} <= set(por_gravidade)
    for f in novos:
        if f["tipo"] != "exclusao":
            assert f["dimensoes"]["gravidade"] == "nao_se_aplica", f["id"]
        else:
            assert f["dimensoes"]["gravidade"] != "nao_se_aplica", f["id"]
        assert "crime" not in json.dumps(f["dimensoes"], ensure_ascii=False).lower()


def test_ambiguas_tem_certeza_baixa_e_dizem_o_que_muda_a_leitura(novos):
    amb = [f for f in novos if f["tipo"] == "ambigua"]
    assert len(amb) == 25
    for f in amb:
        assert f["dimensoes"]["certeza_rotulo"] == "baixa" and f["muda_se"]
        assert "ambigua" in f["rotulos_editoriais"]


def test_controles_nao_ganham_rotulo_de_discriminacao(novos):
    controles = [f for f in novos if f["tipo"] == "nao_discriminatoria"]
    assert controles and all(f["rotulos_editoriais"] == [] and f["tema"] == "sem_discriminacao" for f in controles)


def test_lgbtfobia_e_transfobia_nao_se_misturam(novos):
    for f in novos:
        if f["tema"] == "transfobia":
            assert "transfobia" in f["rotulos_editoriais"] and "lgbtfobia" not in f["rotulos_editoriais"]
            assert f["dimensoes"]["grupo"] == "pessoas_trans"
        if f["tema"] == "lgbtfobia":
            assert "lgbtfobia" in f["rotulos_editoriais"] and "transfobia" not in f["rotulos_editoriais"]
        if f["tema"] == "estereotipos_masculinidade":
            assert "misoginia" not in f["rotulos_editoriais"] and f["dimensoes"]["grupo"] == "homens"


def test_grupos_de_descoberta_pedidos_existem():
    nomes = {g["nome"] for g in expansao.grupos()}
    assert {"Mulheres", "Homens e expectativas sociais", "Pessoas idosas", "Religiões", "Pessoas trans"} <= nomes


# ------------------------------------------------------------------ contexto: palavra isolada não decide
def test_casos_de_contexto_nao_sao_tratados_como_discriminacao(novos):
    m = _por_id(novos)
    assert m["NX-397"]["tipo"] == "ambigua" and "corpo errado" in m["NX-397"]["texto"]  # autodescrição
    assert m["NX-385"]["tipo"] == "ambigua" and "homem da casa" in m["NX-385"]["texto"]
    assert m["NX-297"]["tipo"] == "ambigua" and "para a sua idade" in m["NX-297"]["texto"]
    assert m["NX-400"]["tipo"] == "ambigua" and "travesti" in m["NX-400"]["texto"]  # pergunta, não ofensa
    # a mesma expressão pode ser exclusão quando o contexto muda
    assert m["NX-281"]["tipo"] == "exclusao" and "homem da casa" in m["NX-281"]["texto"]
    assert m["NX-301"]["tipo"] == "exclusao" and "para a sua idade" in m["NX-301"]["texto"]
    assert m["NX-326"]["tipo"] == "exclusao" and "macumba" in m["NX-326"]["texto"]


def test_termo_pejorativo_em_exclusao_traz_aviso_e_controles_nao(novos):
    m = _por_id(novos)
    assert m["NX-325"]["aviso_conteudo"] and m["NX-326"]["aviso_conteudo"]
    assert not m["NX-397"]["aviso_conteudo"]
    assert all(f["tipo"] == "exclusao" for f in novos if f["aviso_conteudo"])  # controle e ambígua nunca levam o selo
    assert sum(1 for f in novos if f["aviso_conteudo"]) == 56


def test_baseline_de_regras_nao_cria_as_classes_novas(conn):
    """A sugestão automática é só rascunho e não conhece as classes exploratórias: palavras soltas não viram rótulo."""
    casos.enfileirar(conn)
    for linha in store.listar(conn):
        if linha["id"].startswith("NX-"):
            assert not (NOVOS_TEMAS & set(json.loads(linha["ia_rotulos"])))


# ------------------------------------------------------------------ taxonomia e regressão das categorias antigas
def test_classes_novas_sao_exploratorias_e_sem_rotulo_mapeado():
    tax = registry.carregar_taxonomia()
    for classe in NOVOS_TEMAS:
        assert tax[classe]["tipo"] == "exploratorio"
        assert tax[classe].get("definicao") and tax[classe].get("nao_e")
    mapeados = {c.alvo for c in registry.correspondencias()}
    assert not (NOVOS_TEMAS & mapeados)
    assert tax["lgbtfobia"]["tipo"] == "supervisionado"  # homofobia continua onde estava


def test_categorias_antigas_continuam_com_os_mesmos_ids_de_tema():
    ids = {t["id"] for t in casos.temas()}
    assert {"racismo", "xenofobia", "misoginia", "lgbtfobia", "capacitismo", "intolerancia_religiosa", "depende_contexto",
            "sem_discriminacao", "ironia", "critica_legitima", "desumanizacao"} <= ids


# ------------------------------------------------------------------ publicação: só o aprovado, com dimensões e grupo
def test_publicacao_exporta_grupo_dimensoes_e_aviso_so_do_aprovado(conn):
    casos.enfileirar(conn)
    for i in ("NX-326", "NX-397", "NX-422", "EX-61"):
        store.aprovar(conn, i, "revisora-teste") if i != "NX-397" else store.marcar_ambiguo(conn, i, "revisora-teste")
    dados = publicacao.exportar_frases(conn)
    m = _por_id(dados["frases"])
    assert set(m) == {"NX-326", "NX-397", "NX-422", "EX-61"}
    assert m["NX-326"]["aviso_conteudo"] is True and m["NX-326"]["grupo"] == "religioes"
    assert m["NX-326"]["dimensoes"]["gravidade"] == "ofensa"
    assert m["NX-397"]["grupo"] == "pessoas_trans" and m["NX-397"]["tipo"] == "ambigua"
    assert {g["id"] for g in dados["grupos"]} == {"religioes", "pessoas_trans"} | ({m["EX-61"]["grupo"]} - {None})
    for f in dados["frases"]:
        assert "estado_revisao" not in f and "revisor" not in json.dumps(f)  # sem dados de quem revisou


def test_nenhum_dado_de_autor_ou_corpus_de_treino_no_json_publicado(conn):
    casos.enfileirar(conn)
    store.aprovar(conn, "NX-250", "revisora-teste")
    texto = json.dumps(publicacao.exportar_frases(conn), ensure_ascii=False)
    for proibido in ("revisora-teste", "hatebr", "told", "brazilian_twitter", "origem_original", "colecao"):
        assert proibido not in texto.lower(), proibido


# ------------------------------------------------------------------ dados de contexto (ANTRA)
def test_contexto_publico_traz_fonte_ano_metodologia_e_limites():
    itens = {i["id"]: i for i in publicacao.contexto_publico()["itens"]}
    a = itens["antra_assassinatos_2025"]
    assert a["grupo"] == "pessoas_trans" and a["ano"] == 2025
    for campo in ("dado", "fonte", "metodologia", "limitacoes", "conferencia", "links"):
        assert a[campo], campo
    assert "80" in a["dado"] and "subnotifica" in a["limitacoes"].lower()
    assert "não é censo" in a["limitacoes"].lower()
    assert all(l["url"].startswith("https://") for l in a["links"])


def test_nao_afirma_que_pessoas_trans_vivem_ate_35_anos():
    itens = publicacao.contexto_publico()["itens"]
    item = next(i for i in itens if i["id"] == "antra_35_anos")
    assert "não afirma" in item["limitacoes"].lower() and "não é tábua de mortalidade" in item["limitacoes"].lower()
    for i in itens:
        for campo in ("dado", "titulo"):
            assert "vivem até 35" not in i[campo].lower()
    # nenhuma frase publicável afirma isso como fato
    assert not any("35 anos" in f["texto"] for f in casos.carregar_todos()["frases"])
