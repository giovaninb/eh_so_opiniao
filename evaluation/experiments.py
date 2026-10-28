"""Experimentos A–E. Todo número reportado é calculado aqui, a partir dos corpora no cache local.

Saídas versionáveis (sem texto de corpora): `relatorios/experimento_<x>.json`.
Saídas com texto (ex.: lista de falsos positivos) ficam em `datasets/_local/experimentos/`.
"""

from __future__ import annotations

import json
import platform
import random
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import sklearn

from .. import paths, registry
from ..classifiers.rules import RegrasBaseline
from ..classifiers.tfidf import TfidfBaseline
from ..pipeline import normalize, splits
from ..schema import NormalizedTextSample
from ..textnorm import hash_chave
from . import metrics as M

SEMENTES = (13, 42, 2026)
SEMENTE_PRINCIPAL = 42
OFENSIVO = "linguagem_ofensiva"


# ----------------------------------------------------------------------------- dados
@lru_cache(maxsize=None)
def _bruto(ds_id: str) -> tuple[NormalizedTextSample, ...]:
    return tuple(normalize.carregar_normalizado(ds_id))


@lru_cache(maxsize=None)
def corpus(ds_id: str, semente: int) -> tuple[NormalizedTextSample, ...]:
    """Corpus com splits sem vazamento (agrupado + deduplicação cruzada)."""
    base = [NormalizedTextSample.from_dict(a.to_dict()) for a in _bruto(ds_id)]
    if ds_id == "olid_br":  # preserva o split oficial; separa validação do treino
        treino = [a for a in base if a.split == "train"]
        teste = [a for a in base if a.split == "test"]
        destino = splits.dividir(treino, splits.grupo_por_texto, {"train": 0.85, "validation": 0.15}, semente)
        todos = splits.aplicar(treino, destino) + teste
    else:
        agrupador = splits.grupo_por_publicacao if ds_id == "hatebr" else splits.grupo_por_texto
        destino = splits.dividir(base, agrupador, None, semente)
        todos = splits.aplicar(base, destino)
    mantidas, _ = splits.remover_duplicatas_cruzadas(todos)
    return tuple(mantidas)


def auditoria_splits(ds_id: str, semente: int) -> dict[str, Any]:
    c = corpus(ds_id, semente)
    brutas = len(_bruto(ds_id))
    cont = {s: sum(1 for a in c if a.split == s) for s in ("train", "validation", "test")}
    return {"n_original": brutas, "n_apos_dedup": len(c), "por_split": cont, **splits.auditar_vazamento(list(c))}


def _xy(amostras: Sequence[NormalizedTextSample], rotulo: str, split: str | None = None):
    sel = [a for a in amostras if (split is None or a.split == split) and a.valor(rotulo) is not None]
    return [a.text for a in sel], np.array([int(a.valor(rotulo)) for a in sel]), [a.sample_id for a in sel], sel


def _chaves(amostras: Sequence[NormalizedTextSample]) -> set[str]:
    return {hash_chave(a.text) for a in amostras}


def _sem_sobreposicao(amostras: Sequence[NormalizedTextSample], chaves_treino: set[str]) -> tuple[list[NormalizedTextSample], int]:
    mantidas = [a for a in amostras if hash_chave(a.text) not in chaves_treino]
    return mantidas, len(amostras) - len(mantidas)


def _versoes() -> dict[str, Any]:
    manifestos = {}
    for ds in registry.listar_datasets():
        caminho = paths.cache_bruto() / ds / "manifest.json"
        if caminho.exists():
            manifestos[ds] = {k: v["sha256"] for k, v in json.loads(caminho.read_text(encoding="utf-8"))["arquivos"].items()}
    return {"python": platform.python_version(), "scikit_learn": sklearn.__version__, "numpy": np.__version__,
            "taxonomia": registry.versao_taxonomia(), "mapeamento": registry.versao_mapeamento(),
            "sha256_arquivos": manifestos, "sementes": list(SEMENTES)}


