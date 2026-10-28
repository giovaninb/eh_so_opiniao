"""Estudo de caso qualitativo (cidade não identificada): carrega as frases, roda os baselines e
coloca cada item na fila de revisão humana como PENDENTE (nada é publicado aqui)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import paths, registry
from .classifiers.rules import RegrasBaseline
from .review import store

ARQUIVO = paths.CASOS / "estudo_de_caso.yaml"


def carregar(caminho: Path | None = None) -> dict[str, Any]:
    dados = yaml.safe_load((caminho or ARQUIVO).read_text(encoding="utf-8"))
    tax = registry.rotulos_taxonomia()
    ids = set()
    for f in dados["frases"]:
        if f["id"] in ids:
            raise ValueError(f"id duplicado: {f['id']}")
        ids.add(f["id"])
        invalidos = [r for r in f["rotulos_editoriais"] if r not in tax]
        if invalidos:
            raise ValueError(f"{f['id']}: rótulos fora da taxonomia {invalidos}")
        if f["tipo"] not in ("exclusao", "nao_discriminatoria", "ambigua"):
            raise ValueError(f"{f['id']}: tipo inválido")
    return dados


def sugestao_ia(texto: str, modelo_ofensivo=None) -> tuple[list[str], str]:
    """Rótulos sugeridos pelos baselines. `modelo_ofensivo`: (modelo, limiar) opcional (baseline B)."""
    regras = RegrasBaseline()
    rotulos = [r for r, v in regras.prever(texto).items() if v]
    metodo = f"{regras.nome} {regras.versao}"
    if modelo_ofensivo is not None:
        modelo, limiar = modelo_ofensivo
        if float(modelo.pontuar([texto])[0]) >= limiar and "linguagem_ofensiva" not in rotulos:
            rotulos.append("linguagem_ofensiva")
        metodo += " + B_tfidf (HateBR+OLID-BR)"
    return sorted(set(rotulos)), metodo


def enfileirar(conn, caminho: Path | None = None, modelo_ofensivo=None) -> dict[str, int]:
    dados = carregar(caminho)
    novos = 0
    for f in dados["frases"]:
        rotulos, metodo = sugestao_ia(f["texto"], modelo_ofensivo)
        criado = store.adicionar(conn, {
            "id": f["id"], "origem": f["origem"], "tipo": f["tipo"], "texto": f["texto"], "mecanismo": f.get("mecanismo"),
            "par_espelho": f.get("par_espelho"), "pode_publicar_ambigua": f.get("pode_publicar_ambigua", False),
            "ia_rotulos": rotulos, "ia_metodo": metodo, "ia_versao": RegrasBaseline.versao,
            "rotulos_propostos": f["rotulos_editoriais"],
        })
        novos += int(criado)
    return {"total": len(dados["frases"]), "novos": novos}


def modelo_ofensivo_local():
    """Baseline B treinado em HateBR+OLID-BR, se os corpora estiverem normalizados localmente."""
    try:
        from .evaluation import experiments

        info = experiments.treinar_ofensivo(("hatebr", "olid_br"), experiments.SEMENTE_PRINCIPAL, "lr")
        return info["modelo"], experiments._limiar(info, "limiar_f1")
    except FileNotFoundError:
        return None
