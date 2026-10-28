"""Normalização de texto usada para deduplicação e agrupamento de splits.

Não altera o texto original das amostras: serve apenas para gerar chaves de
quase-duplicata (retweets, menções, URLs, caixa e pontuação).
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_MENCAO = re.compile(r"@\w+")
_RT = re.compile(r"^\s*rt\b[:\s]*", re.IGNORECASE)
_NAO_ALNUM = re.compile(r"[^0-9a-zà-ÿ ]+")
_ESPACOS = re.compile(r"\s+")


def chave_quase_duplicata(texto: str) -> str:
    t = unicodedata.normalize("NFKC", texto or "").lower()
    t = _URL.sub(" ", t)
    t = _RT.sub("", t)
    t = _MENCAO.sub(" ", t)
    t = _NAO_ALNUM.sub(" ", t)
    return _ESPACOS.sub(" ", t).strip()


def hash_chave(texto: str) -> str:
    return hashlib.sha256(chave_quase_duplicata(texto).encode("utf-8")).hexdigest()[:16]


def hash_curto(valor: str, tamanho: int = 12) -> str:
    return hashlib.sha256(valor.encode("utf-8")).hexdigest()[:tamanho]