# ------------------------------------------------------------------------- treinamento
@lru_cache(maxsize=None)
def treinar_ofensivo(composicao: tuple[str, ...], semente: int, modelo: str = "lr") -> dict[str, Any]:
    """Treina o baseline B no rótulo `linguagem_ofensiva` (APROXIMADO entre datasets)."""
    t_tr, y_tr, t_va, y_va, chaves = [], [], [], [], set()
    for ds in composicao:
        c = corpus(ds, semente)
        a, b, _, sel = _xy(c, OFENSIVO, "train")
        t_tr += a
        y_tr += list(b)
        chaves |= _chaves(sel)
        a, b, _, _ = _xy(c, OFENSIVO, "validation")
        t_va += a
        y_va += list(b)
    base = TfidfBaseline(modelo=modelo, semente=semente)
    X_tr = base.ajustar_vetores(t_tr)
    base.ajustar(t_tr, y_tr, X_tr)
    s_va = base.pontuar(t_va)
    lim_f1 = M.escolher_limiar(y_va, s_va, "f1")
    lim_p = M.escolher_limiar(y_va, s_va, "precisao", 0.85)
    padrao = 0.5 if modelo == "lr" else 0.0
    return {"modelo": base, "chaves_treino": chaves, "n_treino": len(t_tr), "n_validacao": len(t_va),
            "limiar_padrao": padrao, "limiar_f1": lim_f1, "limiar_precisao": lim_p,
            "positivos_treino": int(sum(y_tr))}


def _limiar(info: dict[str, Any], chave: str) -> float:
    v = info[chave]["limiar"]
    return info["limiar_padrao"] if v is None else v


def _avaliar_ofensivo(info: dict[str, Any], amostras: Sequence[NormalizedTextSample]) -> dict[str, Any]:
    textos, y, ids, _ = _xy(amostras, OFENSIVO)
    s = info["modelo"].pontuar(textos)
    out = {"n": len(y), "positivos": int(y.sum())}
    for nome, lim in (("padrao", info["limiar_padrao"]), ("val_f1", _limiar(info, "limiar_f1"))):
        pred = (s >= lim).astype(int)
        out[nome] = {"limiar": round(float(lim), 4), **M.metricas_binarias(y, pred)}
    return out


def _agregar(metricas_por_semente: list[dict[str, Any]], caminho: Sequence[str] = ()) -> dict[str, Any]:
    """Média/desvio de precision, recall, f1 para uma lista de dicionários de métricas."""
    def pega(m, k):
        for c in caminho:
            m = m[c]
        return m[k]
    return {k: M.media_e_desvio([pega(m, k) for m in metricas_por_semente]) for k in ("precision", "recall", "f1", "macro_f1")}


# -------------------------------------------------------------------------- A
CLASSES_GRUPO = ("insulto_hostilidade", "lgbtfobia", "misoginia", "racismo", "xenofobia")


