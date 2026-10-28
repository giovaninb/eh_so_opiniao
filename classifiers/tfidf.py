"""Baseline B — TF-IDF + regressão logística ou SVM linear (scikit-learn).

Simples de propósito: reproduzível, rápido e interpretável (coeficientes por termo). Todos
os hiperparâmetros e a semente ficam registrados em `descricao()` para o relatório.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

VERSAO = "tfidf-1.0.0"


def _prep(texto: str) -> str:
    return (texto or "").replace("\n", " ")


class TfidfBaseline:
    nome = "B_tfidf"
    versao = VERSAO

    def __init__(self, modelo: str = "lr", c: float = 1.0, semente: int = 42,
                 max_features_palavra: int = 100_000, max_features_char: int = 150_000) -> None:
        if modelo not in ("lr", "svm"):
            raise ValueError("modelo deve ser 'lr' ou 'svm'")
        self.modelo = modelo
        self.c = c
        self.semente = semente
        self.vetor_palavra = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                                             max_features=max_features_palavra, strip_accents="unicode",
                                             token_pattern=r"(?u)\b\w+\b")
        self.vetor_char = TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                                          sublinear_tf=True, max_features=max_features_char, strip_accents="unicode")
        self.clf = (LogisticRegression(C=c, class_weight="balanced", max_iter=2000, solver="liblinear", random_state=semente)
                    if modelo == "lr" else LinearSVC(C=c, class_weight="balanced", random_state=semente))
        self._ajustado = False
        self._vetores_prontos = False

    def _matriz(self, textos: Sequence[str], ajustar: bool):
        t = [_prep(x) for x in textos]
        if ajustar:
            return hstack([self.vetor_palavra.fit_transform(t), self.vetor_char.fit_transform(t)]).tocsr()
        return hstack([self.vetor_palavra.transform(t), self.vetor_char.transform(t)]).tocsr()

    def transformar(self, textos: Sequence[str]):
        """Matriz TF-IDF com os vetores JÁ ajustados (reutilizável entre classes)."""
        return self._matriz(textos, ajustar=False)

    def ajustar_vetores(self, textos: Sequence[str]):
        """Ajusta os vetores TF-IDF no treino e devolve a matriz de treino."""
        X = self._matriz(textos, ajustar=True)
        self._vetores_prontos = True
        return X

    def compartilhar_vetores(self, outro: "TfidfBaseline") -> "TfidfBaseline":
        self.vetor_palavra, self.vetor_char = outro.vetor_palavra, outro.vetor_char
        self._vetores_prontos = True
        return self

    def ajustar(self, textos: Sequence[str], y: Sequence[int], X=None) -> "TfidfBaseline":
        if X is None:
            X = self.transformar(textos) if self._vetores_prontos else self.ajustar_vetores(textos)
        self.clf.fit(X, np.asarray(y, dtype=int))
        self._ajustado = True
        return self

    def pontuar(self, textos: Sequence[str], X=None) -> np.ndarray:
        """Pontuação contínua (probabilidade para LR; margem para SVM)."""
        X = self.transformar(textos) if X is None else X
        if self.modelo == "lr":
            return self.clf.predict_proba(X)[:, 1]
        return self.clf.decision_function(X)

    def prever(self, textos: Sequence[str], limiar: float | None = None) -> np.ndarray:
        s = self.pontuar(textos)
        corte = (0.5 if self.modelo == "lr" else 0.0) if limiar is None else limiar
        return (s >= corte).astype(int)

    def coeficientes_palavra(self) -> dict[str, float]:
        """Coeficiente por unigrama (para destaque de trechos). Só usa as colunas de palavras."""
        nomes = self.vetor_palavra.get_feature_names_out()
        coef = self.clf.coef_[0][: len(nomes)]
        return {n: float(c) for n, c in zip(nomes, coef) if " " not in n}

    def descricao(self) -> dict[str, Any]:
        import sklearn
        return {"nome": self.nome, "versao": self.versao, "modelo": self.modelo, "C": self.c, "semente": self.semente,
                "class_weight": "balanced", "ngramas_palavra": [1, 2], "ngramas_char_wb": [3, 5],
                "sklearn": sklearn.__version__, "numpy": np.__version__}
