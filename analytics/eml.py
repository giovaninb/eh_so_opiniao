"""Leitura heurística de notificações .eml (Formspree envia e-mail no plano Free).

Não há exemplo real versionado: o parser aceita pares chave/valor, JSON e
formulário URL-encoded. Se o formato não for reconhecido, a importação marca
o arquivo como inválido em vez de inventar campos.
"""

from __future__ import annotations

import email
import json
import re
from email import policy
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

_PAR = re.compile(r"^([A-Za-z][A-Za-z0-9_-]{1,40})\s*[:=]\s*(.*)$")


def ler_eml(caminho: Path) -> list[dict[str, str]]:
    msg = email.message_from_bytes(Path(caminho).read_bytes(), policy=policy.default)
    textos: list[str] = []
    if msg.is_multipart():
        for parte in msg.walk():
            tipo = parte.get_content_type()
            if tipo in ("text/plain", "text/html"):
                try:
                    textos.append(parte.get_content())
                except Exception:
                    continue
    else:
        try:
            textos.append(msg.get_content())
        except Exception:
            textos.append(str(msg.get_payload() or ""))
    corpo = "\n".join(textos)
    campos = _extrair(corpo)
    if not campos:
        raise ValueError("não foi possível reconhecer campos na mensagem .eml")
    return [campos]


def _extrair(corpo: str) -> dict[str, str]:
    bruto = (corpo or "").strip()
    if not bruto:
        return {}
    if bruto.startswith("{") and bruto.endswith("}"):
        try:
            obj = json.loads(bruto)
            if isinstance(obj, dict):
                return {str(k): "" if v is None else (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)) for k, v in obj.items()}
        except json.JSONDecodeError:
            pass
    if "=" in bruto and "&" in bruto and "\n" not in bruto[:200]:
        qs = parse_qs(bruto, keep_blank_values=True)
        return {k: (v[0] if v else "") for k, v in qs.items()}
    campos: dict[str, str] = {}
    linhas = [re.sub(r"<[^>]+>", " ", ln).strip() for ln in bruto.replace("\r\n", "\n").split("\n")]
    i = 0
    while i < len(linhas):
        ln = linhas[i]
        m = _PAR.match(ln)
        if m:
            campos[m.group(1).lower()] = m.group(2).strip()
            i += 1
            continue
        if ln and i + 1 < len(linhas) and linhas[i + 1] and not _PAR.match(linhas[i + 1]) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,40}", ln):
            campos[ln.lower()] = linhas[i + 1]
            i += 2
            continue
        i += 1
    return campos