def experimento_a(sementes: Sequence[int] = SEMENTES) -> dict[str, Any]:
    """A — ToLD-Br (tweets) -> OLID-BR (YouTube/Twitter): classes de insulto e de grupo."""
    olid = list(corpus("olid_br", SEMENTE_PRINCIPAL))
    por_classe: dict[str, dict[str, list]] = {c: {"dominio": [], "cruzado": []} for c in CLASSES_GRUPO}
    contagens: dict[str, Any] = {}
    for sem in sementes:
        told = corpus("told_br", sem)
        t_tr, _, _, sel_tr = _xy(told, "insulto_hostilidade", "train")
        base = TfidfBaseline(semente=sem)
        X_tr = base.ajustar_vetores(t_tr)
        t_va = [a.text for a in told if a.split == "validation"]
        t_te = [a.text for a in told if a.split == "test"]
        X_va, X_te = base.transformar(t_va), base.transformar(t_te)
        eval_olid, excl = _sem_sobreposicao(olid, _chaves(told))
        X_ol = base.transformar([a.text for a in eval_olid])
        contagens[str(sem)] = {"told_train": len(t_tr), "told_val": len(t_va), "told_test": len(t_te),
                               "olid_avaliado": len(eval_olid), "olid_excluido_sobreposicao": excl}
        for cls in CLASSES_GRUPO:
            y_tr = np.array([int(a.valor(cls)) for a in told if a.split == "train"])
            y_va = np.array([int(a.valor(cls)) for a in told if a.split == "validation"])
            y_te = np.array([int(a.valor(cls)) for a in told if a.split == "test"])
            y_ol = np.array([int(a.valor(cls)) for a in eval_olid])
            clf = TfidfBaseline(semente=sem).compartilhar_vetores(base).ajustar(None, y_tr, X_tr)
            lim = M.escolher_limiar(y_va, clf.pontuar(None, X_va), "f1")["limiar"]
            corte = 0.5 if lim is None else lim
            for nome, X, y in (("dominio", X_te, y_te), ("cruzado", X_ol, y_ol)):
                s = clf.pontuar(None, X)
                m = M.metricas_binarias(y, (s >= corte).astype(int))
                m.update({"limiar": round(float(corte), 4), "limiar_origem": "validacao" if lim is not None else "padrao_0.5",
                          "average_precision": M.curva_pr(y, s, 1)["average_precision"], "positivos_treino": int(y_tr.sum())})
                por_classe[cls][nome].append(m)
    resumo = {}
    mapa = {c.original: c for c in registry.correspondencias("told_br")}
    for cls in CLASSES_GRUPO:
        origem_told = next(c.original for c in registry.correspondencias("told_br") if c.alvo == cls)
        origem_olid = next(c.original for c in registry.correspondencias("olid_br") if c.alvo == cls)
        resumo[cls] = {
            "rotulo_told": origem_told, "relacao_told": mapa[origem_told].relacao,
            "rotulo_olid": origem_olid, "relacao_olid": registry.correspondencia("olid_br", origem_olid).relacao,
            "dominio_told_teste": {**_agregar(por_classe[cls]["dominio"]), "positivos_teste_por_semente": [m["suporte_positivos"] for m in por_classe[cls]["dominio"]]},
            "cruzado_olid": {**_agregar(por_classe[cls]["cruzado"]), "positivos_avaliados_por_semente": [m["suporte_positivos"] for m in por_classe[cls]["cruzado"]],
                             "average_precision": M.media_e_desvio([m["average_precision"] for m in por_classe[cls]["cruzado"]]),
                             "prevalencia_base": round(por_classe[cls]["cruzado"][0]["suporte_positivos"] / por_classe[cls]["cruzado"][0]["suporte_total"], 4)},
            "suporte_insuficiente_dominio": any(m["suporte_insuficiente"] for m in por_classe[cls]["dominio"]),
            "positivos_treino_por_semente": [m["positivos_treino"] for m in por_classe[cls]["dominio"]],
        }
    macro = {}
    for nome, chave in (("dominio", "dominio_told_teste"), ("cruzado", "cruzado_olid")):
        macro[nome] = M.media_e_desvio([np.mean([resumo[c][chave]["f1"]["media"] for c in CLASSES_GRUPO])])
    return {"id": "A", "titulo": "ToLD-Br -> OLID-BR: classes de insulto e de grupo (aprox. entre datasets)",
            "pergunta": "Um modelo treinado em tweets generaliza classes de grupo para outro dataset com definições aproximadas?",
            "modelo": TfidfBaseline(semente=0).descricao(), "contagens": contagens, "por_classe": resumo,
            "macro_f1_media_das_classes": macro,
            "leitura": "Classes raras no ToLD-Br (racismo, xenofobia) têm poucos positivos por semente: resultados instáveis, sem conclusão.",
            "versoes": _versoes()}


