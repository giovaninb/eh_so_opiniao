"""Protocolos AMP-A a AMP-G (catálogo ampliado: RacismoBR, MultiDomainYT-ToxBR e recursos complementares).

Regras que valem para TODOS os protocolos:
- Resultados são calculados aqui, a partir dos corpora do cache local; nenhum número é inventado.
- Resultados ficam SEPARADOS por dataset, por classe e por protocolo. Não há fusão automática de datasets.
- Cada classificador é binário (uma classe por vez). Não se treina nem se publica modelo multirrótulo cuja
  qualidade não tenha sido validada: em AMP-G cada classe passa por um portão explícito (`validada`).
- O F1 binário do MultiDomainYT-ToxBR (0,78 no artigo) NÃO é indicador de capacidade por categoria.
- Dataset `pendente_fonte` (RacismoBR) devolve `{"status": "pendente_fonte"}`: o protocolo está implementado e
  testado com fixtures sintéticas, mas nenhum número real existe.
- Saídas com texto de corpora (falsos positivos, casos explicados, folha de anotação) ficam em
  `datasets/_local/experimentos/` (não versionado). Os JSON de `relatorios/` trazem só números e ids.
- Pontuação ou probabilidade de modelo não é evidência de crime; destaques de modelo não são explicações causais.
"""

from __future__ import annotations

import csv
import json
import math
import random
import re
from functools import lru_cache
from typing import Any, Sequence

import numpy as np

from .. import paths, registry
from ..classifiers.tfidf import TfidfBaseline
from ..schema import NormalizedTextSample
from ..textnorm import hash_chave
from . import experiments as X
from . import metrics as M

SEMENTES = X.SEMENTES
SEMENTE_PRINCIPAL = X.SEMENTE_PRINCIPAL
MDYT = "multidomain_yt_toxbr"
CLASSES_MDYT = ("insulto_hostilidade", "lgbtfobia", "racismo", "misoginia", "xenofobia", "incitacao_violencia",
                "intolerancia_religiosa", "hostilidade_politica", "capacitismo")
AVISO_BINARIO = ("O F1 binário do MultiDomainYT-ToxBR (0,78 no artigo) mede 'tóxico ou não' e NÃO indica capacidade de "
                 "identificar categorias específicas; só os resultados por classe abaixo servem para isso.")


# ------------------------------------------------------------------------------ dados
def _tem(ds: str) -> bool:
    return (paths.normalizados() / f"{ds}.jsonl").exists()


def _pendente(ds: str) -> dict[str, Any] | None:
    info = registry.dataset(ds)
    if info["status_acesso"] == "pendente_fonte":
        return {"status": "pendente_fonte", "motivo": info.get("pendencia", "sem fonte pública verificável")}
    if not _tem(ds):
        return {"status": "ausente_no_cache", "motivo": f"{ds} não normalizado: rode `baixar` e `normalizar`"}
    return None


def _relacao(ds: str, alvo: str) -> dict[str, str]:
    for c in registry.correspondencias(ds):
        if c.alvo == alvo:
            return {"rotulo_original": c.original, "relacao": c.relacao}
    return {"rotulo_original": "(sem rótulo)", "relacao": "ausente"}


def _wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    meia = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, centro - meia), 4), round(min(1.0, centro + meia), 4)]


# ----------------------------------------------------------------- treino e avaliação
@lru_cache(maxsize=None)
def _ajustar(fontes: tuple[tuple[str, str], ...], sem: int, modelo: str = "lr") -> dict[str, Any]:
    """Treina um classificador binário. `fontes` = ((dataset, rótulo normalizado), ...). Sem fusão de rótulos entre classes."""
    t_tr: list[str] = []
    y_tr: list[int] = []
    t_va: list[str] = []
    y_va: list[int] = []
    chaves: set[str] = set()
    for ds, rot in fontes:
        c = X.corpus(ds, sem)
        a, b, _, sel = X._xy(c, rot, "train")
        t_tr += a
        y_tr += list(b)
        chaves |= X._chaves(sel)
        a, b, _, sel_v = X._xy(c, rot, "validation")
        t_va += a
        y_va += list(b)
        chaves |= X._chaves(sel_v)
    if not t_tr or sum(y_tr) == 0 or sum(y_tr) == len(y_tr):
        return {"modelo": None, "motivo": "treino sem as duas classes", "positivos_treino": int(sum(y_tr)), "n_treino": len(t_tr)}
    base = TfidfBaseline(modelo=modelo, semente=sem)
    X_tr = base.ajustar_vetores(t_tr)
    base.ajustar(t_tr, y_tr, X_tr)
    padrao = 0.5 if modelo == "lr" else 0.0
    lim = M.escolher_limiar(y_va, base.pontuar(t_va), "f1") if len(set(y_va)) == 2 else {"limiar": None}
    corte = padrao if lim["limiar"] is None else lim["limiar"]
    return {"modelo": base, "limiar": corte, "limiar_origem": "validacao_f1" if lim["limiar"] is not None else "padrao",
            "chaves_treino": chaves, "n_treino": len(t_tr), "positivos_treino": int(sum(y_tr)), "n_validacao": len(t_va),
            "positivos_validacao": int(sum(y_va))}


def _sem_treino(amostras: Sequence[NormalizedTextSample], chaves: set[str]) -> tuple[list[NormalizedTextSample], int]:
    return X._sem_sobreposicao(amostras, chaves)


def _celula(info: dict[str, Any], amostras: Sequence[NormalizedTextSample], rotulo: str) -> dict[str, Any] | None:
    """Métricas de um classificador binário em amostras rotuladas. None se o treino falhou ou não há rótulo."""
    if info.get("modelo") is None:
        return None
    textos, y, _, _ = X._xy(amostras, rotulo)
    if len(y) == 0:
        return None
    s = info["modelo"].pontuar(textos)
    m = M.metricas_binarias(y, (s >= info["limiar"]).astype(int))
    triv = M.metricas_binarias(y, np.ones_like(y))
    prev = float(y.mean())
    ap = M.curva_pr(y, s, 1)["average_precision"]
    from sklearn.metrics import roc_auc_score

    auc = round(float(roc_auc_score(y, s)), 4) if 0 < y.sum() < len(y) else None
    return {"roc_auc": auc, "precision": m["precision"], "recall": m["recall"], "f1": m["f1"], "macro_f1": m["macro_f1"],
            "taxa_falso_positivo": m["taxa_falso_positivo"], "suporte_positivos": m["suporte_positivos"], "n": len(y),
            "suporte_insuficiente": m["suporte_insuficiente"], "prevalencia": round(prev, 4), "average_precision": ap,
            "lift_ap_sobre_prevalencia": round(ap / prev, 3) if (ap is not None and prev > 0) else None,
            "chute_trivial_macro_f1": triv["macro_f1"], "confusao": m["confusao"]}


