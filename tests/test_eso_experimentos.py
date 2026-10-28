"""Experimentos A–E executados de ponta a ponta sobre corpora SINTÉTICOS (rápido, sem rede)."""

from __future__ import annotations

import json
import random

import numpy as np
import pytest

from eh_so_opiniao import paths, registry
from eh_so_opiniao.evaluation import experiments as X
from eh_so_opiniao.schema import NormalizedTextSample, escrever_jsonl

NEUTRAS = "casa rua festa trabalho cidade prefeito saude escola trânsito domingo mercado vizinho obra projeto".split()
OFENSIVAS = "idiota nojento lixo canalha inútil".split()
CLASSES = ("insulto_hostilidade", "lgbtfobia", "misoginia", "racismo", "xenofobia")
PARES = [("lula", "bolsonaro"), ("petista", "bolsonarista")]


def _rotulo(valor, relacao="aproximado"):
    return {"value": bool(valor), "relation": relacao, "policy": "sintetico", "source": ["sintetico"]}


def _gerar(ds_id: str, n: int, semente: int) -> list[NormalizedTextSample]:
    rng = random.Random(semente)
    saida = []
    for i in range(n):
        ofensivo = rng.random() < 0.5
        palavras = [rng.choice(NEUTRAS) for _ in range(6)]
        if rng.random() < 0.3:
            palavras.insert(rng.randrange(len(palavras)), rng.choice(PARES)[rng.randrange(2)])
        pos = None
        if ofensivo:
            pos = len(" ".join(palavras)) + 1
            palavras.append(rng.choice(OFENSIVAS))
        texto = " ".join(palavras) + f" doc{ds_id}{i}"
        a = NormalizedTextSample(sample_id=f"{ds_id}:{i}", dataset_id=ds_id, source_platform="sintetico", text=texto, license="sintetico",
                                 provenance={"origem": "fixture_sintetica"})
        a.normalized_labels["linguagem_ofensiva"] = _rotulo(ofensivo)
        if ds_id == "told_br":
            for c in CLASSES:
                tem = ofensivo and rng.random() < 0.35
                if tem:
                    a.text = a.text.replace(f" doc{ds_id}{i}", f" sinal{c} doc{ds_id}{i}")
                a.normalized_labels[c] = _rotulo(tem)
        if ds_id == "hatebr":
            a.context = {"post_group": f"post{i % 12}"}
        if ofensivo and ds_id == "hatebr":
            a.toxic_spans = [{"start": pos, "end": pos + len(palavras[-1]), "origin": "anotado"}]
            a.annotation_metadata["spans_confiaveis"] = True
        saida.append(a.validar())
    return saida


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("ESO_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(paths, "RELATORIOS", tmp_path / "relatorios")
    pasta = tmp_path / "normalizado"
    corpora = {ds: _gerar(ds, n, i) for i, (ds, n) in enumerate((("told_br", 900), ("hatebr", 800)))}
    for ds, am in corpora.items():
        escrever_jsonl(am, pasta / f"{ds}.jsonl")

    def limpar():
        X._bruto.cache_clear()
        X.corpus.cache_clear()
        X.treinar_ofensivo.cache_clear()

    limpar()
    yield corpora
    limpar()


def test_experimento_a_classes_de_grupo(ambiente):
    r = X.experimento_a()
    assert r["id"] == "A" and set(r["por_classe"]) == set(CLASSES)
    for classe, v in r["por_classe"].items():
        assert v["relacao_told"] in ("equivalente", "aproximado")
        assert 0 <= v["dominio_told_teste"]["f1"]["media"] <= 1
        assert len(v["positivos_treino_por_semente"]) == len(X.SEMENTES)
    assert set(r["por_classe"]["racismo"]) >= {"dominio_told_teste"} and "limite" in r  # um único dataset com classes de grupo
    assert set(r["versoes"]["sementes"]) == set(X.SEMENTES)


def test_experimento_b_compara_regras_modelos_e_chute(ambiente):
    r = X.experimento_b()
    t = r["teste_hatebr"]
    assert set(t) == {"trivial", "A_lexico", "B_lr_0.5", "B_lr_val_f1", "B_lr_precisao>=0.85", "B_svm_val_f1"}
    assert t["B_lr_val_f1"]["f1"]["media"] > t["trivial"]["f1"]["media"] - 0.05
    assert t["B_lr_val_f1"]["f1"]["media"] > 0.8  # sinal sintético forte
    assert 0 <= r["detalhes_semente_principal"]["calibracao_lr"]["ece"] <= 1
    assert r["detalhes_semente_principal"]["auditoria_splits"]["publicacoes_em_mais_de_um_split"] == 0
    assert "macro_f1" in t["B_lr_val_f1"] and "macro_f1" in r["transferencia_para_told"]["trivial"]


def test_experimento_c_matriz_e_efeito_de_combinar(ambiente):
    r = X.experimento_c()
    assert set(r["matriz_treino_x_teste"]) == {"hatebr", "told_br", "hatebr+told_br"}
    cel = r["matriz_treino_x_teste"]["hatebr"]
    assert cel["hatebr"]["em_dominio"] is True and cel["told_br"]["em_dominio"] is False
    assert len(r["efeito_de_combinar_em_dominio"]) == 2
    for g in r["efeito_de_combinar_em_dominio"]:
        assert g["delta"] == pytest.approx(g["f1_combinado"] - g["f1_referencia"], abs=1e-4)


def test_experimento_d_contrafactual_e_nao_vaza_texto(ambiente, tmp_path):
    r = X.experimento_d()
    cf = r["contrafactual"]["hatebr"]
    for grupo in ("nao_ofensivos", "ofensivos"):
        for direcao in ("esquerda_para_direita", "direita_para_esquerda"):
            x = cf[grupo][direcao]
            assert "n" in x
            if x["n"]:
                assert x["ic95_bootstrap"][0] <= x["delta_medio_assinado"] <= x["ic95_bootstrap"][1]
    # a lista com texto dos FPs fica FORA do relatório versionável
    assert (paths.pasta_experimentos_locais() / "falsos_positivos_hatebr.jsonl").exists()
    bruto = json.dumps(r, ensure_ascii=False)
    for a in ambiente["hatebr"][:50]:
        assert a.text not in bruto
    fx = r["fixtures_do_monitor"]  # arquivo do monitor não é versionado no repositório público
    if fx["disponivel"]:
        assert fx["carater"].startswith("QUALITATIVO")
        assert {c["id"] for c in fx["casos"]} >= {"SYN-001", "SYN-002", "FB-001"}
    else:
        assert fx == {"disponivel": False}


def test_experimento_e_destaque_de_trechos_supera_chute_aleatorio(ambiente):
    r = X.experimento_e()
    b, rnd = r["hatebr_teste"]["B_coeficientes_tfidf"], r["hatebr_teste"]["aleatorio_prob_0.3"]
    assert b["f1"] > rnd["f1"]
    assert r["hatebr_teste"]["tudo"]["recall"] == 1.0
    assert "causais" in r["leitura"]


def test_executar_grava_relatorios_sem_texto_de_corpora(ambiente, tmp_path):
    saida = X.executar(["a", "b", "e"])
    assert set(saida) == {"a", "b", "e"}
    for chave in saida:
        arq = paths.RELATORIOS / f"experimento_{chave}.json"
        bruto = arq.read_text(encoding="utf-8")
        assert json.loads(bruto)["id"] == chave.upper()
        for ds in ambiente.values():
            for a in ds[:80]:
                assert a.text not in bruto


# ---------------------------------------------------------------- funções puras
def test_troca_espelhada_preserva_caixa_e_so_palavras_inteiras():
    assert X._trocar("Lula e LULA e lulado", "lula", "bolsonaro") == "Bolsonaro e BOLSONARO e lulado"


def test_tokens_gold_e_metricas_de_trecho():
    texto = "voce idiota total"
    spans = [{"start": 5, "end": 11, "origin": "anotado"}]
    assert X._gold_tokens(texto, spans) == [0, 1, 0]
    a = NormalizedTextSample(sample_id="s", dataset_id="hatebr", source_platform=None, text=texto, license="x",
                             provenance={"origem": "fixture_sintetica"}, toxic_spans=spans)
    r = X._avaliar_tokens([a], lambda t: [0, 1, 1])
    assert (r["precision"], r["recall"]) == (0.5, 1.0)


def test_sobreposicao_entre_corpora_e_excluida_da_avaliacao_cruzada():
    a = NormalizedTextSample(sample_id="1", dataset_id="x", source_platform=None, text="Texto Repetido!", license="x", provenance={"origem": "fixture_sintetica"})
    b = NormalizedTextSample(sample_id="2", dataset_id="y", source_platform=None, text="outro", license="x", provenance={"origem": "fixture_sintetica"})
    mantidas, excl = X._sem_sobreposicao([a, b], X._chaves([NormalizedTextSample(sample_id="3", dataset_id="z", source_platform=None, text="texto repetido", license="x", provenance={"origem": "fixture_sintetica"})]))
    assert [m.sample_id for m in mantidas] == ["2"] and excl == 1