# -------------------------------------------------------------------------- B
def experimento_b(sementes: Sequence[int] = SEMENTES) -> dict[str, Any]:
    """B — HateBR (comentários políticos): regras vs TF-IDF (LR/SVM); limiares e calibração; transferência."""
    regras = RegrasBaseline()
    olid_all = list(corpus("olid_br", SEMENTE_PRINCIPAL))
    por_sem: dict[str, list] = {k: [] for k in ("trivial", "A_lexico", "B_lr_0.5", "B_lr_val_f1", "B_lr_precisao>=0.85", "B_svm_val_f1")}
    cruz: dict[str, list] = {k: [] for k in ("trivial", "A_lexico", "B_lr_val_f1")}
    extra: dict[str, Any] = {}
    for sem in sementes:
        c = corpus("hatebr", sem)
        textos, y, ids, sel = _xy(c, OFENSIVO, "test")
        lr = treinar_ofensivo(("hatebr",), sem, "lr")
        svm = treinar_ofensivo(("hatebr",), sem, "svm")
        s_lr, s_svm = lr["modelo"].pontuar(textos), svm["modelo"].pontuar(textos)
        por_sem["trivial"].append(M.metricas_binarias(y, np.ones_like(y)))
        por_sem["A_lexico"].append(M.metricas_binarias(y, np.array(regras.prever_ofensivo(textos), dtype=int)))
        por_sem["B_lr_0.5"].append(M.metricas_binarias(y, (s_lr >= 0.5).astype(int)))
        por_sem["B_lr_val_f1"].append(M.metricas_binarias(y, (s_lr >= _limiar(lr, "limiar_f1")).astype(int)))
        por_sem["B_lr_precisao>=0.85"].append(M.metricas_binarias(y, (s_lr >= _limiar(lr, "limiar_precisao")).astype(int)))
        por_sem["B_svm_val_f1"].append(M.metricas_binarias(y, (s_svm >= _limiar(svm, "limiar_f1")).astype(int)))
        if sem == SEMENTE_PRINCIPAL:
            extra = {"curva_pr_lr": M.curva_pr(y, s_lr), "calibracao_lr": M.calibracao(y, s_lr),
                     "limiares_lr": {"f1": lr["limiar_f1"], "precisao>=0.85": lr["limiar_precisao"]},
                     "n_treino": lr["n_treino"], "positivos_treino": lr["positivos_treino"], "auditoria_splits": auditoria_splits("hatebr", sem)}
        eval_olid, excl = _sem_sobreposicao(olid_all, lr["chaves_treino"])
        t_o, y_o, _, _ = _xy(eval_olid, OFENSIVO)
        cruz["trivial"].append(M.metricas_binarias(y_o, np.ones_like(y_o)))
        cruz["A_lexico"].append(M.metricas_binarias(y_o, np.array(regras.prever_ofensivo(t_o), dtype=int)))
        s_o = lr["modelo"].pontuar(t_o)
        m = M.metricas_binarias(y_o, (s_o >= _limiar(lr, "limiar_f1")).astype(int))
        m["average_precision"] = M.curva_pr(y_o, s_o, 1)["average_precision"]
        m["excluidos_sobreposicao"], m["prevalencia"] = excl, round(float(y_o.mean()), 4)
        cruz["B_lr_val_f1"].append(m)
    return {"id": "B", "titulo": "HateBR: regras vs TF-IDF (LR/SVM), limiares, calibração e transferência para OLID-BR",
            "pergunta": "O que um modelo simples separa em comentários políticos ofensivos vs não ofensivos, e isso se mantém fora do domínio?",
            "teste_hatebr": {k: _agregar(v) | {"suporte_teste_por_semente": [x["suporte_total"] for x in v], "confusao_semente_principal": v[list(sementes).index(SEMENTE_PRINCIPAL)]["confusao"]} for k, v in por_sem.items()},
            "transferencia_para_olid": {k: _agregar(v) | {"confusao_semente_principal": v[list(sementes).index(SEMENTE_PRINCIPAL)]["confusao"]} for k, v in cruz.items()}
            | {"prevalencia_olid": cruz["B_lr_val_f1"][0]["prevalencia"], "excluidos_sobreposicao_por_semente": [m["excluidos_sobreposicao"] for m in cruz["B_lr_val_f1"]]},
            "semente_principal": SEMENTE_PRINCIPAL, "detalhes_semente_principal": extra,
            "regras": regras.descricao(), "modelo": TfidfBaseline(semente=0).descricao(), "versoes": _versoes(),
            "leitura": "O rótulo 'ofensivo' é aproximado entre HateBR e OLID-BR; o baseline trivial 'sempre ofensivo' contextualiza a OLID (prevalência alta)."}