def _resumir(celulas: list[dict[str, Any] | None]) -> dict[str, Any]:
    v = [c for c in celulas if c is not None]
    if not v:
        return {"status": "sem_resultado", "motivo": "treino ou rótulo indisponível"}
    out = X._agregar(v)
    out.update({
        "positivos_por_semente": [c["suporte_positivos"] for c in v], "n_por_semente": [c["n"] for c in v],
        "suporte_insuficiente": any(c["suporte_insuficiente"] for c in v),
        "prevalencia": M.media_e_desvio([c["prevalencia"] for c in v]),
        "average_precision": M.media_e_desvio([c["average_precision"] for c in v]),
        "roc_auc": M.media_e_desvio([c["roc_auc"] for c in v]),
        "chute_trivial_macro_f1": M.media_e_desvio([c["chute_trivial_macro_f1"] for c in v]),
        "taxa_falso_positivo": M.media_e_desvio([c["taxa_falso_positivo"] for c in v]),
    })
    if out["suporte_insuficiente"]:
        out["aviso"] = f"menos de {M.MIN_POSITIVOS} positivos no teste em ao menos uma semente: não interpretar P/R/F1"
    return out


def _matriz(alvo: str, datasets: Sequence[str], sementes: Sequence[int]) -> dict[str, Any]:
    """Treino x teste para UM rótulo-alvo. Em domínio: split de teste. Fora de domínio: corpus inteiro menos textos vistos no treino."""
    saida: dict[str, Any] = {}
    for tr in datasets:
        for te in datasets:
            cel = []
            excl = []
            for sem in sementes:
                info = _ajustar(((tr, alvo),), sem)
                if tr == te:
                    amostras, ex = [a for a in X.corpus(te, sem) if a.split == "test"], 0
                else:
                    amostras, ex = _sem_treino(list(X._bruto(te)), info.get("chaves_treino", set())) if info.get("modelo") else ([], 0)
                cel.append(_celula(info, amostras, alvo))
                excl.append(ex)
            saida[f"{tr}->{te}"] = {
                "em_dominio": tr == te, "relacao_treino": _relacao(tr, alvo), "relacao_teste": _relacao(te, alvo),
                "avaliado_em": "split de teste do próprio dataset" if tr == te else "dataset inteiro, sem textos vistos no treino/validação",
                "excluidos_por_sobreposicao_por_semente": excl, **_resumir(cel)}
    return saida


def _disponiveis(candidatos: Sequence[str]) -> tuple[list[str], dict[str, Any]]:
    ok, fora = [], {}
    for ds in candidatos:
        p = _pendente(ds)
        if p is None:
            ok.append(ds)
        else:
            fora[ds] = p
    return ok, fora


# ---------------------------------------------------------------------------- AMP-A
def _validacao_cruzada_racismobr(amostras: Sequence[NormalizedTextSample], modelo: str, n_folds: int = 5, semente: int = 42) -> dict[str, Any]:
    from sklearn.model_selection import StratifiedGroupKFold

    textos = [a.text for a in amostras]
    y = np.array([int(a.valor("racismo")) for a in amostras])
    grupos = [hash_chave(t) for t in textos]
    por_dobra = []
    for tr, te in StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=semente).split(textos, y, grupos):
        base = TfidfBaseline(modelo=modelo, semente=semente)
        X_tr = base.ajustar_vetores([textos[i] for i in tr])
        base.ajustar(None, y[tr], X_tr)
        pred = base.prever([textos[i] for i in te])
        s = base.pontuar([textos[i] for i in te])
        m = M.metricas_binarias(y[te], pred)
        m["f1_nao_racista"], m["average_precision"] = m["f1_classe_negativa"], M.curva_pr(y[te], s, 1)["average_precision"]
        por_dobra.append(m)
    return {"dobras": n_folds, "f1_racista": M.media_e_desvio([m["f1"] for m in por_dobra]),
            "f1_nao_racista": M.media_e_desvio([m["f1_nao_racista"] for m in por_dobra]),
            "macro_f1": M.media_e_desvio([m["macro_f1"] for m in por_dobra]),
            "precisao_racista": M.media_e_desvio([m["precision"] for m in por_dobra]),
            "revocacao_racista": M.media_e_desvio([m["recall"] for m in por_dobra]),
            "average_precision": M.media_e_desvio([m["average_precision"] for m in por_dobra]),
            "positivos_por_dobra_de_teste": [m["suporte_positivos"] for m in por_dobra]}


