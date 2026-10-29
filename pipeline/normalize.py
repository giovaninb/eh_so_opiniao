"""Validação + normalização: arquivos do cache -> JSONL de `NormalizedTextSample`.

Dataset sem arquivos íntegros no cache NÃO derruba o pipeline: vira um item do relatório
com o status do catálogo (ex.: pendente_autorizacao) e as demais fontes seguem.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .. import paths, registry
from ..adapters import HateBrAdapter, MultiDomainYtToxBrAdapter, ToldBrAdapter
from ..adapters.base import AdapterBase
from ..schema import NormalizedTextSample, escrever_jsonl, ler_jsonl
from . import download


def _arquivo(ds_id: str, nome: str) -> Path | None:
    info = registry.dataset(ds_id)
    arq = next(a for a in info["url_arquivos"] if a["arquivo"] == nome)
    r = download.validar_integridade(ds_id, arq)
    return Path(r.caminho) if r.status == "integridade_ok" and r.caminho else None


def construir_adaptador(ds_id: str, **opcoes: Any) -> AdapterBase | None:
    """Cria o adaptador com os arquivos íntegros do cache; None se faltarem arquivos."""
    if ds_id == "told_br":
        f = _arquivo(ds_id, "ToLD-BR.csv")
        return ToldBrAdapter(f, politica=opcoes.get("politica", "maioria")) if f else None
    if ds_id == "hatebr":
        f, x = _arquivo(ds_id, "HateBR.csv"), _arquivo(ds_id, "HateBRXplain.csv")
        return HateBrAdapter(f, x) if f else None
    if ds_id == "multidomain_yt_toxbr":
        b, m = _arquivo(ds_id, "multiDomainYtBinary.csv"), _arquivo(ds_id, "multiDomainYtMultilabel.csv")
        if not (b and m):
            return None
        planilhas = [_arquivo(ds_id, f"comentariosParaAnotacao{k}.xlsx") for k in range(1, 7)]
        # Sem as seis planilhas a concordância fica indisponível e a ordem do vetor não é reconferida.
        return MultiDomainYtToxBrAdapter(b, m, planilhas if all(planilhas) else None, modo=opcoes.get("modo", "ambos"))
    if ds_id == "racismobr":
        return None  # pendente_fonte: nenhum arquivo para ler; o contrato só é exercitado por fixtures sintéticas
    raise registry.CatalogoInvalido(f"sem fábrica para {ds_id}")


def resumo_rotulos(amostras: list[NormalizedTextSample]) -> dict[str, dict[str, int]]:
    cont: dict[str, Counter] = {}
    for a in amostras:
        for nome, info in a.normalized_labels.items():
            cont.setdefault(nome, Counter())[str(info["value"])] += 1
    return {k: dict(v) for k, v in sorted(cont.items())}


def normalizar_dataset(ds_id: str, destino: Path | None = None, **opcoes: Any) -> dict[str, Any]:
    info = registry.dataset(ds_id)
    if info["integracao"] == "somente_sobreposicao":
        return {"dataset_id": ds_id, "status": "nao_normalizado", "amostras": 0,
                "motivo": "dataset lido apenas para análise de sobreposição; seus rótulos não entram nos experimentos"}
    if info["status_acesso"] == "pendente_fonte":
        return {"dataset_id": ds_id, "status": "pendente_fonte", "amostras": 0,
                "motivo": "sem fonte pública verificável; nenhum dado foi lido (ver registry.yaml)"}
    adaptador = construir_adaptador(ds_id, **opcoes)
    if adaptador is None:
        return {"dataset_id": ds_id, "status": info["status_acesso"] if info["status_acesso"] != "acessado" else "ausente_no_cache",
                "motivo": "arquivos não disponíveis ou sem integridade validada no cache local", "amostras": 0}
    amostras = adaptador.todas()
    destino = destino or paths.normalizados() / f"{ds_id}.jsonl"
    n = escrever_jsonl(amostras, destino)
    origens = Counter(a.provenance["origem"] for a in amostras)
    return {
        "dataset_id": ds_id, "status": "normalizado", "amostras": n, "arquivo": str(destino),
        "origens": dict(origens), "rotulos_normalizados": resumo_rotulos(amostras),
        "relatorio_adaptador": adaptador.relatorio, "versao_dataset": info["versao"],
    }


def normalizar_todos(**opcoes: Any) -> dict[str, Any]:
    relatorio = {ds: normalizar_dataset(ds, **opcoes) for ds in registry.listar_datasets()}
    pasta = paths.normalizados()
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "relatorio_normalizacao.json").write_text(json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8")
    return relatorio


def carregar_normalizado(ds_id: str) -> list[NormalizedTextSample]:
    caminho = paths.normalizados() / f"{ds_id}.jsonl"
    if not caminho.exists():
        raise FileNotFoundError(f"{ds_id} ainda não normalizado: rode `normalizar`")
    return list(ler_jsonl(caminho))
