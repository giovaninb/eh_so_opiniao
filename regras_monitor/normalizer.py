# CÓPIA CONGELADA de monitor/processing/normalizer.py (monitor de assédio eleitoral).
# Existe para que o repositório É Só Opinião? funcione sozinho. Regras auditáveis usadas só como
# hipótese no Baseline A. tests/test_regras_monitor_copia.py compara com o original quando presente.
from __future__ import annotations

import re
import unicodedata


def norm(text: str | None) -> str:
    """Minúsculas, sem acentos e com espaços colapsados. Texto vazio permanece vazio."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text.casefold())
    sem_acento = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).strip()


def normalizar_item(texto: str | None) -> str:
    item = norm(texto)
    item = re.sub(r"^[\-\*\u2022]+", "", item)
    item = re.sub(r"^\d{1,3}[.)]\s*", "", item)
    return item.strip(" .;:-")
