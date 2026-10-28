"""Esquema `NormalizedTextSample` — representação comum SEM fusão de rótulos.

Regras de projeto:
- `original_labels` guarda os rótulos exatamente como a fonte os define.
- `normalized_labels` guarda, por rótulo da taxonomia, um objeto
  `{"value": bool|None, "relation": ..., "policy": ..., "source": [...]}`.
  `value=None` significa ausência/indisponibilidade (permitida).
- Nenhum campo identifica autores ou anotadores.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

RELACOES = ("equivalente", "aproximado", "incompativel", "ausente")
ORIGENS = ("anotada_original", "aumento_sintetico", "nao_rotulada", "fixture_sintetica")


class AmostraInvalida(ValueError):
    pass


@dataclass
class NormalizedTextSample:
    sample_id: str
    dataset_id: str
    source_platform: str | None
    text: str
    original_labels: dict[str, Any] = field(default_factory=dict)
    normalized_labels: dict[str, dict[str, Any]] = field(default_factory=dict)
    annotation_metadata: dict[str, Any] = field(default_factory=dict)
    target_groups: list[str] = field(default_factory=list)
    severity: dict[str, Any] | None = None
    toxic_spans: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    split: str | None = None
    license: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def validar(self) -> "NormalizedTextSample":
        if not self.sample_id or not self.dataset_id:
            raise AmostraInvalida("sample_id e dataset_id são obrigatórios")
        if not isinstance(self.text, str) or not self.text.strip():
            raise AmostraInvalida(f"{self.sample_id}: texto vazio")
        if not self.license:
            raise AmostraInvalida(f"{self.sample_id}: licença ausente")
        origem = self.provenance.get("origem")
        if origem not in ORIGENS:
            raise AmostraInvalida(f"{self.sample_id}: provenance.origem inválida ({origem!r})")
        for nome, info in self.normalized_labels.items():
            if not isinstance(info, dict) or "value" not in info or "relation" not in info:
                raise AmostraInvalida(f"{self.sample_id}: rótulo normalizado malformado ({nome})")
            if info["relation"] not in RELACOES:
                raise AmostraInvalida(f"{self.sample_id}: relação inválida em {nome}")
            if info["value"] is not None and not isinstance(info["value"], bool):
                raise AmostraInvalida(f"{self.sample_id}: value de {nome} deve ser bool ou None")
        n = len(self.text)
        for span in self.toxic_spans:
            if not (0 <= span["start"] < span["end"] <= n):
                raise AmostraInvalida(f"{self.sample_id}: toxic_span fora do texto {span}")
        if self.split not in (None, "train", "validation", "test"):
            raise AmostraInvalida(f"{self.sample_id}: split inválido ({self.split!r})")
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> "NormalizedTextSample":
        return cls(**dados)

    def valor(self, rotulo: str) -> bool | None:
        info = self.normalized_labels.get(rotulo)
        return None if info is None else info["value"]


def escrever_jsonl(amostras: Iterable[NormalizedTextSample], destino: Path) -> int:
    destino.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with destino.open("w", encoding="utf-8") as f:
        for a in amostras:
            f.write(json.dumps(a.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
    return n


def ler_jsonl(origem: Path) -> Iterator[NormalizedTextSample]:
    with origem.open(encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                yield NormalizedTextSample.from_dict(json.loads(linha))