# -------------------------------------------------------------------------- C
COMPOSICOES = (("hatebr",), ("olid_br",), ("told_br",), ("hatebr", "olid_br"), ("hatebr", "olid_br", "told_br"))
DATASETS_TESTE = ("hatebr", "olid_br", "told_br")


def experimento_c(sementes: Sequence[int] = SEMENTES) -> dict[str, Any]:
    """C — combinar datasets com rótulo APROXIMADO ajuda ou atrapalha? (matriz treino x teste)"""
    matriz: dict[str, dict[str, Any]] = {}
    for comp in COMPOSICOES:
        nome = "+".join(comp)
        matriz[nome] = {}
        for ds_teste in DATASETS_TESTE:
            res_0_5, res_val, exc, sup = [], [], [], []
            for sem in sementes:
                info = treinar_ofensivo(comp, sem, "lr")
                teste = [a for a in corpus(ds_teste, sem) if a.split == "test"]
                avaliavel, excl = _sem_sobreposicao(teste, info["chaves_treino"])
                r = _avaliar_ofensivo(info, avaliavel)
                res_0_5.append(r["padrao"])
                res_val.append(r["val_f1"])
                exc.append(excl)
                sup.append({"n": r["n"], "positivos": r["positivos"]})
            matriz[nome][ds_teste] = {
                "em_dominio": ds_teste in comp,
                "limiar_0.5": _agregar(res_0_5), "limiar_val_f1": _agregar(res_val),
                "suporte_por_semente": sup, "excluidos_sobreposicao_por_semente": exc,
            }
    ganhos = []
    for ds_teste in DATASETS_TESTE:
        ref = [c for c in COMPOSICOES if c == (ds_teste,)][0]
        for comp in COMPOSICOES:
            if comp == ref or ds_teste not in comp:
                continue
            a = matriz["+".join(ref)][ds_teste]["limiar_val_f1"]["f1"]["media"]
            b = matriz["+".join(comp)][ds_teste]["limiar_val_f1"]["f1"]["media"]
            ganhos.append({"teste": ds_teste, "treino_referencia": "+".join(ref), "treino_combinado": "+".join(comp),
                           "f1_referencia": a, "f1_combinado": b, "delta": round(b - a, 4)})
    return {"id": "C", "titulo": "Combinar HateBR, OLID-BR e ToLD-Br: efeito do mapeamento aproximado de 'linguagem ofensiva'",
            "pergunta": "Treinar com datasets de definição aproximada melhora a generalização ou introduz ruído?",
            "definicoes": {"hatebr": "offensive_label (binário, políticos/Instagram)", "olid_br": "is_offensive (Perspective API + anotadores)",
                           "told_br": "derivado: qualquer categoria com >=2/3 votos"},
            "matriz_treino_x_teste": matriz, "efeito_de_combinar_em_dominio": ganhos,
            "modelo": TfidfBaseline(semente=0).descricao(), "versoes": _versoes(),
            "leitura": "Cada célula usa o split de teste do dataset de avaliação, sem os textos que aparecem no treino."}


# -------------------------------------------------------------------------- D
PARES_POLITICOS = (("lula", "bolsonaro"), ("petista", "bolsonarista"), ("petistas", "bolsonaristas"),
                   ("esquerda", "direita"), ("esquerdista", "direitista"), ("esquerdistas", "direitistas"), ("pt", "pl"))
TERMOS_POLITICOS = re.compile(r"\b(?:lula|bolsonaro|pt|pl|petistas?|bolsonaristas?|esquerd\w*|direit\w*|govern\w*|president\w*|"
                              r"politic\w*|deputad\w*|senador\w*|partido|elei\w+|vot\w+|candidat\w*)\b", re.IGNORECASE)


def _trocar(texto: str, de: str, para: str) -> str:
    def sub(m: re.Match) -> str:
        o = m.group(0)
        return para.upper() if o.isupper() and len(o) > 1 else (para.capitalize() if o[0].isupper() else para)
    return re.sub(rf"\b{re.escape(de)}\b", sub, texto, flags=re.IGNORECASE)


