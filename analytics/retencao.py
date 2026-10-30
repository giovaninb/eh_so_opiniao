"""Retenção local: relatórios agregados podem ficar; textos originais não precisam.

Não envia nada a CI, GitHub Actions nem repositório público.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .importar import ler_arquivo_local, pasta_arquivo
from .relatorios import gerar

CAMPOS_TEXTO = ("frase", "comentario", "contexto")


def _parse_data(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def aplicar(dias: int = 90, destino: Path | None = None) -> dict[str, Any]:
    """Remove ou esvazia textos originais mais antigos que `dias`. Mantém estrutura para agregados."""
    pasta = pasta_arquivo()
    arq = pasta / "submissoes.jsonl"
    if not arq.exists():
        return {"lidas": 0, "expurgadas": 0, "mantidas": 0}
    limite = datetime.now(timezone.utc) - timedelta(days=max(1, dias))
    lidas = expurgadas = mantidas = 0
    saida = []
    for rec in ler_arquivo_local():
        lidas += 1
        quando = _parse_data(str(rec.get("recebido_em") or rec.get("importado_em") or ""))
        if quando and quando.tzinfo is None:
            quando = quando.replace(tzinfo=timezone.utc)
        if quando and quando < limite:
            for k in CAMPOS_TEXTO:
                if rec.get(k):
                    rec[k] = ""
            rec["_texto_expurgado"] = True
            expurgadas += 1
        else:
            mantidas += 1
        saida.append(rec)
    tmp = arq.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for rec in saida:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    tmp.replace(arq)
    gerar(destino)
    return {"lidas": lidas, "expurgadas": expurgadas, "mantidas": mantidas}
