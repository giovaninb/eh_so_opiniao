"""Pares de frases ("Duas frases, uma diferença").

Os pares ficam em `casos/pares.yaml` (conteúdo editorial) e a decisão humana fica em `casos/pares_revisao.json`, escrita
só pela linha de comando (`pares aprovar`). Um par só vai ao site quando (1) uma pessoa o revisou e (2) as DUAS frases
estão publicadas. O site nunca recebe o nome de quem revisou.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from . import paths

ARQUIVO = paths.CASOS / "pares.yaml"
REVISAO = paths.CASOS / "pares_revisao.json"
CAMPOS = ("id", "titulo", "a", "b", "diferenca", "limite")


class ParInvalido(ValueError):
    pass


def carregar(caminho: Path | None = None, ids_validos: set[str] | None = None) -> list[dict[str, Any]]:
    pares = yaml.safe_load(Path(caminho or ARQUIVO).read_text(encoding="utf-8"))["pares"]
    vistos: set[str] = set()
    for p in pares:
        faltam = [c for c in CAMPOS if not str(p.get(c) or "").strip()]
        if faltam:
            raise ParInvalido(f"{p.get('id')}: campos vazios {faltam}")
        if p["id"] in vistos:
            raise ParInvalido(f"par duplicado: {p['id']}")
        vistos.add(p["id"])
        if p["a"] == p["b"]:
            raise ParInvalido(f"{p['id']}: as duas frases são a mesma")
        if ids_validos is not None and not {p["a"], p["b"]} <= ids_validos:
            raise ParInvalido(f"{p['id']}: frase inexistente na biblioteca ({p['a']}, {p['b']})")
    return pares


def revisoes(caminho: Path | None = None) -> dict[str, dict[str, str]]:
    c = Path(caminho or REVISAO)
    return json.loads(c.read_text(encoding="utf-8")) if c.exists() else {}


def aprovar(par_id: str, revisor: str, caminho: Path | None = None, ids_validos: set[str] | None = None) -> None:
    if not (revisor or "").strip():
        raise ParInvalido("informe o revisor: decisões anônimas não são aceitas")
    if par_id not in {p["id"] for p in carregar(ids_validos=ids_validos)}:
        raise ParInvalido(f"par inexistente: {par_id}")
    dados = revisoes(caminho)
    dados[par_id] = {"revisor": revisor.strip(), "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    Path(caminho or REVISAO).write_text(json.dumps(dados, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def retirar(par_id: str, caminho: Path | None = None) -> None:
    dados = revisoes(caminho)
    dados.pop(par_id, None)
    Path(caminho or REVISAO).write_text(json.dumps(dados, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def slug(par_id: str) -> str:
    return par_id.lower()


def exportar(ids_publicados: set[str], pares: list[dict[str, Any]] | None = None, revisados: set[str] | None = None) -> dict[str, Any]:
    """Pares publicáveis agora. `revisados` (para testes) substitui o arquivo de revisão."""
    pares = pares if pares is not None else carregar()
    ok = revisados if revisados is not None else set(revisoes())
    saida = [{"id": p["id"], "slug": slug(p["id"]), "titulo": p["titulo"], "a": p["a"], "b": p["b"],
              "diferenca": p["diferenca"], "limite": p["limite"]}
             for p in pares if p["id"] in ok and p["a"] in ids_publicados and p["b"] in ids_publicados]
    return {"pares": saida}