def _contrafactual(info: dict[str, Any], amostras: Sequence[NormalizedTextSample]) -> dict[str, Any]:
    lim = _limiar(info, "limiar_f1")
    resultado: dict[str, Any] = {}
    for direcao, (idx_de, idx_para) in {"esquerda_para_direita": (0, 1), "direita_para_esquerda": (1, 0)}.items():
        orig, troc = [], []
        for a in amostras:
            texto = a.text
            tem_de = any(re.search(rf"\b{re.escape(p[idx_de])}\b", texto, re.IGNORECASE) for p in PARES_POLITICOS)
            tem_para = any(re.search(rf"\b{re.escape(p[idx_para])}\b", texto, re.IGNORECASE) for p in PARES_POLITICOS)
            if tem_de and not tem_para:  # só um lado presente: troca espelhada sem ambiguidade
                novo = texto
                for p in PARES_POLITICOS:
                    novo = _trocar(novo, p[idx_de], p[idx_para])
                if novo != texto:
                    orig.append(texto)
                    troc.append(novo)
        if not orig:
            resultado[direcao] = {"n": 0}
            continue
        so, st = info["modelo"].pontuar(orig), info["modelo"].pontuar(troc)
        rng = np.random.default_rng(SEMENTE_PRINCIPAL)
        dif = st - so
        medias = [float(dif[rng.integers(0, len(dif), len(dif))].mean()) for _ in range(2000)]
        resultado[direcao] = {"n": len(orig), "delta_medio_assinado": round(float(np.mean(dif)), 4),
                              "ic95_bootstrap": [round(float(np.percentile(medias, 2.5)), 4), round(float(np.percentile(medias, 97.5)), 4)],
                              "delta_medio_absoluto": round(float(np.mean(np.abs(st - so))), 4),
                              "mudou_decisao": int(((so >= lim) != (st >= lim)).sum()),
                              "fracao_mudou_decisao": round(float(((so >= lim) != (st >= lim)).mean()), 4)}
    return resultado


def experimento_d() -> dict[str, Any]:
    """D — falsos positivos e neutralidade partidária (contrafactual), mais fixtures do monitor."""
    sem = SEMENTE_PRINCIPAL
    saidas_locais = paths.pasta_experimentos_locais()
    saidas_locais.mkdir(parents=True, exist_ok=True)
    resultado: dict[str, Any] = {"id": "D", "titulo": "Falsos positivos e neutralidade partidária (contrafactual)",
                                 "pergunta": "O modelo trata de modo diferente o mesmo texto quando só a sigla/lado político é trocado?"}
    for nome, comp in (("hatebr", ("hatebr",)), ("hatebr+olid_br", ("hatebr", "olid_br"))):
        info = treinar_ofensivo(comp, sem, "lr")
        base = [a for ds in comp for a in corpus(ds, sem) if a.split in ("validation", "test")]
        base, _ = _sem_sobreposicao(base, info["chaves_treino"])
        resultado.setdefault("contrafactual", {})[nome] = {
            "n_avaliacao": len(base), "limiar": _limiar(info, "limiar_f1"),
            "nao_ofensivos": _contrafactual(info, [a for a in base if a.valor(OFENSIVO) is False]),
            "ofensivos": _contrafactual(info, [a for a in base if a.valor(OFENSIVO) is True]),
        }
    # falsos positivos em comentários NÃO ofensivos do HateBR (teste)
    info = treinar_ofensivo(("hatebr",), sem, "lr")
    teste = [a for a in corpus("hatebr", sem) if a.split == "test" and a.valor(OFENSIVO) is False]
    textos = [a.text for a in teste]
    pred = info["modelo"].pontuar(textos) >= _limiar(info, "limiar_f1")
    grupos = {
        "menciona_termo_politico": [bool(TERMOS_POLITICOS.search(t)) for t in textos],
        "curto_ate_3_palavras": [len(t.split()) <= 3 for t in textos],
        "contem_exclamacao": ["!" in t for t in textos],
        "contem_maiusculas_longas": [bool(re.search(r"[A-ZÀ-Ý]{4,}", t)) for t in textos],
    }
    faixa: dict[str, Any] = {"n_nao_ofensivos_teste": len(textos), "taxa_falso_positivo_geral": round(float(pred.mean()), 4)}
    for nome, mascara in grupos.items():
        m = np.array(mascara)
        faixa[nome] = {"com": {"n": int(m.sum()), "taxa_fp": round(float(pred[m].mean()), 4) if m.any() else None},
                       "sem": {"n": int((~m).sum()), "taxa_fp": round(float(pred[~m].mean()), 4) if (~m).any() else None}}
    resultado["falsos_positivos_hatebr_nao_ofensivos"] = faixa
    with (saidas_locais / "falsos_positivos_hatebr.jsonl").open("w", encoding="utf-8") as f:
        for a, p in zip(teste, pred):
            if p:
                f.write(json.dumps({"sample_id": a.sample_id, "text": a.text}, ensure_ascii=False) + "\n")
    resultado["observacao_privacidade"] = "A lista com texto dos falsos positivos fica só em datasets/_local/experimentos (não versionada)."
    resultado["fixtures_do_monitor"] = _fixtures_do_monitor()
    resultado["versoes"] = _versoes()
    return resultado


