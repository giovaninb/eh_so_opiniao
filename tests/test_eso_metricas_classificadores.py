"""Métricas calculadas à mão e baselines A/B/C."""

from __future__ import annotations

import numpy as np
import pytest

from eh_so_opiniao.classifiers import transformer
from eh_so_opiniao.classifiers.rules import COBERTURA, RegrasBaseline
from eh_so_opiniao.classifiers.tfidf import TfidfBaseline
from eh_so_opiniao.evaluation import metrics as M


def test_metricas_binarias_valores_conhecidos():
    yt = [1, 1, 1, 0, 0, 0, 0, 0]
    yp = [1, 1, 0, 1, 0, 0, 0, 0]
    m = M.metricas_binarias(yt, yp)
    assert m["confusao"] == {"tp": 2, "fp": 1, "fn": 1, "tn": 4}
    assert m["precision"] == pytest.approx(0.6667, abs=1e-4) and m["recall"] == pytest.approx(0.6667, abs=1e-4)
    assert m["f1"] == pytest.approx(0.6667, abs=1e-4)
    assert m["f1_classe_negativa"] == pytest.approx(0.8, abs=1e-4)
    assert m["macro_f1"] == pytest.approx((0.6667 + 0.8) / 2, abs=1e-3)
    assert m["suporte_insuficiente"] is True  # só 3 positivos


def test_suporte_insuficiente_e_divisao_por_zero():
    m = M.metricas_binarias([0, 0, 0], [0, 0, 0])
    assert m["f1"] == 0.0 and m["recall"] == 0.0 and m["suporte_positivos"] == 0
    grande = M.metricas_binarias([1] * 40 + [0] * 40, [1] * 40 + [0] * 40)
    assert grande["suporte_insuficiente"] is False and grande["f1"] == 1.0


def test_chute_trivial_tem_macro_f1_baixo_quando_ha_desequilibrio():
    yt = [1] * 85 + [0] * 15
    m = M.metricas_binarias(yt, [1] * 100)
    assert m["f1"] > 0.9 and m["macro_f1"] < 0.5  # F1 sozinho engana; macro-F1 expõe


def test_macro_f1_ignora_instaveis_quando_pedido():
    por_classe = {"a": {"f1": 0.9, "suporte_insuficiente": False}, "b": {"f1": 0.1, "suporte_insuficiente": True}}
    assert M.macro_f1(por_classe) == 0.5 and M.macro_f1(por_classe, ignorar_instaveis=True) == 0.9


def test_curva_pr_e_calibracao():
    yt = np.array([0, 0, 1, 1, 0, 1, 1, 0] * 10)
    score = np.where(yt == 1, 0.8, 0.2)
    curva = M.curva_pr(yt, score)
    assert curva["average_precision"] == 1.0 and curva["pontos"]
    cal = M.calibracao(yt, score)
    assert cal["aplicavel"] and 0 <= cal["ece"] <= 1 and cal["brier"] == pytest.approx(0.04, abs=1e-6)
    assert M.calibracao(yt, score * 10)["aplicavel"] is False  # não é probabilidade
    assert M.curva_pr([0, 0], [0.1, 0.2])["average_precision"] is None


def test_limiar_escolhido_so_com_dados_de_validacao():
    yv = np.array([0, 0, 0, 1, 1, 1] * 5)
    sv = np.array([0.1, 0.2, 0.45, 0.55, 0.8, 0.9] * 5)
    r = M.escolher_limiar(yv, sv, "f1")
    assert 0.45 < r["limiar"] <= 0.55 and r["f1_val"] == 1.0
    p = M.escolher_limiar(yv, sv * 0.1 + 0.4, "precisao", 0.99)
    assert p["limiar"] is not None
    assert M.escolher_limiar([1, 1], [0.1, 0.9])["limiar"] is None


