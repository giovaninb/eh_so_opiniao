"""Caminhos do projeto. Corpora brutos ficam em um diretório local ignorado pelo Git."""

from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CATALOGO = RAIZ / "datasets"
REGISTRY = CATALOGO / "registry.yaml"
MAPPING = CATALOGO / "label_mapping.yaml"
TAXONOMIA = CATALOGO / "taxonomy.yaml"
REFERENCIAS = CATALOGO / "referencias.yaml"
DOCS = RAIZ / "docs"
SITE = RAIZ / "site"
RELATORIOS = RAIZ / "relatorios"
CASOS = RAIZ / "casos"


def dados_locais() -> Path:
    """Diretório de dados locais (brutos, normalizados, revisão). Nunca versionado.

    Pode ser trocado com a variável de ambiente ESO_DATA_DIR.
    """
    base = os.environ.get("ESO_DATA_DIR")
    return Path(base).expanduser() if base else CATALOGO / "_local"


def cache_bruto() -> Path:
    return dados_locais() / "bruto"


def normalizados() -> Path:
    return dados_locais() / "normalizado"


def pasta_revisao() -> Path:
    return dados_locais() / "revisao"


def pasta_experimentos_locais() -> Path:
    """Saídas que podem conter texto de corpora (ex.: falsos positivos). Nunca versionadas."""
    return dados_locais() / "experimentos"