def _fixtures_do_monitor() -> dict[str, Any]:
    caminho = Path(__file__).resolve().parents[2] / "monitor_intolerancia_politica_arquivos" / "fixtures_monitor_intolerancia.jsonl"
    if not caminho.exists():
        return {"disponivel": False}
    linhas = [json.loads(x) for x in caminho.read_text(encoding="utf-8").splitlines() if x.strip()]
    info = treinar_ofensivo(("hatebr", "olid_br"), SEMENTE_PRINCIPAL, "lr")
    scores = info["modelo"].pontuar([x["texto_original"] for x in linhas])
    regras = RegrasBaseline()
    return {
        "disponivel": True, "carater": "QUALITATIVO: 27 casos não são amostra estatística e não geram métrica.",
        "limiar": _limiar(info, "limiar_f1"),
        "casos": [{"id": x["id"], "triagem_esperada_no_arquivo": x["triagem"], "score_ofensivo_B": round(float(s), 3),
                   "B_acima_do_limiar": bool(s >= _limiar(info, "limiar_f1")),
                   "A_lexico": bool(regras.termos_encontrados(x["texto_original"]))} for x, s in zip(linhas, scores)],
    }


# -------------------------------------------------------------------------- E
def _sem_acentos(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)).lower()


def _tokens(texto: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group(0)) for m in re.finditer(r"\w+", texto)]


def _gold_tokens(texto: str, spans: Sequence[dict[str, Any]]) -> list[int]:
    cobertos = np.zeros(len(texto), dtype=bool)
    for sp in spans:
        cobertos[sp["start"]:sp["end"]] = True
    saida = []
    for ini, fim, _ in _tokens(texto):
        saida.append(int(cobertos[ini:fim].mean() >= 0.5))
    return saida


def _prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(2 * p * r / (p + r), 4) if p + r else 0.0}


def _avaliar_tokens(amostras: Sequence[NormalizedTextSample], prever) -> dict[str, Any]:
    tp = fp = fn = 0
    for a in amostras:
        gold = _gold_tokens(a.text, a.toxic_spans)
        pred = prever(a.text)
        for g, p in zip(gold, pred):
            tp += g and p
            fp += (not g) and p
            fn += g and (not p)
    return {**_prf(tp, fp, fn), "tokens_gold_positivos": tp + fn, "amostras": len(amostras)}


