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
    "condicoes_licenca", "integracao",
)
# acesso:
#   aberto               -> arquivos publicados sem credencial;
#   restrito_autorizacao -> exige aceite/credencial do operador;
#   sem_fonte_publica    -> o artigo cita uma fonte, mas nenhuma fonte pública verificável existe hoje.
ACESSOS = ("aberto", "restrito_autorizacao", "sem_fonte_publica")
STATUS = ("acessado", "pendente_autorizacao", "pendente_fonte")
# integracao:
#   integrado            -> tem adaptador e entra nos experimentos;
#   somente_sobreposicao -> arquivos só são lidos para medir sobreposição com outros corpora;
#   pendente_fonte       -> contrato do adaptador existe (testado com fixtures sintéticas), dados não.
INTEGRACOES = ("integrado", "somente_sobreposicao", "pendente_fonte")
CAMPOS_CONDICOES = ("declarada", "identificador", "fonte_da_verificacao", "uso_pelo_projeto", "restricoes",
                    "exige_reconhecimento_do_operador", "verificado_em")
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
        if ds["integracao"] not in INTEGRACOES:
            raise CatalogoInvalido(f"{ds_id}: integracao inválida {ds['integracao']!r}")
        _validar_condicoes(ds_id, ds)
        _validar_pendente_fonte(ds_id, ds)
        for arq in ds["url_arquivos"]:
            if "arquivo" not in arq or "url" not in arq:
                raise CatalogoInvalido(f"{ds_id}: arquivo sem nome/url")
            if ds["acesso"] == "aberto" and not (arq.get("sha256") or arq.get("md5")):
                raise CatalogoInvalido(f"{ds_id}: arquivo aberto sem hash de integridade ({arq['arquivo']})")


def _validar_condicoes(ds_id: str, ds: dict[str, Any]) -> None:
    """Condições de licença são registradas ANTES de qualquer arquivo entrar no cache."""
    cond = ds["condicoes_licenca"]
    faltando = [c for c in CAMPOS_CONDICOES if c not in cond]
    if faltando:
        raise CatalogoInvalido(f"{ds_id}: condicoes_licenca sem {faltando}")
    if not cond["declarada"]:
        if not cond["exige_reconhecimento_do_operador"]:
            raise CatalogoInvalido(f"{ds_id}: licença não declarada exige reconhecimento explícito do operador antes do download")
        if not str(ds["redistribuicao"]).strip().lower().startswith("não"):
            raise CatalogoInvalido(f"{ds_id}: licença não declarada não autoriza redistribuição")
    if not cond["restricoes"]:
        raise CatalogoInvalido(f"{ds_id}: condicoes_licenca.restricoes não pode ser vazio")


def _validar_pendente_fonte(ds_id: str, ds: dict[str, Any]) -> None:
    pendente = ds["status_acesso"] == "pendente_fonte"
    if pendente != (ds["integracao"] == "pendente_fonte"):
        raise CatalogoInvalido(f"{ds_id}: status_acesso pendente_fonte e integracao pendente_fonte devem andar juntos")
    if not pendente:
        if ds["acesso"] == "sem_fonte_publica":
            raise CatalogoInvalido(f"{ds_id}: sem_fonte_publica exige status pendente_fonte")
        return
    if ds["acesso"] != "sem_fonte_publica":
        raise CatalogoInvalido(f"{ds_id}: pendente_fonte exige acesso sem_fonte_publica")
    if ds["url_arquivos"]:
        raise CatalogoInvalido(f"{ds_id}: dataset pendente_fonte não pode listar arquivos de download")
    if ds["registros_confirmados"] is not None:
        raise CatalogoInvalido(f"{ds_id}: sem leitura do arquivo, registros_confirmados deve ser null")
    for campo in ("fontes_verificadas", "ficha_cientifica"):
        if not ds.get(campo):
            raise CatalogoInvalido(f"{ds_id}: pendente_fonte exige {campo} (o que foi checado e o que o artigo declara)")


def exige_reconhecimento_de_licenca(ds_id: str) -> bool:
    return bool(dataset(ds_id)["condicoes_licenca"]["exige_reconhecimento_do_operador"])


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


# ---------------------------------------------------------------- referências adicionais
TIPOS_REFERENCIA = ("dataset_avaliado", "recurso_explicabilidade", "referencia_teorica", "artigo")
CAMPOS_REFERENCIA = ("id", "tipo", "titulo", "autores", "ano", "veiculo", "url", "citacao", "papel_no_projeto",
                     "licenca_ou_direitos", "o_que_nao_e")


@lru_cache(maxsize=1)
def carregar_referencias() -> list[dict[str, Any]]:
    """Recursos citados que não são (ou não só são) datasets integrados: escala teórica, recursos avaliados."""
    itens = _ler(paths.REFERENCIAS)["referencias"]
    ids: set[str] = set()
    for r in itens:
        faltando = [c for c in CAMPOS_REFERENCIA if c not in r]
        if faltando:
            raise CatalogoInvalido(f"referência {r.get('id')}: campos ausentes {faltando}")
        if r["tipo"] not in TIPOS_REFERENCIA:
            raise CatalogoInvalido(f"referência {r['id']}: tipo inválido {r['tipo']!r}")
        if r["id"] in ids:
            raise CatalogoInvalido(f"referência duplicada: {r['id']}")
        ids.add(r["id"])
        if r["tipo"] == "referencia_teorica" and r.get("usar_como_dataset_supervisionado") is not False:
            raise CatalogoInvalido(f"referência teórica {r['id']} deve declarar usar_como_dataset_supervisionado: false")
    return itens
