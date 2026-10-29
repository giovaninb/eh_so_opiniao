"""NX-001..NX-247: exemplos do catálogo consolidado que vieram sem metadados. Os metadados são PROPOSTA (gerada por regras
revisáveis) e tudo entra Pendente; id, leitura, tema e texto não mudam."""

from __future__ import annotations

import csv
import json
from collections import Counter

import pytest

from eh_so_opiniao import casos, expansao, paths, publicacao, registry
from eh_so_opiniao.review import store

ARQ = paths.CASOS / "catalogo_anterior_nx001_247.jsonl"
CSV_CONSOLIDADO = paths.RAIZ.parent / "expansao_genero_idadismo_religiao_trans" / "catalogo_completo_atualizado.csv"


@pytest.fixture(scope="module")
def antigos():
    return expansao.carregar(ARQ)["frases"]


def test_247_registros_com_ids_nx001_a_nx247_sem_lacuna_nem_duplicata(antigos):
    ids = [f["id"] for f in antigos]
    assert ids == [f"NX-{i:03d}" for i in range(1, 248)]


@pytest.mark.skipif(not CSV_CONSOLIDADO.exists(), reason="CSV consolidado fora do repositório")
def test_id_leitura_tema_e_texto_batem_com_o_catalogo_consolidado():
    with CSV_CONSOLIDADO.open(encoding="utf-8-sig", newline="") as fh:
        base = {r["id"]: r for r in csv.DictReader(fh) if r["id"].startswith("NX-") and int(r["id"][3:]) <= 247}
    registros = [json.loads(l) for l in ARQ.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(registros) == len(base) == 247
    for r in registros:
        o = base[r["id"]]
        assert (r["leitura"], r["tema"], r["texto"]) == (o["leitura"], o["tema"], o["texto"]), r["id"]


def test_todos_pendentes_e_nao_publicaveis_com_origem_declarada_como_nao_documentada():
    for l in ARQ.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        assert r["estado_revisao"] == "Pendente" and r["pode_publicar"] is False
        assert "sem_metadados" in r["origem"] and r["metadados_propostos"]  # a lacuna de origem não é escondida


def test_dimensoes_validas_e_sem_incitacao(antigos):
    ids_grupo = {g["id"] for g in expansao.grupos()}
    for f in antigos:
        d = f["dimensoes"]
        assert d["gravidade"] in expansao.GRAVIDADES and d["gravidade"] != "incitacao_violencia"
        assert d["grupo"] is None or d["grupo"] in ids_grupo
        assert (f["tipo"] == "exclusao") == (d["gravidade"] != "nao_se_aplica"), f["id"]
        assert d["mecanismo"] and d["certeza_rotulo"] in expansao.CERTEZAS
        assert f["subtema"] and f["mecanismo"]


def test_contagens_por_leitura_e_tema(antigos):
    assert Counter(f["tipo"] for f in antigos) == {"exclusao": 183, "ambigua": 30, "nao_discriminatoria": 34}
    por_tema = Counter(f["tema"] for f in antigos)
    assert por_tema == {"capacitismo": 69, "sem_discriminacao": 34, "racismo": 30, "estigma_nao_monogamia": 29, "lgbtfobia": 28,
                        "misoginia": 27, "depende_contexto": 26, "ironia": 4}


def test_ironia_vira_ambigua_e_nao_discriminacao(antigos):
    for f in (x for x in antigos if x["tema"] == "ironia"):
        assert f["tipo"] == "ambigua" and "ironia_humor" in f["rotulos_editoriais"] and f["muda_se"]


def test_controles_nao_recebem_rotulo_de_discriminacao(antigos):
    controles = [f for f in antigos if f["tipo"] == "nao_discriminatoria"]
    assert len(controles) == 34 and all(f["rotulos_editoriais"] == [] for f in controles)


def test_novo_tema_e_nova_classe_exploratoria_sem_rotulo_mapeado():
    assert "estigma_nao_monogamia" in {t["id"] for t in casos.temas()}
    tax = registry.carregar_taxonomia()
    assert tax["estigma_nao_monogamia"]["tipo"] == "exploratorio"
    assert "estigma_nao_monogamia" not in {c.alvo for c in registry.correspondencias()}
    assert "infidelidade" in tax["estigma_nao_monogamia"]["nao_e"].lower()


def test_contexto_decide_bissexualidade_trans_e_nao_monogamia(antigos):
    m = {f["id"]: f for f in antigos}
    assert m["NX-126"]["tipo"] == "ambigua" and m["NX-127"]["tipo"] == "ambigua"      # pergunta sobre bissexualidade
    assert m["NX-036"]["tipo"] == "exclusao" and m["NX-036"]["dimensoes"]["grupo"] == "pessoas_lgbt"
    assert m["NX-054"]["dimensoes"]["grupo"] == "pessoas_trans" and "transfobia" in m["NX-054"]["rotulos_editoriais"]
    assert m["NX-235"]["tipo"] == "ambigua" and m["NX-241"]["tipo"] == "nao_discriminatoria"   # preferência pessoal pela monogamia
    assert m["NX-247"]["tipo"] == "nao_discriminatoria" and "traição" in m["NX-247"]["texto"].lower()  # traição ≠ formato da relação
    assert m["NX-143"]["tipo"] == "nao_discriminatoria" and "bombril" in m["NX-143"]["texto"]  # citação crítica de um termo, sem endosso
    assert not m["NX-143"]["aviso_conteudo"] or m["NX-143"]["tipo"] != "exclusao"


def test_termos_pejorativos_levam_aviso_e_controles_nao(antigos):
    comaviso = {f["id"] for f in antigos if f["aviso_conteudo"]}
    assert comaviso == {"NX-007", "NX-008", "NX-010", "NX-013", "NX-016", "NX-207", "NX-208"}
    assert all(f["tipo"] == "exclusao" for f in antigos if f["aviso_conteudo"])


def test_importacao_total_592_idempotente_e_tudo_novo_pendente(tmp_path):
    conn = store.abrir(tmp_path / "r.sqlite3")
    try:
        r = casos.enfileirar(conn)
        assert r == {"total": 592, "novos": 592}
        assert casos.enfileirar(conn)["novos"] == 0
        assert {l["estado"] for l in store.listar(conn) if l["id"].startswith("NX-")} == {"Pendente"}
        assert not any(f["id"].startswith("NX-") for f in publicacao.exportar_frases(conn)["frases"])
    finally:
        conn.close()


def test_grupos_novos_aparecem_para_frases_antigas_ja_publicadas():
    assert expansao.grupo_de("racismo") == "raca_e_povos_indigenas"
    assert expansao.grupo_de("capacitismo") == "pessoas_com_deficiencia"
    assert expansao.grupo_de("estigma_nao_monogamia") == "relacoes_nao_monogamicas"
