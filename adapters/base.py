"""Base dos adaptadores: lê o formato original e emite `NormalizedTextSample`.

Um adaptador NUNCA baixa dados, NUNCA funde datasets e NUNCA carrega dados pessoais de
autores/anotadores. Rótulos originais são preservados; rótulos normalizados carregam a
relação (equivalente/aproximado/incompativel) definida em `label_mapping.yaml`.
"""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Any, Iterable, Iterator

from .. import SCHEMA_VERSION, registry
from ..schema import NormalizedTextSample

ADAPTER_VERSION = "1.0.0"
csv.field_size_limit(10**9)


class EsquemaInesperado(ValueError):
    """O arquivo não tem o layout esperado pelo adaptador."""


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler_csv(caminho: Path, delimitador: str = ",") -> Iterator[dict[str, str]]:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f, delimiter=delimitador)


def colunas_csv(caminho: Path, delimitador: str = ",") -> list[str]:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f, delimiter=delimitador), [])


def para_int(valor: Any) -> int | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    if texto == "" or texto.lower() in ("nan", "none", "n/a"):
        return None
    try:
        return int(float(texto))
    except ValueError:
        return None


def intervalos_contiguos(offsets: Iterable[int]) -> list[tuple[int, int]]:
    """[5,6,7,10,11] -> [(5, 8), (10, 12)] (fim exclusivo)."""
    ordenados = sorted(set(int(o) for o in offsets))
    saida: list[tuple[int, int]] = []
    for o in ordenados:
        if saida and o == saida[-1][1]:
            saida[-1] = (saida[-1][0], o + 1)
        else:
            saida.append((o, o + 1))
    return saida


def localizar_trechos(texto: str, trechos: Iterable[str]) -> tuple[list[tuple[int, int]], list[str]]:
    """Localiza trechos no texto (sem diferenciar caixa). Retorna (intervalos, não localizados)."""
    achados: list[tuple[int, int]] = []
    perdidos: list[str] = []
    for trecho in trechos:
        t = trecho.strip().strip(";").strip()
        if not t:
            continue
        m = re.search(re.escape(t), texto, re.IGNORECASE)
        if m:
            achados.append((m.start(), m.end()))
        else:
            perdidos.append(t)
    return mesclar_intervalos(achados), perdidos


def mesclar_intervalos(intervalos: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    saida: list[tuple[int, int]] = []
    for ini, fim in sorted(intervalos):
        if saida and ini <= saida[-1][1]:
            saida[-1] = (saida[-1][0], max(saida[-1][1], fim))
        else:
            saida.append((ini, fim))
    return saida


class AdapterBase:
    dataset_id: str = ""

    def __init__(self) -> None:
        self.relatorio: dict[str, Any] = {"lidas": 0, "emitidas": 0, "descartadas": {}}

    # ---- utilidades -----------------------------------------------------------------
    def _info(self) -> dict[str, Any]:
        return registry.dataset(self.dataset_id)

    def _descartar(self, motivo: str) -> None:
        d = self.relatorio["descartadas"]
        d[motivo] = d.get(motivo, 0) + 1

    def _nova(
        self,
        sample_id: str,
        texto: str,
        *,
        plataforma: str | None,
        arquivo: str,
        linha: int | None,
        origem: str = "anotada_original",
        split: str | None = None,
        sha256: str | None = None,
    ) -> NormalizedTextSample:
        info = self._info()
        return NormalizedTextSample(
            sample_id=sample_id,
            dataset_id=self.dataset_id,
            source_platform=plataforma,
            text=texto,
            split=split,
            license=info["licenca"],
            provenance={
                "dataset_version": info["versao"],
                "adapter": type(self).__name__,
                "adapter_version": ADAPTER_VERSION,
                "schema_version": SCHEMA_VERSION,
                "taxonomy_version": registry.versao_taxonomia(),
                "mapping_version": registry.versao_mapeamento(),
                "source_file": arquivo,
                "source_sha256": sha256,
                "row_index": linha,
                "origem": origem,
            },
        )

    @staticmethod
    def _normalizar(amostra: NormalizedTextSample, dataset_id: str, original: str, valor: bool | None, politica: str, fontes: list[str] | None = None) -> None:
        """Adiciona rótulo normalizado (primeiro vence; rótulos incompatíveis ficam só no original)."""
        alvo, entrada = registry.rotulo_normalizado(dataset_id, original, valor, politica, fontes)
        if alvo is not None and alvo not in amostra.normalized_labels:
            amostra.normalized_labels[alvo] = entrada

    def amostras(self) -> Iterator[NormalizedTextSample]:  # pragma: no cover - interface
        raise NotImplementedError

    def todas(self) -> list[NormalizedTextSample]:
        return list(self.amostras())


def marcar_como_fixture(amostras: list) -> list:
    """Marca amostras geradas de fixtures sintéticas: nunca devem ser confundidas com dado real."""
    for a in amostras:
        a.provenance["origem"] = "fixture_sintetica"
        a.provenance["dataset_version"] = "fixture-sintetica (nao e o dataset real)"
        a.annotation_metadata["fixture_sintetica"] = True
    return amostras