def experimento_amp_a() -> dict[str, Any]:
    """AMP-A — classificadores binários de racismo DENTRO do RacismoBR (protocolo do artigo: subconjunto balanceado, 5 dobras, semente 42)."""
    base = {"id": "AMP-A", "titulo": "RacismoBR: classificadores binários de racismo (em domínio)",
            "pergunta": "Baselines clássicos separam posts racistas de não racistas no RacismoBR, no subconjunto balanceado e no corpus original?",
            "protocolo": {"subconjunto_experimental": "858 = 429 racistas + 429 não racistas, subamostragem da maioria (semente 42)",
                          "validacao": "StratifiedGroupKFold, 5 dobras, semente 42, agrupando quase-duplicatas",
                          "modelos": ["TF-IDF + regressão logística", "TF-IDF + SVM linear", "chute trivial (sempre racista)"],
                          "separacao": "resultados do corpus ORIGINAL (desbalanceado) e do subconjunto balanceado são reportados em separado"},
            "referencia_do_artigo": "O artigo reporta Macro-F1 mais alto para GPT-4.1 e BERTimbau e nenhuma diferença significativa entre modelos; não é comparável a estes baselines."}
    p = _pendente("racismobr")
    if p:
        return {**base, **p, "resultado": None,
                "nota": "Protocolo implementado e testado só com fixtures sintéticas. Nenhum número real existe até o dataset ter fonte verificável."}
    amostras = list(X._bruto("racismobr"))
    subconj = [a for a in amostras if a.context.get("subconjunto") == "experimental_balanceado"]
    origem = "fornecido_pelos_autores"
    if len(subconj) == 0:
        rng = random.Random(42)
        pos = [a for a in amostras if a.valor("racismo")]
        neg = [a for a in amostras if a.valor("racismo") is False]
        subconj = pos + rng.sample(neg, min(len(pos), len(neg)))
        origem = "reconstruido_pelo_projeto (subamostragem aleatória, semente 42)"
    resultado: dict[str, Any] = {"subconjunto_balanceado": {"origem": origem, "n": len(subconj), "racistas": sum(1 for a in subconj if a.valor("racismo"))},
                                 "corpus_original": {"n": len(amostras), "racistas": sum(1 for a in amostras if a.valor("racismo"))}}
    for nome, conj in (("subconjunto_balanceado", subconj), ("corpus_original", amostras)):
        if min(sum(1 for a in conj if a.valor("racismo")), sum(1 for a in conj if a.valor("racismo") is False)) < 5:
            resultado[nome]["status"] = "dados_insuficientes_para_validacao_cruzada"
            continue
        resultado[nome].update({"lr": _validacao_cruzada_racismobr(conj, "lr"), "svm": _validacao_cruzada_racismobr(conj, "svm"),
                                "chute_trivial_sempre_racista": M.metricas_binarias([int(a.valor("racismo")) for a in conj], [1] * len(conj))})
    return {**base, "status": "executado", "resultado": resultado, "versoes": X._versoes()}


# ---------------------------------------------------------------------------- AMP-B
def experimento_amp_b(sementes: Sequence[int] = SEMENTES) -> dict[str, Any]:
    """AMP-B — generalização entre RacismoBR, ToLD-Br e MultiDomainYT-ToxBR, por rótulo-alvo, respeitando definições distintas."""
    resultado: dict[str, Any] = {}
    for alvo, candidatos in (("racismo", ("racismobr", "told_br", MDYT)), ("linguagem_ofensiva", ("told_br", "hatebr", MDYT))):
        ok, fora = _disponiveis(candidatos)
        resultado[alvo] = {"datasets_usados": ok, "datasets_indisponiveis": fora,
                           "definicoes": {ds: _relacao(ds, alvo) for ds in candidatos}, "matriz": _matriz(alvo, ok, sementes) if len(ok) >= 1 else {}}
    return {"id": "AMP-B", "titulo": "Generalização entre RacismoBR, ToLD-Br e MultiDomainYT-ToxBR",
            "pergunta": "Um baseline treinado numa definição de racismo (ou de ofensa) generaliza para outra, quando as definições só são aproximadas?",
            "avisos": ["Cada rótulo é binário e vem do PRÓPRIO dataset; nenhum rótulo é fundido nem reescrito.",
                       "Relação `aproximado` entre definições: leia a queda fora de domínio como efeito da diferença de definição, domínio e plataforma, não só de modelo.",
                       "RacismoBR cobre racismo contra pessoas negras; ToLD-Br e MultiDomainYT têm escopos próprios (ver label_mapping.yaml).",
                       "Textos em comum entre treino e avaliação são removidos (ver relatorios/sobreposicao_corpora.json); a sobreposição RacismoBR x ToLD-Br é ESPERADA e só pode ser medida quando houver arquivo.",
                       AVISO_BINARIO],
            "alvos": resultado, "modelo": TfidfBaseline(semente=0).descricao(), "versoes": X._versoes()}


# ---------------------------------------------------------------------------- AMP-C
FOLHA = "folha_explicito_implicito.csv"
VALORES_FOLHA = ("explicito", "implicito", "indeterminado")
MIN_POR_ESTRATO = 20


def gerar_folha_explicito_implicito(maximo_por_dataset: int = 60, semente: int = SEMENTE_PRINCIPAL) -> dict[str, Any]:
    """Cria (sem sobrescrever anotações) a folha LOCAL para humanos classificarem positivos de racismo como explícito/implícito."""
    destino = paths.pasta_experimentos_locais() / FOLHA
    destino.parent.mkdir(parents=True, exist_ok=True)
    existentes: dict[str, dict[str, str]] = {}
    if destino.exists():
        with destino.open(encoding="utf-8", newline="") as f:
            existentes = {l["sample_id"]: l for l in csv.DictReader(f)}
    novas = 0
    linhas = list(existentes.values())
    for ds in ("told_br", MDYT, "racismobr"):
        if _pendente(ds):
            continue
        positivos = sorted((a for a in X._bruto(ds) if a.valor("racismo")), key=lambda a: a.sample_id)
        escolhidos = random.Random(semente).sample(positivos, min(maximo_por_dataset, len(positivos)))
        for a in sorted(escolhidos, key=lambda a: a.sample_id):
            if a.sample_id not in existentes:
                linhas.append({"sample_id": a.sample_id, "dataset_id": ds, "texto": a.text, "avaliacao_humana": "", "nota": ""})
                novas += 1
    with destino.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sample_id", "dataset_id", "texto", "avaliacao_humana", "nota"])
        w.writeheader()
        w.writerows(linhas)
    return {"arquivo_local": str(destino), "linhas": len(linhas), "novas": novas}