def experimento_e() -> dict[str, Any]:
    """E — destaque de trechos: coeficientes do TF-IDF vs spans humanos (OLID-BR) e rationales (HateBRXplain)."""
    sem = SEMENTE_PRINCIPAL
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    c_olid = corpus("olid_br", sem)
    t_tr, y_tr, _, _ = _xy(c_olid, OFENSIVO, "train")
    vet = TfidfVectorizer(lowercase=True, strip_accents="unicode", token_pattern=r"(?u)\b\w+\b", min_df=2, binary=True)
    modelo_uni = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000, solver="liblinear", random_state=sem)
    modelo_uni.fit(vet.fit_transform(t_tr), y_tr)
    coef = {_sem_acentos(k): float(v) for k, v in zip(vet.get_feature_names_out(), modelo_uni.coef_[0])}
    regras = RegrasBaseline()
    rng = random.Random(sem)

    def selecionar(c, splits_):
        return [a for a in c if a.split in splits_ and a.valor(OFENSIVO) is True and a.toxic_spans
                and a.annotation_metadata.get("spans_confiaveis", True)]

    olid = corpus("olid_br", sem)
    val, teste = selecionar(olid, ("validation",)), selecionar(olid, ("test",))

    def por_limiar(tau):
        return lambda texto: [int(coef.get(_sem_acentos(tok), 0.0) > tau) for _, _, tok in _tokens(texto)]

    grade = (-0.5, -0.25, 0.0, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0)
    val_res = {tau: _avaliar_tokens(val, por_limiar(tau))["f1"] for tau in grade}
    tau = max(val_res, key=val_res.get)
    metodos = {
        "B_coeficientes_tfidf": por_limiar(tau),
        "A_lexico": lambda texto: [int(bool(regras.termos_encontrados(tok))) for _, _, tok in _tokens(texto)],
        "tudo": lambda texto: [1 for _ in _tokens(texto)],
        "aleatorio_prob_0.3": lambda texto: [int(rng.random() < 0.3) for _ in _tokens(texto)],
    }
    olid_res = {k: _avaliar_tokens(teste, f) for k, f in metodos.items()}
    brutas = [a for a in _bruto("olid_br") if a.valor(OFENSIVO) is True and a.toxic_spans]
    xplain = [a for a in _bruto("hatebr") if a.valor(OFENSIVO) is True and a.toxic_spans]
    xplain_res = {k: _avaliar_tokens(xplain, f) for k, f in metodos.items()}
    return {"id": "E", "titulo": "Destaque de trechos ofensivos: baseline vs anotação humana",
            "pergunta": "Os termos que o modelo considera mais 'ofensivos' coincidem com os trechos que humanos marcaram?",
            "metrica": "P/R/F1 por token (palavra) com gold = token com >=50% dos caracteres em spans humanos",
            "modelo_de_destaque": "regressão logística só com unigramas binários (TF-IDF), treinada no treino do OLID-BR; token sem coeficiente = 0",
            "limiar_coeficiente_escolhido_na_validacao": tau, "f1_validacao_por_limiar": {str(k): v for k, v in val_res.items()},
            "olid_br_teste": olid_res,
            "hatebrxplain_transferencia": {"observacao": "modelo treinado só em OLID-BR; spans derivados de rationales (busca textual)", **xplain_res},
            "exclusoes": {"olid_amostras_ofensivas_com_span": len(brutas), "olid_spans_nao_confiaveis": sum(1 for a in brutas if not a.annotation_metadata.get("spans_confiaveis", True)),
                          "olid_ofensivas_sem_span_ignoradas": sum(1 for a in _bruto("olid_br") if a.valor(OFENSIVO) is True and not a.toxic_spans)},
            "versoes": _versoes(),
            "leitura": "Coeficientes de modelo NÃO são explicações causais; servem como destaque auditável, sujeito a revisão humana."}


# ----------------------------------------------------------------------- execução
EXPERIMENTOS = {"a": experimento_a, "b": experimento_b, "c": experimento_c, "d": experimento_d, "e": experimento_e}


def executar(quais: Sequence[str] | None = None) -> dict[str, Any]:
    paths.RELATORIOS.mkdir(parents=True, exist_ok=True)
    saida = {}
    for chave in (quais or EXPERIMENTOS):
        resultado = EXPERIMENTOS[chave]()
        (paths.RELATORIOS / f"experimento_{chave}.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
        saida[chave] = resultado
    return saida
