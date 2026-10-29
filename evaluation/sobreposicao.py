"""Análise de sobreposição de textos entre corpora (sem expor nenhum texto).

Por que existe: o TuPyE reúne o ToLD-Br, o HateBR e o corpus de Fortuna et al.; o RacismoBR reaproveita
posts de Fortuna e do ToLD-Br. Treinar num corpus e avaliar em outro que o contém infla métricas.
A chave é a quase-duplicata (`textnorm.hash_chave`: sem caixa, pontuação, URL, menção, 'RT').
Os relatórios trazem só contagens; nenhum texto, nem hash, é publicado.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .. import paths, registry
from ..adapters.base import ler_csv
from ..pipeline import download, normalize
from ..textnorm import hash_chave

CORPORA_NORMALIZADOS = ("told_br", "hatebr", "multidomain_yt_toxbr", "racismobr")
csv.field_size_limit(10**9)


def _chaves_normalizado(ds_id: str) -> dict[str, dict[str, Any]] | None:
    """{chave: {"rotulo_ofensivo": bool|None}} do corpus normalizado; None se não houver dado."""
    try:
        amostras = normalize.carregar_normalizado(ds_id)
    except FileNotFoundError:
        return None
    return {hash_chave(a.text): {"ofensivo": a.valor("linguagem_ofensiva")} for a in amostras}


def _tupye() -> list[dict[str, str]] | None:
    info = registry.dataset("tupye")
    linhas: list[dict[str, str]] = []
    for arq in info["url_arquivos"]:
        r = download.validar_integridade("tupye", arq)
        if r.status != "integridade_ok" or not r.caminho:
            return None
        for l in ler_csv(Path(r.caminho)):
            linhas.append({"text": l.get("text") or "", "researcher": l.get("researcher") or "", "aggressive": l.get("aggressive") or "",
                           "hate": l.get("hate") or ""})
    return linhas


def _par(a: set[str], b: set[str]) -> dict[str, Any]:
    comum = len(a & b)
    return {"em_comum": comum, "fracao_de_a": round(comum / len(a), 4) if a else None, "fracao_de_b": round(comum / len(b), 4) if b else None}


def calcular() -> dict[str, Any]:
    chaves: dict[str, set[str]] = {}
    rotulos: dict[str, dict[str, dict[str, Any]]] = {}
    indisponiveis: list[str] = []
    resumo: dict[str, Any] = {}
    for ds in CORPORA_NORMALIZADOS:
        d = _chaves_normalizado(ds)
        if d is None:
            indisponiveis.append(ds)
            continue
        rotulos[ds] = d
        chaves[ds] = set(d)
        amostras = normalize.carregar_normalizado(ds)
        resumo[ds] = {"textos": len(amostras), "chaves_unicas": len(chaves[ds]), "duplicatas_internas": len(amostras) - len(chaves[ds])}
    tupye = _tupye()
    por_fonte: dict[str, Any] = {}
    cruzado: dict[str, Any] = {}
    if tupye is not None:
        k_tupye = [hash_chave(l["text"]) for l in tupye]
        chaves["tupye"] = set(k_tupye)
        resumo["tupye"] = {"textos": len(tupye), "chaves_unicas": len(chaves["tupye"]), "duplicatas_internas": len(tupye) - len(chaves["tupye"])}
        grupos: dict[str, list[tuple[str, dict[str, str]]]] = defaultdict(list)
        for k, l in zip(k_tupye, tupye):
            grupos[l["researcher"]].append((k, l))
        for fonte, itens in sorted(grupos.items()):
            ks = {k for k, _ in itens}
            por_fonte[fonte] = {"textos": len(itens), **{f"em_{ds}": len(ks & chaves[ds]) for ds in chaves if ds != "tupye"}}
        # definição de rótulo: onde TuPyE e outro corpus têm o MESMO texto, o que cada um diz?
        for ds in ("told_br", "hatebr", "multidomain_yt_toxbr"):
            if ds not in rotulos:
                continue
            tab: Counter = Counter()
            for k, l in zip(k_tupye, tupye):
                if k in rotulos[ds]:
                    ofensivo = rotulos[ds][k]["ofensivo"]
                    tab[(f"tupye_aggressive={l['aggressive']}", f"tupye_hate={l['hate']}", f"{ds}_ofensivo={ofensivo}")] += 1
            cruzado[ds] = [{"tupye_aggressive": a, "tupye_hate": h, "outro_corpus_ofensivo": o, "textos": n} for (a, h, o), n in sorted(tab.items())]
    nomes = sorted(chaves)
    pares = {f"{a}__{b}": _par(chaves[a], chaves[b]) for i, a in enumerate(nomes) for b in nomes[i + 1:]}
    return {
        "metodo": "chave de quase-duplicata (textnorm.hash_chave: sem caixa, pontuação, URL, menção, 'RT'); só contagens",
        "corpora": resumo, "indisponiveis_sem_dados": indisponiveis + (["tupye"] if tupye is None else []),
        "pares": pares,
        "tupye_por_fonte_original": por_fonte,
        "tupye_x_outro_corpus_definicao_de_rotulo": cruzado,
        "racismobr": {"status": "pendente_fonte", "sobreposicao_esperada": ("Parte dos 629 posts da literatura vem de Fortuna et al. (2019) e de Leite et al. (2020, ToLD-Br), "
                      "logo há sobreposição esperada com ToLD-Br e TuPyE. NÃO MEDIDA: sem arquivo. Medir antes de qualquer avaliação cruzada.")},
        "leitura": ("TuPyE contém ToLD-Br e HateBR por construção; não treinar nele para avaliar nesses corpora. Entre ToLD-Br, HateBR e "
                    "MultiDomainYT-ToxBR a sobreposição de textos é a que consta em `pares`; textos em comum são removidos da avaliação cruzada."),
    }


def gerar(destino: Path | None = None) -> dict[str, Any]:
    resultado = calcular()
    destino = destino or paths.RELATORIOS / "sobreposicao_corpora.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    return resultado
