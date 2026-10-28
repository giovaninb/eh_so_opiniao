"""Carregamento e validação do catálogo de datasets, taxonomia e mapeamento."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import yaml

from . import paths
from .schema import RELACOES

CAMPOS_OBRIGATORIOS = (
    "nome", "adaptador", "versao", "data_versao", "autores", "referencia", "url_origem",
    "url_arquivos", "licenca", "redistribuicao", "acesso", "status_acesso", "formatos",
    "registros_confirmados", "esquema_anotacao", "rotulos_originais", "idioma",
    "plataforma", "contexto", "hash_ou_revisao", "limitacoes_vieses",
)
ACESSOS = ("aberto", "restrito_autorizacao")
STATUS = ("acessado", "pendente_autorizacao")
TIPOS_TAXONOMIA = ("supervisionado", "exploratorio", "salvaguarda")


class CatalogoInvalido(ValueError):
    pass


def _ler(caminho) -> dict[str, Any]:
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def carregar_registry() -> dict[str, Any]:
    dados = _ler(paths.REGISTRY)
    validar_registry(dados)
    return dados


def validar_registry(dados: dict[str, Any]) -> None:
    politica = dados.get("politica_geral", {})
    if politica.get("corpora_brutos_no_git") is not False:
        raise CatalogoInvalido("politica_geral.corpora_brutos_no_git deve ser false")
    if politica.get("contornar_controle_de_acesso") is not False:
        raise CatalogoInvalido("politica_geral.contornar_controle_de_acesso deve ser false")
    for ds_id, ds in dados.get("datasets", {}).items():
        faltando = [c for c in CAMPOS_OBRIGATORIOS if c not in ds]
        if faltando:
            raise CatalogoInvalido(f"{ds_id}: campos ausentes {faltando}")
        if ds["acesso"] not in ACESSOS:
            raise CatalogoInvalido(f"{ds_id}: acesso inválido {ds['acesso']!r}")
        if ds["status_acesso"] not in STATUS:
            raise CatalogoInvalido(f"{ds_id}: status_acesso inválido {ds['status_acesso']!r}")
        if ds["acesso"] != "aberto" and ds["status_acesso"] == "acessado":
            raise CatalogoInvalido(f"{ds_id}: dataset restrito não pode constar como acessado sem verificação")
        for arq in ds["url_arquivos"]:
            if "arquivo" not in arq or "url" not in arq:
                raise CatalogoInvalido(f"{ds_id}: arquivo sem nome/url")
            if ds["acesso"] == "aberto" and not (arq.get("sha256") or arq.get("md5")):
                raise CatalogoInvalido(f"{ds_id}: arquivo aberto sem hash de integridade ({arq['arquivo']})")


def listar_datasets() -> list[str]:
    return list(carregar_registry()["datasets"])


def dataset(ds_id: str) -> dict[str, Any]:
    try:
        return carregar_registry()["datasets"][ds_id]
    except KeyError as erro:
        raise CatalogoInvalido(f"dataset desconhecido: {ds_id}") from erro


@lru_cache(maxsize=1)
def carregar_taxonomia() -> dict[str, dict[str, Any]]:
    dados = _ler(paths.TAXONOMIA)
    rotulos = {r["id"]: r for r in dados["rotulos"]}
    for r in rotulos.values():
        if r["tipo"] not in TIPOS_TAXONOMIA:
            raise CatalogoInvalido(f"taxonomia: tipo inválido em {r['id']}")
    rotulos["__versao__"] = {"id": "__versao__", "versao": dados["versao"]}
    return rotulos


def versao_taxonomia() -> str:
    return carregar_taxonomia()["__versao__"]["versao"]


def rotulos_taxonomia() -> dict[str, dict[str, Any]]:
    return {k: v for k, v in carregar_taxonomia().items() if k != "__versao__"}


@dataclass(frozen=True)
class Correspondencia:
    dataset_id: str
    original: str
    alvo: str | None
    relacao: str
    nota: str


@lru_cache(maxsize=1)
def _mapping_bruto() -> dict[str, Any]:
    return _ler(paths.MAPPING)


def versao_mapeamento() -> str:
    return _mapping_bruto()["versao"]


def correspondencias(dataset_id: str | None = None) -> list[Correspondencia]:
    saida: list[Correspondencia] = []
    for ds_id, bloco in _mapping_bruto()["datasets"].items():
        if dataset_id and ds_id != dataset_id:
            continue
        for grupo in ("rotulos", "derivados"):
            for original, info in bloco.get(grupo, {}).items():
                saida.append(Correspondencia(ds_id, original, info.get("alvo"), info["relacao"], info.get("nota", "")))
    return saida


def correspondencia(dataset_id: str, original: str) -> Correspondencia:
    for c in correspondencias(dataset_id):
        if c.original == original:
            return c
    raise CatalogoInvalido(f"sem correspondência para {dataset_id}:{original}")


def validar_mapeamento() -> None:
    """Todo alvo deve existir na taxonomia; relações válidas; alvo nulo só se incompatível."""
    tax = rotulos_taxonomia()
    for c in correspondencias():
        if c.relacao not in RELACOES:
            raise CatalogoInvalido(f"relação inválida: {c}")
        if c.alvo is None and c.relacao != "incompativel":
            raise CatalogoInvalido(f"alvo nulo exige relação 'incompativel': {c}")
        if c.alvo is not None and c.alvo not in tax:
            raise CatalogoInvalido(f"alvo fora da taxonomia: {c}")
        if c.relacao == "equivalente" and c.alvo is None:
            raise CatalogoInvalido(f"equivalente sem alvo: {c}")


def rotulo_normalizado(dataset_id: str, original: str, valor: bool | None, politica: str, fontes: list[str] | None = None) -> tuple[str | None, dict[str, Any]]:
    """Retorna (alvo, entrada de normalized_labels). Alvo None => rótulo incompatível (não normalizado)."""
    c = correspondencia(dataset_id, original)
    if c.alvo is None:
        return None, {}
    return c.alvo, {
        "value": valor,
        "relation": c.relacao,
        "policy": politica,
        "source": fontes or [original],
        "mapping_version": versao_mapeamento(),
    }