def _ler_folha() -> list[dict[str, str]]:
    destino = paths.pasta_experimentos_locais() / FOLHA
    if not destino.exists():
        return []
    with destino.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def experimento_amp_c(sementes: Sequence[int] = SEMENTES) -> dict[str, Any]:
    """AMP-C — racismo explícito x implícito. SÓ roda com rótulo humano: nenhum dataset traz essa distinção e não se infere por regra."""
    base = {"id": "AMP-C", "titulo": "Discriminação racial explícita x linguisticamente implícita",
            "pergunta": "A revocação do classificador de racismo cai nos casos que humanos consideram implícitos?",
            "metodo": ("Folha LOCAL de positivos de racismo (datasets/_local/experimentos) para avaliação humana: explicito | implicito | indeterminado. "
                       "O experimento só calcula a revocação por estrato quando há pelo menos "
                       f"{MIN_POR_ESTRATO} itens anotados em cada um dos dois estratos. Nenhum rótulo é inferido automaticamente."),
            "limite": "Nenhum dataset integrado traz a distinção explícito/implícito; o artigo do RacismoBR a discute só qualitativamente."}
    disp, fora = _disponiveis(("told_br", MDYT, "racismobr"))
    folha = gerar_folha_explicito_implicito() if disp else {"arquivo_local": None, "linhas": 0, "novas": 0}
    anot = [l for l in _ler_folha() if (l.get("avaliacao_humana") or "").strip().lower() in VALORES_FOLHA]
    cont = {v: sum(1 for l in anot if l["avaliacao_humana"].strip().lower() == v) for v in VALORES_FOLHA}
    base.update({"folha": {**folha, "anotadas": len(anot), "por_estrato": cont}, "datasets_indisponiveis": fora})
    if min(cont["explicito"], cont["implicito"]) < MIN_POR_ESTRATO:
        return {**base, "status": "aguardando_anotacao_humana",
                "motivo": f"são necessários >= {MIN_POR_ESTRATO} itens 'explicito' e >= {MIN_POR_ESTRATO} 'implicito' anotados por pessoas; há {cont}",
                "resultado": None}
    por_estrato: dict[str, Any] = {}
    por_id = {a.sample_id: a for ds in disp for a in X._bruto(ds)}
    for estrato in ("explicito", "implicito"):
        cel = []
        for sem in sementes:
            partes = []
            for l in anot:
                a = por_id.get(l["sample_id"])
                if a is not None and l["avaliacao_humana"].strip().lower() == estrato and l["dataset_id"] == "told_br":
                    partes.append(a)
            info = _ajustar((("told_br", "racismo"),), sem)
            exemplos, _ = _sem_treino(partes, info.get("chaves_treino", set())) if info.get("modelo") else ([], 0)
            if exemplos and info.get("modelo"):
                s = info["modelo"].pontuar([a.text for a in exemplos])
                cel.append({"recall": float(np.mean(s >= info["limiar"])), "n": len(exemplos)})
        por_estrato[estrato] = {"revocacao": M.media_e_desvio([c["recall"] for c in cel]), "n_por_semente": [c["n"] for c in cel]}
    return {**base, "status": "executado", "resultado": {"modelo_treinado_em": "told_br (rótulo racismo)", "revocacao_por_estrato": por_estrato},
            "versoes": X._versoes()}


# ---------------------------------------------------------------------------- AMP-D
REGIONAL = re.compile(r"\b(?:nordest\w*|sulist\w*|nortista\w*|sudestin\w*|baian\w*|paraiba\w*|carioca\w*|paulist\w*|gaucho\w*|"
                      r"mineir\w*|cearense\w*|pernambucan\w*|amazonens\w*|goian\w*|capixaba\w*)\b")
NACIONALIDADE = re.compile(r"\b(?:imigrant\w*|estrangeir\w*|haitian\w*|venezuelan\w*|argentin\w*|bolivian\w*|paraguai\w*|gringo\w*|"
                           r"refugiad\w*|europeu\w*|chines\w*|portugues\w*|africano\w*|mulcumano\w*|muculmano\w*)\b")


def _composicao_xenofobia(ds: str) -> dict[str, Any]:
    pos = [a for a in X._bruto(ds) if a.valor("xenofobia")]
    reg = nac = ambos = 0
    for a in pos:
        t = X._sem_acentos(a.text)
        r, n = bool(REGIONAL.search(t)), bool(NACIONALIDADE.search(t))
        reg += r and not n
        nac += n and not r
        ambos += r and n
    return {"positivos_xenofobia": len(pos), "com_marcador_regional": reg, "com_marcador_nacionalidade": nac, "com_ambos": ambos,
            "sem_marcador_da_lista": len(pos) - reg - nac - ambos,
            "leitura": "Listas simples de marcadores lexicais: DIAGNÓSTICO de composição, não rótulo nem prova de preconceito regional."}


def experimento_amp_d(sementes: Sequence[int] = SEMENTES) -> dict[str, Any]:
    """AMP-D — desempenho em xenofobia e (sem rótulo) composição regional dos positivos."""
    ok, fora = _disponiveis(("told_br", MDYT))
    return {"id": "AMP-D", "titulo": "Xenofobia e discriminação regional",
            "pergunta": "Um baseline detecta xenofobia anotada, e quanto desses positivos é regional (nordestinos, sulistas etc.) ou de nacionalidade?",
            "datasets_usados": ok, "datasets_indisponiveis": fora,
            "definicoes": {ds: _relacao(ds, "xenofobia") for ds in ("told_br", MDYT)},
            "matriz_xenofobia": _matriz("xenofobia", ok, sementes) if ok else {},
            "composicao_dos_positivos": {ds: _composicao_xenofobia(ds) for ds in ok},
            "discriminacao_regional": {"status": "sem_rotulo_anotado", "classe_taxonomia": "exploratorio",
                                       "referencia_teorica": "Escala de Preconceito contra Nordestinos (Psico, 2025): só referência teórica; não é dataset nem fonte de rótulos.",
                                       "leitura": "Nenhum dataset integrado distingue xenofobia regional da nacional por comentário; nada aqui mede discriminação regional."},
            "avisos": ["Nenhuma outra ferramenta de IA do projeto é usada como classificador de preconceito regional; só estes baselines, sob revisão humana.", AVISO_BINARIO],
            "modelo": TfidfBaseline(semente=0).descricao(), "versoes": X._versoes()}


# ---------------------------------------------------------------------------- AMP-E
def _politico(texto: str) -> bool:
    return bool(X.TERMOS_POLITICOS.search(texto))