def test_ids_de_erro_e_media_desvio():
    e = M.ids_de_erro(["a", "b", "c", "d"], [1, 0, 1, 0], [0, 1, 1, 0])
    assert e == {"falsos_positivos": ["b"], "falsos_negativos": ["a"]}
    assert M.media_e_desvio([0.5, 0.7])["media"] == 0.6 and M.media_e_desvio([])["n"] == 0


# ------------------------------------------------------------------ baseline A
def test_baseline_a_declara_o_que_nao_cobre_e_nao_inventa():
    a = RegrasBaseline()
    d = a.descricao()
    assert {"racismo", "xenofobia", "misoginia", "lgbtfobia"} == set(d["nao_cobre"])
    assert not (COBERTURA & {"racismo", "xenofobia", "misoginia", "lgbtfobia"})
    pred = a.prever("Que pessoa idiota")
    assert pred["linguagem_ofensiva"] is True
    assert a.prever("Discordo da proposta apresentada")["linguagem_ofensiva"] is False


def test_baseline_a_nao_trata_acusacao_como_ofensa_lexical():
    assert RegrasBaseline().termos_encontrados("Ele é um corrupto e ladrão segundo a denúncia") == []


def test_baseline_a_neutralidade_partidaria_espelhada():
    a = RegrasBaseline()
    for esq, dir_ in (("Sou dono da empresa e não contrato petistas.", "Sou dono da empresa e não contrato eleitores do PL."),
                      ("Quem vota nesse partido é burro", "Quem vota nesse partido é burro")):
        assert a.prever(esq) == a.prever(dir_)
    assert a.prever("Sou dono da empresa e não contrato petistas.")["possivel_assedio_eleitoral_contextual"] is True


# ------------------------------------------------------------------ baseline B
TEXTOS = ["que pessoa idiota e nojenta", "ótimo trabalho parabéns", "lixo de gente inútil", "boa tarde a todos",
          "você é um canalha", "concordo com a proposta", "idiota total sem vergonha", "obrigado pela atenção"] * 6
ROTULOS = [1, 0, 1, 0, 1, 0, 1, 0] * 6


@pytest.mark.parametrize("modelo", ["lr", "svm"])
def test_baseline_b_aprende_e_e_reprodutivel(modelo):
    a = TfidfBaseline(modelo=modelo, semente=1).ajustar(TEXTOS, ROTULOS)
    b = TfidfBaseline(modelo=modelo, semente=1).ajustar(TEXTOS, ROTULOS)
    teste = ["que idiota inútil", "parabéns pelo ótimo trabalho"]
    assert list(a.prever(teste)) == [1, 0]
    assert np.allclose(a.pontuar(teste), b.pontuar(teste))
    d = a.descricao()
    assert d["semente"] == 1 and d["modelo"] == modelo and "sklearn" in d


def test_baseline_b_reutiliza_vetores_entre_classes():
    base = TfidfBaseline()
    X = base.ajustar_vetores(TEXTOS)
    c1 = TfidfBaseline().compartilhar_vetores(base).ajustar(None, ROTULOS, X)
    c2 = TfidfBaseline().compartilhar_vetores(base).ajustar(None, [1 - y for y in ROTULOS], X)
    s1, s2 = c1.pontuar(["idiota"]), c2.pontuar(["idiota"])
    assert s1[0] > 0.5 > s2[0]
    assert "idiota" in c1.coeficientes_palavra()


def test_baseline_b_rejeita_modelo_desconhecido():
    with pytest.raises(ValueError):
        TfidfBaseline(modelo="xgboost")


# ------------------------------------------------------------------ baseline C
def test_baseline_c_e_apenas_plano_e_falha_com_clareza():
    p = transformer.plano()
    assert p["executado"] is False and "bert-base-portuguese-cased" in " ".join(p["modelos_candidatos"])
    if not transformer.disponivel():
        with pytest.raises(transformer.DependenciaAusente):
            transformer.EmbeddingsCongelados()
