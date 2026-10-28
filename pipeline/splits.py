"""Splits sem vazamento.

Duas camadas:
1. Agrupamento: amostras do mesmo grupo (publicação/conversa ou quase-duplicata) ficam
   sempre no mesmo split.
2. Deduplicação cruzada: depois do split, remove de validation/test toda amostra cuja
   chave de quase-duplicata (texto normalizado) apareça no treino.

Tudo é determinístico dada a semente.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from typing import Callable, Iterable, Sequence

from ..schema import NormalizedTextSample
from ..textnorm import hash_chave

Agrupador = Callable[[NormalizedTextSample], str]


def grupo_por_texto(a: NormalizedTextSample) -> str:
    """Quase-duplicatas (retweets, mudança de caixa/menção/URL) caem no mesmo grupo."""
    return "t:" + hash_chave(a.text)


def grupo_por_publicacao(a: NormalizedTextSample) -> str:
    """Comentários da mesma publicação ficam juntos; sem publicação, cai para o texto."""
    post = a.context.get("post_group")
    return f"p:{post}" if post else grupo_por_texto(a)


def dividir(amostras: Sequence[NormalizedTextSample], agrupador: Agrupador,
            proporcoes: dict[str, float] | None = None, semente: int = 42) -> dict[str, str]:
    """Retorna {sample_id: split}. Greedy por déficit sobre grupos embaralhados."""
    proporcoes = proporcoes or {"train": 0.7, "validation": 0.15, "test": 0.15}
    if abs(sum(proporcoes.values()) - 1) > 1e-9:
        raise ValueError("proporções devem somar 1")
    grupos: dict[str, list[str]] = defaultdict(list)
    for a in amostras:
        grupos[agrupador(a)].append(a.sample_id)
    ordem = sorted(grupos)
    random.Random(semente).shuffle(ordem)
    total = len(amostras)
    alvo = {s: p * total for s, p in proporcoes.items()}
    atual = Counter()
    destino: dict[str, str] = {}
    # grupos grandes primeiro estabilizam o balanço
    for g in sorted(ordem, key=lambda g: -len(grupos[g])):
        escolhido = max(alvo, key=lambda s: (alvo[s] - atual[s]) / max(alvo[s], 1e-9))
        for sid in grupos[g]:
            destino[sid] = escolhido
        atual[escolhido] += len(grupos[g])
    return destino


def aplicar(amostras: Iterable[NormalizedTextSample], destino: dict[str, str]) -> list[NormalizedTextSample]:
    saida = []
    for a in amostras:
        a.split = destino[a.sample_id]
        saida.append(a)
    return saida


def remover_duplicatas_cruzadas(amostras: Sequence[NormalizedTextSample]) -> tuple[list[NormalizedTextSample], dict[str, int]]:
    """Remove de validation/test o que também aparece no treino e de test o que aparece em validation."""
    chaves_treino = {hash_chave(a.text) for a in amostras if a.split == "train"}
    removidas: Counter = Counter()
    intermediarias: list[NormalizedTextSample] = []
    for a in amostras:
        if a.split in ("validation", "test") and hash_chave(a.text) in chaves_treino:
            removidas[a.split] += 1
            continue
        intermediarias.append(a)
    chaves_val = {hash_chave(a.text) for a in intermediarias if a.split == "validation"}
    mantidas: list[NormalizedTextSample] = []
    for a in intermediarias:
        if a.split == "test" and hash_chave(a.text) in chaves_val:
            removidas["test"] += 1
            continue
        mantidas.append(a)
    return mantidas, dict(removidas)


def auditar_vazamento(amostras: Sequence[NormalizedTextSample]) -> dict[str, int]:
    """Conta vazamentos remanescentes: textos e publicações em mais de um split."""
    texto_splits: dict[str, set[str]] = defaultdict(set)
    post_splits: dict[str, set[str]] = defaultdict(set)
    for a in amostras:
        if a.split is None:
            continue
        texto_splits[hash_chave(a.text)].add(a.split)
        if a.context.get("post_group"):
            post_splits[a.context["post_group"]].add(a.split)
    return {
        "textos_em_mais_de_um_split": sum(1 for s in texto_splits.values() if len(s) > 1),
        "publicacoes_em_mais_de_um_split": sum(1 for s in post_splits.values() if len(s) > 1),
    }


def sobreposicao_entre_corpora(a: Iterable[NormalizedTextSample], b: Iterable[NormalizedTextSample]) -> set[str]:
    """Chaves de quase-duplicata presentes nos dois corpora (para excluir de avaliação cruzada)."""
    return {hash_chave(x.text) for x in a} & {hash_chave(x.text) for x in b}