def experimento_amp_e(sementes: Sequence[int] = SEMENTES) -> dict[str, Any]:
    """AMP-E — falsos positivos em comentários políticos NÃO tóxicos por consenso humano (proxy de 'crítica legítima')."""
    ok, fora = _disponiveis(("told_br", "hatebr", MDYT))
    modelos = [(f"{ds}:linguagem_ofensiva", ds, "linguagem_ofensiva") for ds in ok]
    if MDYT in ok:
        modelos.append((f"{MDYT}:hostilidade_politica", MDYT, "hostilidade_politica"))
    saida: dict[str, Any] = {}
    locais = paths.pasta_experimentos_locais()
    locais.mkdir(parents=True, exist_ok=True)
    fp_ids: dict[str, list[str]] = {}
    for nome, ds_tr, rot in modelos:
        por_corpus: dict[str, Any] = {}
        for ds_te in ok:
            taxas_pol, taxas_resto, cont = [], [], []
            for sem in sementes:
                info = _ajustar(((ds_tr, rot),), sem)
                if not info.get("modelo"):
                    continue
                if ds_tr == ds_te:
                    pool = [a for a in X.corpus(ds_te, sem) if a.split == "test"]
                else:
                    pool, _ = _sem_treino(list(X._bruto(ds_te)), info["chaves_treino"])
                # negativos por consenso humano no rótulo GERAL de ofensa do corpus avaliado
                neg = [a for a in pool if a.valor("linguagem_ofensiva") is False]
                pol = [a for a in neg if _politico(a.text)]
                resto = [a for a in neg if not _politico(a.text)]
                pred_pol = info["modelo"].pontuar([a.text for a in pol]) >= info["limiar"] if pol else np.array([], dtype=bool)
                pred_resto = info["modelo"].pontuar([a.text for a in resto]) >= info["limiar"] if resto else np.array([], dtype=bool)
                taxas_pol.append(float(pred_pol.mean()) if len(pol) else None)
                taxas_resto.append(float(pred_resto.mean()) if len(resto) else None)
                cont.append({"semente": sem, "n_politico_nao_toxico": len(pol), "fp_politico": int(pred_pol.sum()),
                             "ic95_wilson_politico": _wilson(int(pred_pol.sum()), len(pol)), "n_demais_negativos": len(resto), "fp_demais": int(pred_resto.sum())})
                if sem == SEMENTE_PRINCIPAL:
                    fp_ids[f"{nome}->{ds_te}"] = [a.sample_id for a, p in zip(pol, pred_pol) if p]
            por_corpus[ds_te] = {"em_dominio": ds_tr == ds_te, "taxa_fp_politico_nao_toxico": M.media_e_desvio(taxas_pol),
                                 "taxa_fp_demais_negativos": M.media_e_desvio(taxas_resto), "contagens_por_semente": cont}
        saida[nome] = por_corpus
    with (locais / "amp_e_falsos_positivos_ids.json").open("w", encoding="utf-8") as f:
        json.dump(fp_ids, f, ensure_ascii=False, indent=1)
    return {"id": "AMP-E", "titulo": "Falsos positivos em comentários políticos legítimos",
            "pergunta": "Os classificadores marcam como ofensivos ou hostis comentários políticos que humanos consideraram NÃO tóxicos?",
            "definicao_de_alvo": ("'Comentário político não tóxico' = contém termo político (lista de E/D) E foi rotulado como NÃO ofensivo pelos anotadores do próprio corpus. "
                                  "É um proxy: não é uma revisão humana específica de 'crítica legítima'."),
            "modelos": [m[0] for m in modelos], "resultado_por_modelo_e_corpus": saida, "datasets_indisponiveis": fora,
            "avisos": ["Taxa de falso positivo alta em comentários políticos significa que a triagem automática NÃO deve priorizar casos sem revisão humana.",
                       "Nenhuma outra ferramenta de IA do projeto é usada como classificador de intolerância política; só estes baselines, sob revisão humana.", "Ids dos falsos positivos ficam só em datasets/_local/experimentos."],
            "modelo": TfidfBaseline(semente=0).descricao(), "versoes": X._versoes()}


# ---------------------------------------------------------------------------- AMP-F
def _tokens_gold(a: NormalizedTextSample, chave: str) -> list[int] | None:
    from ..adapters.base import localizar_trechos

    trechos = (a.annotation_metadata.get("rationales") or {}).get(chave) or []
    if not trechos:
        return None
    intervalos, _ = localizar_trechos(a.text, trechos)
    if not intervalos:
        return None
    return X._gold_tokens(a.text, [{"start": s, "end": e} for s, e in intervalos])


def _prf_pares(pares: list[tuple[list[int], list[int]]]) -> dict[str, Any]:
    tp = fp = fn = tn = 0
    for gold, pred in pares:
        for g, p in zip(gold, pred):
            tp += g and p
            fp += (not g) and p
            fn += g and (not p)
            tn += (not g) and (not p)
    n = tp + fp + fn + tn
    po = (tp + tn) / n if n else 0.0
    pe = (((tp + fn) * (tp + fp)) + ((fp + tn) * (fn + tn))) / (n * n) if n else 0.0
    kappa = (po - pe) / (1 - pe) if pe < 1 else None
    return {**X._prf(tp, fp, fn), "kappa_de_cohen_por_token": None if kappa is None else round(kappa, 4), "tokens": n, "tokens_gold_positivos": tp + fn}


def _oclusao(modelo: TfidfBaseline, texto: str) -> list[float]:
    """Queda da pontuação ao remover cada token (sensibilidade do modelo, não causa)."""
    toks = X._tokens(texto)
    variantes = [texto[:s] + texto[e:] for s, e, _ in toks]
    if not variantes:
        return []
    s = modelo.pontuar([texto] + variantes)
    return [float(s[0] - x) for x in s[1:]]


