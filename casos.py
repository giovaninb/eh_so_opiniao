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
ARQUIVOS = (ARQUIVO, paths.CASOS / "biblioteca_editorial.yaml", paths.CASOS / "biblioteca_ampliada.yaml")
ARQUIVO_TEMAS = paths.CASOS / "temas.yaml"
NATUREZAS = ("ficticio", "adaptado", "documentado")


def temas() -> list[dict[str, str]]:
    return yaml.safe_load(ARQUIVO_TEMAS.read_text(encoding="utf-8"))["temas"]


def carregar_todos(caminhos: tuple[Path, ...] | None = None) -> dict[str, Any]:
    """Junta os arquivos de casos (estudo de caso + biblioteca editorial) validando ids únicos entre eles."""
    frases: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for c in caminhos or ARQUIVOS:
        if not Path(c).exists():
            continue
        for f in carregar(c)["frases"]:
            if f["id"] in vistos:
                raise ValueError(f"id duplicado entre arquivos: {f['id']}")
            vistos.add(f["id"])
            frases.append(f)
    return {"frases": frases}


def carregar(caminho: Path | None = None) -> dict[str, Any]:
    dados = yaml.safe_load((caminho or ARQUIVO).read_text(encoding="utf-8"))
    tax = registry.rotulos_taxonomia()
    ids_tema = {t["id"] for t in temas()}
    ids = set()
    for f in dados["frases"]:
        if f["id"] in ids:
            raise ValueError(f"id duplicado: {f['id']}")
        ids.add(f["id"])
        if f.get("tema") is not None and f["tema"] not in ids_tema:
            raise ValueError(f"{f['id']}: tema desconhecido {f['tema']}")
        if f.get("origem") != "sintetica_ilustrativa":
            raise ValueError(f"{f['id']}: casos de arquivo só podem ser sintetica_ilustrativa (fictícios)")
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
        metodo += " + B_tfidf (HateBR)"
    return sorted(set(rotulos)), metodo


def enfileirar(conn, caminho: Path | None = None, modelo_ofensivo=None) -> dict[str, int]:
    """Coloca os casos na fila como Pendente. Sem `caminho`, usa todos os arquivos de casos."""
    dados = carregar(caminho) if caminho else carregar_todos()
    novos = 0
    for f in dados["frases"]:
        rotulos, metodo = sugestao_ia(f["texto"], modelo_ofensivo)
        criado = store.adicionar(conn, {
            "id": f["id"], "origem": f["origem"], "tipo": f["tipo"], "texto": f["texto"], "mecanismo": f.get("mecanismo"),
            "par_espelho": f.get("par_espelho"), "pode_publicar_ambigua": f.get("pode_publicar_ambigua", False),
            "ia_rotulos": rotulos, "ia_metodo": metodo, "ia_versao": RegrasBaseline.versao,
            "rotulos_propostos": f["rotulos_editoriais"],
            "editorial": {k: f[k] for k in ("tema", "contexto", "razoes", "muda_se") if f.get(k)},
        })
        novos += int(criado)
    return {"total": len(dados["frases"]), "novos": novos}


def modelo_ofensivo_local():
    """Baseline B treinado no HateBR, se o corpus estiver normalizado localmente."""
    try:
        from .evaluation import experiments

        info = experiments.treinar_ofensivo(("hatebr",), experiments.SEMENTE_PRINCIPAL, "lr")
        return info["modelo"], experiments._limiar(info, "limiar_f1")
    except FileNotFoundError:
        return None
