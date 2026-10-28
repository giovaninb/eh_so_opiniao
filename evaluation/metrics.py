"""Métricas de avaliação. Nenhum número é inventado: tudo é calculado de y_true/y_score.

Convenções:
- Classe positiva = 1. Suporte pequeno é sinalizado (`suporte_insuficiente`) em vez de
  escondido: com poucos positivos, P/R/F1 são instáveis e não devem ser interpretados.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, precision_recall_curve

MIN_POSITIVOS = 30  # abaixo disso a métrica é marcada como instável


def _div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def matriz_confusao(y_true: Sequence[int], y_pred: Sequence[int]) -> dict[str, int]:
    yt, yp = np.asarray(y_true, dtype=int), np.asarray(y_pred, dtype=int)
    return {
        "tp": int(((yt == 1) & (yp == 1)).sum()), "fp": int(((yt == 0) & (yp == 1)).sum()),
        "fn": int(((yt == 1) & (yp == 0)).sum()), "tn": int(((yt == 0) & (yp == 0)).sum()),
    }


def metricas_binarias(y_true: Sequence[int], y_pred: Sequence[int]) -> dict[str, Any]:
    c = matriz_confusao(y_true, y_pred)
    p = _div(c["tp"], c["tp"] + c["fp"])
    r = _div(c["tp"], c["tp"] + c["fn"])
    f1 = _div(2 * p * r, p + r)
    pn, rn = _div(c["tn"], c["tn"] + c["fn"]), _div(c["tn"], c["tn"] + c["fp"])
    f1_neg = _div(2 * pn * rn, pn + rn)
    positivos = c["tp"] + c["fn"]
    return {
        "precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4),
        "f1_classe_negativa": round(f1_neg, 4), "macro_f1": round((f1 + f1_neg) / 2, 4),
        "suporte_positivos": positivos, "suporte_total": sum(c.values()),
        "confusao": c, "suporte_insuficiente": positivos < MIN_POSITIVOS,
        "taxa_falso_positivo": round(_div(c["fp"], c["fp"] + c["tn"]), 4),
        "taxa_falso_negativo": round(_div(c["fn"], c["fn"] + c["tp"]), 4),
    }


def macro_f1(por_classe: dict[str, dict[str, Any]], ignorar_instaveis: bool = False) -> float | None:
    valores = [m["f1"] for m in por_classe.values() if not (ignorar_instaveis and m["suporte_insuficiente"])]
    return round(float(np.mean(valores)), 4) if valores else None


def curva_pr(y_true: Sequence[int], y_score: Sequence[float], max_pontos: int = 25) -> dict[str, Any]:
    yt = np.asarray(y_true, dtype=int)
    if yt.sum() == 0:
        return {"average_precision": None, "pontos": []}
    p, r, t = precision_recall_curve(yt, np.asarray(y_score, dtype=float))
    idx = np.unique(np.linspace(0, len(t) - 1, num=min(max_pontos, len(t))).astype(int)) if len(t) else []
    return {
        "average_precision": round(float(average_precision_score(yt, y_score)), 4),
        "pontos": [{"limiar": round(float(t[i]), 4), "precision": round(float(p[i]), 4), "recall": round(float(r[i]), 4)} for i in idx],
    }


def calibracao(y_true: Sequence[int], y_prob: Sequence[float], n_bins: int = 10) -> dict[str, Any]:
    """Brier e ECE (só faz sentido para probabilidades, ex.: regressão logística)."""
    yt, yp = np.asarray(y_true, dtype=int), np.asarray(y_prob, dtype=float)
    if len(yt) == 0 or yp.min() < 0 or yp.max() > 1:
        return {"aplicavel": False}
    bins = np.linspace(0, 1, n_bins + 1)
    ece, tabela = 0.0, []
    for i in range(n_bins):
        m = (yp >= bins[i]) & ((yp < bins[i + 1]) if i < n_bins - 1 else (yp <= bins[i + 1]))
        if not m.any():
            continue
        conf, acc = float(yp[m].mean()), float(yt[m].mean())
        ece += m.mean() * abs(conf - acc)
        tabela.append({"faixa": [round(bins[i], 2), round(bins[i + 1], 2)], "n": int(m.sum()),
                       "prob_media": round(conf, 4), "fracao_positiva": round(acc, 4)})
    return {"aplicavel": True, "brier": round(float(brier_score_loss(yt, yp)), 4), "ece": round(float(ece), 4), "confiabilidade": tabela}


def escolher_limiar(y_true: Sequence[int], y_score: Sequence[float], criterio: str = "f1", precisao_minima: float = 0.8) -> dict[str, Any]:
    """Escolhe limiar NA VALIDAÇÃO (nunca no teste).

    criterio="f1": maximiza F1. criterio="precisao": maior recall com precisão >= precisao_minima
    (útil quando falso positivo é caro, caso do observatório).
    """
    yt, ys = np.asarray(y_true, dtype=int), np.asarray(y_score, dtype=float)
    if yt.sum() == 0 or yt.sum() == len(yt):
        return {"limiar": None, "motivo": "validação sem as duas classes"}
    p, r, t = precision_recall_curve(yt, ys)
    p, r = p[:-1], r[:-1]
    f1 = np.where((p + r) > 0, 2 * p * r / np.maximum(p + r, 1e-12), 0)
    if criterio == "precisao":
        ok = np.where(p >= precisao_minima)[0]
        if len(ok) == 0:
            return {"limiar": None, "motivo": f"nenhum limiar atinge precisão {precisao_minima}"}
        i = ok[np.argmax(r[ok])]
    else:
        i = int(np.argmax(f1))
    return {"limiar": round(float(t[i]), 6), "criterio": criterio, "precision_val": round(float(p[i]), 4),
            "recall_val": round(float(r[i]), 4), "f1_val": round(float(f1[i]), 4)}


def ids_de_erro(ids: Sequence[str], y_true: Sequence[int], y_pred: Sequence[int]) -> dict[str, list[str]]:
    yt, yp = np.asarray(y_true), np.asarray(y_pred)
    return {
        "falsos_positivos": [i for i, a, b in zip(ids, yt, yp) if a == 0 and b == 1],
        "falsos_negativos": [i for i, a, b in zip(ids, yt, yp) if a == 1 and b == 0],
    }


def media_e_desvio(valores: Sequence[float]) -> dict[str, float | None]:
    v = [x for x in valores if x is not None]
    if not v:
        return {"media": None, "desvio": None, "n": 0}
    return {"media": round(float(np.mean(v)), 4), "desvio": round(float(np.std(v, ddof=0)), 4), "n": len(v)}