def experimento_amp_f(sementes: Sequence[int] = (SEMENTE_PRINCIPAL,)) -> dict[str, Any]:
    """AMP-F — trechos destacados por modelos x justificativas humanas (HateBRXplain), sem tratar destaque como explicação causal."""
    p = _pendente("hatebr")
    base = {"id": "AMP-F", "titulo": "Explicação humana x trechos destacados por modelos (HateBRXplain)",
            "pergunta": "Os trechos que modelos destacam coincidem com as justificativas humanas, e o quanto os dois humanos coincidem entre si?",
            "avisos": ["Coeficientes e oclusão medem a sensibilidade do MODELO; atenção, SHAP ou LIME também não provam a causa de uma decisão.",
                       "Justificativas humanas são trechos escolhidos por 2 anotadores, não verdade absoluta; por isso a concordância entre eles é o teto de comparação.",
                       "Treino e avaliação no mesmo dataset (HateBR)."]}
    if p:
        return {**base, **p, "resultado": None}
    sem = sementes[0]
    c = X.corpus("hatebr", sem)
    info = _ajustar((("hatebr", "linguagem_ofensiva"),), sem)
    if not info.get("modelo"):
        return {**base, "status": "sem_resultado", "motivo": info.get("motivo")}
    modelo: TfidfBaseline = info["modelo"]
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    t_tr, y_tr, _, _ = X._xy(c, "linguagem_ofensiva", "train")
    vet = TfidfVectorizer(lowercase=True, strip_accents="unicode", token_pattern=r"(?u)\b\w+\b", min_df=2, binary=True)
    uni = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000, solver="liblinear", random_state=sem)
    uni.fit(vet.fit_transform(t_tr), y_tr)
    coef = {X._sem_acentos(k): float(v) for k, v in zip(vet.get_feature_names_out(), uni.coef_[0])}

    def selecionar(split: str) -> list[NormalizedTextSample]:
        return [a for a in c if a.split == split and a.valor("linguagem_ofensiva") is True and a.toxic_spans]

    val, teste = selecionar("validation"), selecionar("test")

    def uniao(a: NormalizedTextSample) -> list[int]:
        return X._gold_tokens(a.text, a.toxic_spans)

    def f_coef(tau):
        return lambda a: [int(coef.get(X._sem_acentos(tok), 0.0) > tau) for _, _, tok in X._tokens(a.text)]

    def f_ocl(tau):
        return lambda a: [int(d > tau) for d in _oclusao(modelo, a.text)]

    def f1(met, amostras, tau):
        return _prf_pares([(uniao(a), met(tau)(a)) for a in amostras])["f1"]

    grade_c, grade_o = (-2.0, -1.0, -0.5, 0.0, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0), (-0.05, -0.01, 0.0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2)
    tau_c = max(grade_c, key=lambda t: f1(f_coef, val, t))
    tau_o = max(grade_o, key=lambda t: f1(f_ocl, val, t))
    rng = random.Random(sem)
    metodos = {"coeficientes_tfidf": f_coef(tau_c), "oclusao_do_modelo_completo": f_ocl(tau_o),
               "tudo": lambda a: [1] * len(X._tokens(a.text)), "aleatorio_prob_0.3": lambda a: [int(rng.random() < 0.3) for _ in X._tokens(a.text)]}
    # ranking (independe de limiar): com k = nº de tokens humanos, quantos dos k tokens mais pontuados são humanos
    from sklearn.metrics import average_precision_score

    rng_r = random.Random(sem)
    escores = {"coeficientes_tfidf": lambda a: [coef.get(X._sem_acentos(t), 0.0) for _, _, t in X._tokens(a.text)],
               "oclusao_do_modelo_completo": lambda a: _oclusao(modelo, a.text),
               "aleatorio": lambda a: [rng_r.random() for _ in X._tokens(a.text)]}
    ranking: dict[str, Any] = {}
    for nome, fn in escores.items():
        rp, ap_y, ap_s = [], [], []
        for a in teste:
            gold, sc = uniao(a), fn(a)
            k = sum(gold)
            if not k or len(sc) != len(gold):
                continue
            top = np.argsort(-np.asarray(sc), kind="stable")[:k]
            rp.append(sum(gold[i] for i in top) / k)
            ap_y += gold
            ap_s += list(sc)
        ranking[nome] = {"r_precision_media_por_comentario": M.media_e_desvio(rp), "average_precision_tokens_agrupados": round(float(average_precision_score(ap_y, ap_s)), 4) if ap_y else None}
    densidade = round(sum(sum(uniao(a)) for a in teste) / max(1, sum(len(uniao(a)) for a in teste)), 4)
    gold_a1 = {a.sample_id: _tokens_gold(a, "anotador_1") for a in teste}
    gold_a2 = {a.sample_id: _tokens_gold(a, "anotador_2") for a in teste}
    ambos = [a for a in teste if gold_a1[a.sample_id] is not None and gold_a2[a.sample_id] is not None]
    humano = _prf_pares([(gold_a1[a.sample_id], gold_a2[a.sample_id]) for a in ambos])
    resultado_metodos: dict[str, Any] = {}
    for nome, met in metodos.items():
        pred = {a.sample_id: met(a) for a in teste}
        resultado_metodos[nome] = {
            "contra_uniao_dos_dois_anotadores": _prf_pares([(uniao(a), pred[a.sample_id]) for a in teste]),
            "contra_anotador_1": _prf_pares([(gold_a1[a.sample_id], pred[a.sample_id]) for a in teste if gold_a1[a.sample_id] is not None]),
            "contra_anotador_2": _prf_pares([(gold_a2[a.sample_id], pred[a.sample_id]) for a in teste if gold_a2[a.sample_id] is not None])}
    # sensibilidade do modelo à remoção (NÃO é causalidade): trechos humanos x tokens aleatórios x top-k por coeficiente
    quedas = {"remover_trechos_humanos": [], "remover_aleatorios_mesmo_numero": [], "remover_topk_coeficiente_mesmo_numero": []}
    mudou = {k: 0 for k in quedas}
    alvo_n = 0
    for a in teste:
        s0 = float(modelo.pontuar([a.text])[0])
        if s0 < info["limiar"]:
            continue
        toks = X._tokens(a.text)
        gold = uniao(a)
        idx = [i for i, g in enumerate(gold) if g]
        if not idx or not toks:
            continue
        k = len(idx)
        alvo_n += 1

        def sem_tokens(ids, a=a, toks=toks):
            return _remover(a.text, [toks[i] for i in set(ids)])

        outros = [i for i in range(len(toks)) if not gold[i]]
        rnd = rng.sample(outros, min(k, len(outros))) if outros else []
        ordem = sorted(range(len(toks)), key=lambda i: -coef.get(X._sem_acentos(toks[i][2]), 0.0))[:k]
        for nome, ids in (("remover_trechos_humanos", idx), ("remover_aleatorios_mesmo_numero", rnd), ("remover_topk_coeficiente_mesmo_numero", ordem)):
            s1 = float(modelo.pontuar([sem_tokens(ids)])[0])
            quedas[nome].append(s0 - s1)
            mudou[nome] += int(s1 < info["limiar"])
    sensib = {k: {"queda_media_da_pontuacao": M.media_e_desvio(v), "fracao_que_deixou_de_ser_marcado": round(mudou[k] / alvo_n, 4) if alvo_n else None}
              for k, v in quedas.items()}
    # casos selecionados: ids e F1 por caso no relatório; texto e spans só localmente
    rng_casos = random.Random(sem)
    escolhidos = rng_casos.sample(teste, min(25, len(teste)))
    locais = paths.pasta_experimentos_locais()
    locais.mkdir(parents=True, exist_ok=True)
    casos_f1 = []
    with (locais / "amp_f_casos_explicados.jsonl").open("w", encoding="utf-8") as f:
        for a in escolhidos:
            gold, pred = uniao(a), metodos["coeficientes_tfidf"](a)
            casos_f1.append({"sample_id": a.sample_id, "f1_token": _prf_pares([(gold, pred)])["f1"]})
            f.write(json.dumps({"sample_id": a.sample_id, "text": a.text, "trechos_humanos": a.annotation_metadata.get("rationales"),
                                "tokens_destacados_pelo_modelo": [t for (_, _, t), p in zip(X._tokens(a.text), pred) if p]}, ensure_ascii=False) + "\n")
    return {**base, "status": "executado", "semente": sem, "amostras": {"validacao": len(val), "teste": len(teste), "teste_com_os_dois_anotadores": len(ambos)},
            "teto_humano_anotador_1_vs_2": humano, "metodos": resultado_metodos,
            "ranking_independente_de_limiar": {"densidade_de_tokens_humanos": densidade, **ranking,
                                               "leitura": "O acaso acerta cerca da densidade; o teto humano é o F1/kappa entre anotadores. Quando 'tudo' empata com os métodos, o F1 por limiar não discrimina e vale o ranking."},
            "limiares_escolhidos_na_validacao": {"coeficientes_tfidf": tau_c, "oclusao": tau_o},
            "sensibilidade_do_modelo_a_remocao": {"base": f"{alvo_n} comentários ofensivos do teste marcados pelo modelo", **sensib,
                                                  "leitura": "Mede o quanto a pontuação do MODELO depende dos trechos; não prova que os trechos causam a decisão nem que o modelo 'entende' a ofensa."},
            "casos_selecionados": {"n": len(casos_f1), "f1_token_por_caso": casos_f1, "onde_ler_o_texto": "datasets/_local/experimentos/amp_f_casos_explicados.jsonl (não versionado)"},
            "modelo": modelo.descricao(), "versoes": X._versoes()}


