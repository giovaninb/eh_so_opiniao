"""Adaptador do ToLD-Br (tweets; votos 0-3 por categoria, 3 anotadores)."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from ..schema import NormalizedTextSample
from .base import AdapterBase, EsquemaInesperado, colunas_csv, ler_csv, para_int, sha256_arquivo

CATEGORIAS = ("homophobia", "obscene", "insult", "racism", "misogyny", "xenophobia")
COLUNAS = ("text",) + CATEGORIAS
# Política de consenso configurável: nº mínimo de votos (de 3) para considerar o rótulo presente.
POLITICAS = {"qualquer_voto": 1, "maioria": 2, "unanimidade": 3}
GRUPOS_ALVO = {
    "homophobia": "orientacao_sexual_identidade_genero",
    "racism": "raca_etnia",
    "misogyny": "mulheres",
    "xenophobia": "origem_nacional_regional",
}


class ToldBrAdapter(AdapterBase):
    dataset_id = "told_br"

    def __init__(self, caminho: Path, politica: str = "maioria", calcular_hash: bool = True) -> None:
        super().__init__()
        if politica not in POLITICAS:
            raise ValueError(f"política desconhecida: {politica} (use {list(POLITICAS)})")
        self.caminho = Path(caminho)
        self.politica = politica
        self.limiar = POLITICAS[politica]
        self._sha = sha256_arquivo(self.caminho) if calcular_hash else None

    def amostras(self) -> Iterator[NormalizedTextSample]:
        presentes = colunas_csv(self.caminho)
        faltando = [c for c in COLUNAS if c not in presentes]
        if faltando:
            raise EsquemaInesperado(f"ToLD-Br: colunas ausentes {faltando}")
        for i, linha in enumerate(ler_csv(self.caminho)):
            self.relatorio["lidas"] += 1
            texto = (linha.get("text") or "").strip()
            if not texto:
                self._descartar("texto_vazio")
                continue
            votos = {c: para_int(linha.get(c)) for c in CATEGORIAS}
            if any(v is None or not 0 <= v <= 3 for v in votos.values()):
                self._descartar("votos_invalidos")
                continue
            a = self._nova(f"told_br:{i:05d}", texto, plataforma="twitter", arquivo=self.caminho.name, linha=i, sha256=self._sha)
            a.original_labels = dict(votos)
            for cat in ("homophobia", "insult", "racism", "misogyny", "xenophobia", "obscene"):
                self._normalizar(a, self.dataset_id, cat, votos[cat] >= self.limiar, f"votos>={self.limiar}/3 ({self.politica})")
            toxico = any(v >= self.limiar for v in votos.values())
            self._normalizar(
                a, self.dataset_id, "toxico_qualquer_categoria", toxico,
                f"qualquer categoria com votos>={self.limiar}/3 ({self.politica})", list(CATEGORIAS),
            )
            a.target_groups = [GRUPOS_ALVO[c] for c in GRUPOS_ALVO if votos[c] >= self.limiar]
            a.annotation_metadata = {
                "n_anotadores": 3,
                "politica_consenso": self.politica,
                "categorias_com_dissenso": [c for c, v in votos.items() if 0 < v < 3],
                "severidade": "indisponivel_na_fonte",
            }
            self.relatorio["emitidas"] += 1
            yield a.validar()
