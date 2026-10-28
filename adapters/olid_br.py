"""Adaptador do OLID-BR (parquet do Hugging Face `dougtrajano/olid-br`).

- Preserva `toxic_spans` como lista original de offsets de caracteres (em `original_labels`)
  e também como intervalos contíguos `[start, end)` (em `toxic_spans`).
- Offsets fora do texto não são "consertados": são contados no relatório e descartados dos
  intervalos normalizados (o original continua intacto).
- Aceita .parquet (requer pyarrow) ou .jsonl com as mesmas colunas (fixtures).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from ..schema import NormalizedTextSample
from .base import AdapterBase, EsquemaInesperado, intervalos_contiguos, sha256_arquivo

CATEGORIAS = ("health", "ideology", "insult", "lgbtqphobia", "other_lifestyle", "physical_aspects",
              "profanity_obscene", "racism", "religious_intolerance", "sexism", "xenophobia")
COLUNAS = ("id", "text", "is_offensive", "is_targeted", "targeted_type", "toxic_spans") + CATEGORIAS
GRUPOS_ALVO = {
    "racism": "raca_etnia", "sexism": "genero", "lgbtqphobia": "orientacao_sexual_identidade_genero",
    "xenophobia": "origem_nacional_regional", "religious_intolerance": "religiao",
    "ideology": "posicao_politica_ideologica", "health": "saude", "physical_aspects": "aspecto_fisico",
    "other_lifestyle": "estilo_de_vida",
}
# Rótulos com alvo na taxonomia emitidos como normalizados.
NORMALIZADOS = ("insult", "racism", "sexism", "lgbtqphobia", "xenophobia", "ideology")


def _ler_registros(caminho: Path) -> list[dict[str, Any]]:
    if caminho.suffix == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError as erro:  # pragma: no cover
            raise RuntimeError("OLID-BR em parquet exige pyarrow (requirements.txt)") from erro
        return pq.read_table(caminho).to_pylist()
    with caminho.open(encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


class OlidBrAdapter(AdapterBase):
    dataset_id = "olid_br"

    def __init__(self, arquivos: dict[str, Path], calcular_hash: bool = True) -> None:
        """`arquivos`: {"train": caminho, "test": caminho} (split original preservado)."""
        super().__init__()
        self.arquivos = {k: Path(v) for k, v in arquivos.items()}
        self.calcular_hash = calcular_hash
        self.relatorio.update({"spans_com_offset_fora_do_texto": 0, "spans_vazios_em_ofensivo": 0})

    def amostras(self) -> Iterator[NormalizedTextSample]:
        for split, caminho in self.arquivos.items():
            sha = sha256_arquivo(caminho) if self.calcular_hash else None
            registros = _ler_registros(caminho)
            if registros:
                faltando = [c for c in COLUNAS if c not in registros[0]]
                if faltando:
                    raise EsquemaInesperado(f"OLID-BR: colunas ausentes {faltando}")
            for i, r in enumerate(registros):
                self.relatorio["lidas"] += 1
                texto = r.get("text") or ""  # sem strip: offsets são relativos ao texto original
                if not texto.strip():
                    self._descartar("texto_vazio")
                    continue
                if r["is_offensive"] not in ("OFF", "NOT"):
                    self._descartar("is_offensive_invalido")
                    continue
                yield self._converter(r, texto, split, caminho.name, i, sha)

    def _converter(self, r: dict[str, Any], texto: str, split: str, arquivo: str, i: int, sha: str | None) -> NormalizedTextSample:
        a = self._nova(f"olid_br:{r['id']}", texto, plataforma="nao_informada_por_registro", arquivo=arquivo, linha=i, split=split, sha256=sha)
        offsets = [int(o) for o in (r.get("toxic_spans") or [])]
        a.original_labels = {k: r.get(k) for k in COLUNAS if k not in ("id", "text")}
        a.original_labels["toxic_spans"] = offsets
        ofensivo = r["is_offensive"] == "OFF"
        self._normalizar(a, self.dataset_id, "is_offensive", ofensivo, "rotulo_original")
        for cat in NORMALIZADOS:
            self._normalizar(a, self.dataset_id, cat, bool(r.get(cat)), "rotulo_original")
        if ofensivo:
            a.target_groups = [g for c, g in GRUPOS_ALVO.items() if r.get(c)]
        validos = [o for o in offsets if 0 <= o < len(texto)]
        if len(validos) != len(offsets):
            self.relatorio["spans_com_offset_fora_do_texto"] += 1
        a.toxic_spans = [{"start": s, "end": e, "origin": "anotado"} for s, e in intervalos_contiguos(validos)]
        if ofensivo and not a.toxic_spans:
            self.relatorio["spans_vazios_em_ofensivo"] += 1
        a.annotation_metadata = {
            "is_targeted": r.get("is_targeted"),
            "targeted_type": r.get("targeted_type"),
            "apoio_perspective_api": "segundo o cartão do dataset",
            "offsets": "indices de caractere do texto original",
            # offsets fora do texto indicam spans anotados sobre uma versão ligeiramente
            # diferente do texto: não são corrigidos, e a amostra sai da avaliação de spans.
            "offsets_fora_do_texto": len(offsets) - len(validos),
            "spans_confiaveis": len(validos) == len(offsets),
        }
        self.relatorio["emitidas"] += 1
        return a.validar()