def _remover(texto: str, tokens: Sequence[tuple[int, int, str]]) -> str:
    saida = texto
    for s, e, _ in sorted(tokens, reverse=True):
        saida = saida[:s] + saida[e:]
    return saida


# ---------------------------------------------------------------------------- AMP-G
SUPORTE_MINIMO_VALIDACAO = M.MIN_POSITIVOS
LIFT_MINIMO = 2.0


def _spearman(a: Sequence[float], b: Sequence[float]) -> float | None:
    if len(a) < 4:
        return None
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0:
        return None
    return round(float(np.corrcoef(ra, rb)[0, 1]), 3)


def experimento_amp_g(sementes: Sequence[int] = SEMENTES) -> dict[str, Any]:
    """AMP-G — impacto da concordância entre anotadores e de classes com poucos exemplos (MultiDomainYT-ToxBR)."""
    base = {"id": "AMP-G", "titulo": "Concordância entre anotadores e classes com poucos exemplos",
            "pergunta": "A qualidade medida cai onde os humanos discordam e onde há poucos positivos? Quais classes podem ser reportadas?",
            "avisos": [AVISO_BINARIO, "Um classificador binário por classe (um contra todos), avaliado separadamente. Nenhum modelo multirrótulo conjunto é treinado ou publicado.",
                       "Portão `validada`: >= 30 positivos no teste em TODAS as sementes E average precision >= 2x a prevalência. Classe não validada NÃO deve ser usada."]}
    p = _pendente(MDYT)
    if p:
        return {**base, **p, "resultado": None}
    por_classe: dict[str, Any] = {}
    celulas_por_classe: dict[str, list] = {}
    for cls in ("linguagem_ofensiva", *CLASSES_MDYT):
        cel = []
        for sem in sementes:
            info = _ajustar(((MDYT, cls),), sem)
            teste = [a for a in X.corpus(MDYT, sem) if a.split == "test"]
            cel.append(_celula(info, teste, cls))
        celulas_por_classe[cls] = cel
        r = _resumir(cel)
        if "f1" in r:
            validas = [c for c in cel if c]
            lift = [c["lift_ap_sobre_prevalencia"] for c in validas if c["lift_ap_sobre_prevalencia"] is not None]
            r["validada"] = bool(len(validas) == len(cel) and all(c["suporte_positivos"] >= SUPORTE_MINIMO_VALIDACAO for c in validas)
                                 and lift and min(lift) >= LIFT_MINIMO)
            r["lift_ap_minimo"] = round(min(lift), 3) if lift else None
            r["motivo_nao_validada"] = None if r["validada"] else "suporte < 30 positivos em alguma semente e/ou average precision < 2x a prevalência"
        r["relacao_com_taxonomia"] = _relacao(MDYT, cls) if cls != "linguagem_ofensiva" else _relacao(MDYT, "linguagem_ofensiva")
        por_classe[cls] = r
    # concordância recalculada x desempenho
    sem0 = SEMENTE_PRINCIPAL
    amostras = list(X._bruto(MDYT))
    tem_votos = bool(amostras) and "votos_por_classe" in amostras[0].annotation_metadata
    concordancia: dict[str, Any] = {"disponivel": tem_votos}
    if tem_votos:
        from . import concordancia as C

        nome_original = {c.alvo: c.original for c in registry.correspondencias(MDYT) if c.alvo and c.original != "toxico_qualquer_categoria"}
        kappas = {}
        for cls in CLASSES_MDYT:
            orig = nome_original[cls]
            kappas[cls] = {}
            for grupo in (1, 2):
                cont = [a.annotation_metadata["votos_por_classe"][orig] for a in amostras if a.annotation_metadata.get("grupo_anotadores") == grupo]
                kappas[cls][f"grupo_{grupo}"] = None if not cont else (None if C.kappa_fleiss_binario(cont) is None else round(C.kappa_fleiss_binario(cont), 4))
        pares = [(float(np.mean([v for v in kappas[c].values() if v is not None])), por_classe[c]["f1"]["media"]) for c in CLASSES_MDYT
                 if "f1" in por_classe[c] and any(v is not None for v in kappas[c].values())]
        concordancia.update({
            "kappa_por_classe_e_grupo": kappas,
            "correlacao_de_spearman_kappa_medio_x_f1": _spearman([p[0] for p in pares], [p[1] for p in pares]),
            "leitura_da_correlacao": "n = 9 classes: descritiva, não inferencial; classes raras confundem raridade com desacordo."})
        # desempenho por nível de acordo do item (binário 'tóxico') e por grupo de anotadores
        por_nivel: dict[str, list] = {"unanimes_em_todas_as_classes": [], "com_voto_dividido_em_alguma_classe": []}
        por_grupo: dict[str, list] = {"grupo_1": [], "grupo_2": []}
        for sem in sementes:
            info = _ajustar(((MDYT, "linguagem_ofensiva"),), sem)
            teste = [a for a in X.corpus(MDYT, sem) if a.split == "test"]
            por_nivel["unanimes_em_todas_as_classes"].append(_celula(info, [a for a in teste if a.annotation_metadata.get("unanime_em_todas_as_classes")], "linguagem_ofensiva"))
            por_nivel["com_voto_dividido_em_alguma_classe"].append(_celula(info, [a for a in teste if a.annotation_metadata.get("unanime_em_todas_as_classes") is False], "linguagem_ofensiva"))
            for g in (1, 2):
                por_grupo[f"grupo_{g}"].append(_celula(info, [a for a in teste if a.annotation_metadata.get("grupo_anotadores") == g], "linguagem_ofensiva"))
        concordancia["desempenho_binario_por_nivel_de_acordo"] = {k: _resumir(v) for k, v in por_nivel.items()}
        concordancia["desempenho_binario_por_grupo_de_anotadores"] = {k: _resumir(v) for k, v in por_grupo.items()}
        concordancia["nota_nivel_de_acordo"] = (
            "F1 e precisão dependem da prevalência de cada estrato (itens unânimes são quase todos negativos), então NÃO são comparáveis entre estratos; "
            "use a AUC-ROC, a revocação e a taxa de falso positivo, e leia o n de positivos de cada estrato. Os estratos não têm o mesmo tamanho nem a mesma composição.")
    # classes com poucos exemplos: curva de aprendizado em classes com positivos suficientes
    curva: dict[str, Any] = {}
    for cls in ("insulto_hostilidade", "hostilidade_politica"):
        tamanhos = (10, 25, 50, 100, 200, None)
        pontos = []
        for tam in tamanhos:
            cel = []
            for sem in sementes:
                c = X.corpus(MDYT, sem)
                t_tr, y_tr, _, _ = X._xy(c, cls, "train")
                t_va, y_va, _, _ = X._xy(c, cls, "validation")
                pos_idx = [i for i, y in enumerate(y_tr) if y == 1]
                neg_idx = [i for i, y in enumerate(y_tr) if y == 0]
                if tam is not None:
                    if tam >= len(pos_idx):
                        continue
                    rng = random.Random(sem)
                    pos_idx = sorted(rng.sample(pos_idx, tam))
                idx = sorted(pos_idx + neg_idx)
                tt, yy = [t_tr[i] for i in idx], np.array([int(y_tr[i]) for i in idx])
                base_m = TfidfBaseline(semente=sem)
                X_tr = base_m.ajustar_vetores(tt)
                base_m.ajustar(None, yy, X_tr)
                lim = M.escolher_limiar(y_va, base_m.pontuar(t_va), "f1")["limiar"] if len(set(y_va)) == 2 else None
                info = {"modelo": base_m, "limiar": 0.5 if lim is None else lim}
                cel.append(_celula(info, [a for a in c if a.split == "test"], cls))
            if cel:
                pontos.append({"positivos_no_treino": tam if tam is not None else "todos", **_resumir(cel)})
        curva[cls] = pontos
    return {**base, "status": "executado", "por_classe_em_dominio": por_classe, "concordancia_e_desempenho": concordancia,
            "curva_de_aprendizado_por_positivos": curva,
            "classes_validadas": [c for c, r in por_classe.items() if r.get("validada")],
            "classes_nao_validadas": [c for c, r in por_classe.items() if "f1" in r and not r.get("validada")],
            "modelo": TfidfBaseline(semente=0).descricao(), "versoes": X._versoes()}


# ------------------------------------------------------------------------- execução
EXPERIMENTOS = {"amp_a": experimento_amp_a, "amp_b": experimento_amp_b, "amp_c": experimento_amp_c, "amp_d": experimento_amp_d,
                "amp_e": experimento_amp_e, "amp_f": experimento_amp_f, "amp_g": experimento_amp_g}


def limpar_caches() -> None:
    _ajustar.cache_clear()


def executar(quais: Sequence[str] | None = None) -> dict[str, Any]:
    paths.RELATORIOS.mkdir(parents=True, exist_ok=True)
    saida = {}
    for chave in (quais or EXPERIMENTOS):
        resultado = EXPERIMENTOS[chave]()
        (paths.RELATORIOS / f"experimento_{chave}.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
        saida[chave] = resultado
    return saida
