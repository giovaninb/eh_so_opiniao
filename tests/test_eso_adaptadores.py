"""Adaptadores dos três datasets, testados apenas com fixtures SINTÉTICAS."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eh_so_opiniao import paths
from eh_so_opiniao.adapters import EsquemaInesperado, HateBrAdapter, OlidBrAdapter, ToldBrAdapter
from eh_so_opiniao.adapters.base import intervalos_contiguos, localizar_trechos, marcar_como_fixture

FX = paths.RAIZ / "fixtures"


# ------------------------------------------------------------------------- ToLD-Br
def test_told_preserva_votos_e_normaliza_por_maioria():
    ad = ToldBrAdapter(FX / "told_br_sintetico.csv")
    amostras = ad.todas()
    assert len(amostras) == 9 and ad.relatorio["emitidas"] == 9
    a = amostras[2]  # racismo 3 votos, insulto 1
    assert a.original_labels == {"homophobia": 0, "obscene": 0, "insult": 1, "racism": 3, "misogyny": 0, "xenophobia": 0}
    assert a.valor("racismo") is True and a.valor("insulto_hostilidade") is False  # 1/3 não é maioria
    assert a.normalized_labels["racismo"]["relation"] == "equivalente"
    assert a.normalized_labels["insulto_hostilidade"]["relation"] == "aproximado"
    assert a.target_groups == ["raca_etnia"]
    assert a.annotation_metadata["categorias_com_dissenso"] == ["insult"]
    assert a.source_platform == "twitter" and a.split is None


def test_told_politica_de_consenso_configuravel():
    contagem = {p: sum(1 for a in ToldBrAdapter(FX / "told_br_sintetico.csv", politica=p) .todas() if a.valor("linguagem_ofensiva"))
                for p in ("qualquer_voto", "maioria", "unanimidade")}
    assert contagem["qualquer_voto"] >= contagem["maioria"] >= contagem["unanimidade"]
    assert contagem["qualquer_voto"] > contagem["unanimidade"]
    with pytest.raises(ValueError):
        ToldBrAdapter(FX / "told_br_sintetico.csv", politica="inventada")


def test_told_obscene_fica_so_no_original_e_rotulo_derivado_existe():
    a = ToldBrAdapter(FX / "told_br_sintetico.csv").todas()[3]  # obscene 2 votos
    assert a.original_labels["obscene"] == 2
    assert "obscene" not in a.normalized_labels  # incompatível com a taxonomia v1
    assert a.valor("linguagem_ofensiva") is True
    assert a.normalized_labels["linguagem_ofensiva"]["policy"].startswith("qualquer categoria")


def test_told_descarta_linha_invalida(tmp_path):
    arq = tmp_path / "t.csv"
    arq.write_text("text,homophobia,obscene,insult,racism,misogyny,xenophobia\nok,0,0,0,0,0,0\nruim,9,0,0,0,0,0\n,0,0,0,0,0,0\n", encoding="utf-8")
    ad = ToldBrAdapter(arq)
    assert len(ad.todas()) == 1
    assert ad.relatorio["descartadas"] == {"votos_invalidos": 1, "texto_vazio": 1}


def test_told_esquema_inesperado(tmp_path):
    arq = tmp_path / "t.csv"
    arq.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(EsquemaInesperado):
        ToldBrAdapter(arq).todas()


# ------------------------------------------------------------------------- HateBR
def test_hatebr_binario_sem_camadas_inventadas():
    ad = HateBrAdapter(FX / "hatebr_sintetico.csv")
    amostras = ad.todas()
    assert len(amostras) == 6
    a = amostras[0]
    assert a.valor("linguagem_ofensiva") is True and a.original_labels["label_final"] == 1
    assert a.severity is None and a.target_groups == []
    assert a.annotation_metadata["camadas_indisponiveis"] == ["nivel_ofensa", "alvos_de_odio"]
    assert ad.relatorio["label_final_difere_da_maioria"] == 0
    assert set(a.normalized_labels) == {"linguagem_ofensiva"}


def test_hatebr_nao_carrega_conta_nem_url_da_publicacao():
    for a in HateBrAdapter(FX / "hatebr_sintetico.csv").todas():
        bruto = json.dumps(a.to_dict(), ensure_ascii=False)
        assert "Conta Fictícia" not in bruto and "exemplo.invalid" not in bruto
        assert len(a.context["post_group"]) == 10
    grupos = {a.context["post_group"] for a in HateBrAdapter(FX / "hatebr_sintetico.csv").todas()}
    assert len(grupos) == 3


def test_hatebrxplain_rationales_viram_offsets_derivados_e_contam_falhas():
    ad = HateBrAdapter(FX / "hatebr_sintetico.csv", FX / "hatebrxplain_sintetico.csv")
    amostras = {a.sample_id: a for a in ad.todas()}
    a1 = amostras["hatebr:1"]
    trechos = [a1.text[s["start"]:s["end"]] for s in a1.toxic_spans]
    assert any("horrível e inútil" in t for t in trechos)
    assert all(s["origin"] == "derivado_de_rationale" for s in a1.toxic_spans)
    assert a1.annotation_metadata["rationales"]["anotador_1"] == ["horrível e inútil", "só sabe atrapalhar"]
    a5 = amostras["hatebr:5"]  # "SEM VERGONHA" casa sem diferenciar caixa e se sobrepõe ao outro trecho
    assert len(a5.toxic_spans) == 1
    assert amostras["hatebr:2"].toxic_spans == []  # n/a
    assert ad.relatorio["xplain_unidas"] == 6 and ad.relatorio["xplain_sem_par"] == 0
    assert ad.relatorio["rationales_nao_localizados"] == 1
    assert ad.relatorio["xplain_texto_diferente"] == 0 and ad.relatorio["xplain_rotulo_diferente"] == 0


# ------------------------------------------------------------------------- OLID-BR
def _olid(tmp_path: Path | None = None) -> OlidBrAdapter:
    return OlidBrAdapter({"train": FX / "olid_br_sintetico_train.jsonl", "test": FX / "olid_br_sintetico_test.jsonl"})


def test_olid_preserva_offsets_originais_e_gera_intervalos():
    ad = _olid()
    amostras = {a.sample_id: a for a in ad.todas()}
    a = amostras["olid_br:o-train-1"]
    assert a.original_labels["toxic_spans"] == list(range(9, 16))
    assert a.toxic_spans == [{"start": 9, "end": 16, "origin": "anotado"}]
    assert a.text[9:16] == "canalha"
    assert a.split == "train" and amostras["olid_br:o-test-1"].split == "test"
    assert a.valor("linguagem_ofensiva") is True and a.valor("insulto_hostilidade") is True
    assert a.annotation_metadata["targeted_type"] == "IND"


def test_olid_nao_corrige_offsets_fora_do_texto_e_marca_amostra():
    ad = _olid()
    amostras = {a.sample_id: a for a in ad.todas()}
    ruim = amostras["olid_br:o-train-4"]
    assert ruim.annotation_metadata["spans_confiaveis"] is False
    assert ruim.annotation_metadata["offsets_fora_do_texto"] > 0
    assert len(ruim.original_labels["toxic_spans"]) == 25  # original intacto
    assert ad.relatorio["spans_com_offset_fora_do_texto"] == 1
    assert amostras["olid_br:o-train-1"].annotation_metadata["spans_confiaveis"] is True


def test_olid_nao_remove_espacos_do_texto_para_nao_deslocar_offsets():
    a = {x.sample_id: x for x in _olid().todas()}["olid_br:o-test-2"]
    assert a.text.startswith("  ")
    assert a.text[a.toxic_spans[0]["start"]:a.toxic_spans[0]["end"]].strip() != ""


def test_olid_alvos_de_grupo_e_ideologia_sem_inferir_pessoas():
    amostras = {a.sample_id: a for a in _olid().todas()}
    assert amostras["olid_br:o-train-3"].target_groups == ["raca_etnia"]
    assert "posicao_politica_ideologica" in amostras["olid_br:o-train-5"].target_groups
    assert amostras["olid_br:o-train-5"].valor("hostilidade_politica") is True
    assert amostras["olid_br:o-train-2"].target_groups == []


def test_olid_parquet_equivale_ao_jsonl(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    registros = [json.loads(l) for l in (FX / "olid_br_sintetico_train.jsonl").read_text(encoding="utf-8").splitlines()]
    pq.write_table(pa.Table.from_pylist(registros), tmp_path / "train.parquet")
    do_parquet = OlidBrAdapter({"train": tmp_path / "train.parquet"}).todas()
    do_jsonl = OlidBrAdapter({"train": FX / "olid_br_sintetico_train.jsonl"}).todas()
    assert [a.text for a in do_parquet] == [a.text for a in do_jsonl]
    assert [a.toxic_spans for a in do_parquet] == [a.toxic_spans for a in do_jsonl]


# ------------------------------------------------------------------------- utilidades
def test_fixtures_podem_ser_marcadas_e_nunca_passam_por_reais():
    amostras = marcar_como_fixture(ToldBrAdapter(FX / "told_br_sintetico.csv").todas())
    assert all(a.provenance["origem"] == "fixture_sintetica" for a in amostras)
    for a in amostras:
        a.validar()


def test_intervalos_e_localizacao():
    assert intervalos_contiguos([5, 6, 7, 10, 11, 5]) == [(5, 8), (10, 12)]
    achados, perdidos = localizar_trechos("Que NOJO de gente", ["nojo", "inexistente", "n/a;"])
    assert achados == [(4, 8)] and perdidos == ["inexistente", "n/a"]
