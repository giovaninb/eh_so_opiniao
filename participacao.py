"""Participação de visitantes: importa o que chegou pelo formulário e prepara agregados públicos.

Fluxo (nada é publicado automaticamente):
1. O site envia a frase/voto a um formulário externo (privado). Nada fica em repositório público.
2. A pessoa operadora exporta o CSV e roda `participacao importar arquivo.csv`.
3. Frases entram como Pendente, de origem `enviada_por_visitante` (NÃO publicável), já mascaradas;
   o texto original não é guardado. Votos viram só contagem por frase.
4. Revisão humana: `revisao anonimizar` reescreve a frase sem nada identificável; só então ela
   pode ser aprovada. Quem enviou nunca é identificado nem procurado.
5. `site` publica contagens de votos só de frases já publicadas e só com no mínimo `MINIMO_PARA_EXIBIR` votos.
"""

from __future__ import annotations

import csv
import hashlib
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import anonimizacao, casos
from .review import store
from .textnorm import hash_chave

MINIMO_PARA_EXIBIR = 10
AVALIACOES = ("opiniao", "discriminacao", "contexto")
TIPO_SUGERIDO = {"opiniao": "nao_discriminatoria", "discriminacao": "exclusao", "contexto": "ambigua"}
_ID_FRASE = re.compile(r"^[A-Z]{1,3}-\d{1,4}$")
_CONSENTIU = {"sim", "true", "on", "1", "yes", "aceito"}


def _chave_coluna(nome: str) -> str:
    n = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]+", "_", n).strip("_")


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _linhas(caminho: Path) -> list[dict[str, str]]:
    with Path(caminho).open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        return [{_chave_coluna(k): (v or "").strip() for k, v in linha.items() if k} for linha in leitor]


_AVALIACAO_NOVA = {
    "nao_vejo_problema": "opiniao",
    "possivel_discriminacao": "discriminacao",
    "preciso_contexto": "contexto",
}


def _avaliacao(valor: str) -> str | None:
    v = _chave_coluna(valor)
    if v in _AVALIACAO_NOVA:
        return _AVALIACAO_NOVA[v]
    for a, trecho in (("discriminacao", "discrimina"), ("opiniao", "opiniao"), ("contexto", "contexto"), ("contexto", "depende")):
        if trecho in v:
            return a
    return None


def _registrar(conn, chave: str, tipo: str, descartada: str | None = None) -> bool:
    """False se a linha já tinha sido importada."""
    if conn.execute("SELECT 1 FROM importadas WHERE chave = ?", (chave,)).fetchone():
        return False
    conn.execute("INSERT INTO importadas (chave, tipo, descartada, quando) VALUES (?,?,?,?)", (chave, tipo, descartada, _agora()))
    return True


def importar(conn, caminho: Path, modelo_ofensivo=None) -> dict[str, Any]:
    """Importa envios (CSV legado ou schema v2). Ver analytics.importar."""
    from .analytics.importar import importar as _imp
    return _imp(conn, caminho, modelo_ofensivo)


def resultados_publicos(conn, ids_publicados: set[str], minimo: int = MINIMO_PARA_EXIBIR) -> dict[str, Any]:
    """Contagens de votos só de frases já publicadas e só quando n >= minimo (evita expor poucos votos)."""
    por_frase: dict[str, Counter[str]] = {}
    for linha in conn.execute("SELECT frase_id, avaliacao FROM votos"):
        if linha["frase_id"] in ids_publicados:
            por_frase.setdefault(linha["frase_id"], Counter())[linha["avaliacao"]] += 1
    resultados = {}
    for fid, c in sorted(por_frase.items()):
        n = sum(c.values())
        if n >= minimo:
            resultados[fid] = {"n": n, **{a: c.get(a, 0) for a in AVALIACOES}}
    recebidas = conn.execute("SELECT COUNT(*) FROM itens WHERE origem IN (?,?)",
                             (store.ORIGEM_VISITANTE, store.ORIGEM_VISITANTE_ANONIMIZADA)).fetchone()[0]
    return {
        "minimo_para_exibir": minimo,
        "aviso": "Enquete informal e voluntária: não representa a população nem prova nada. Frases de visitantes só aparecem aqui depois de anonimizadas e revisadas por uma pessoa.",
        "frases_recebidas": recebidas,
        "resultados": resultados,
    }
