"""Catálogo, taxonomia, mapeamento e políticas do projeto É Só Opinião?."""

from __future__ import annotations

from pathlib import Path

import pytest

from eh_so_opiniao import docsgen, paths, registry
from eh_so_opiniao.schema import AmostraInvalida, NormalizedTextSample, ler_jsonl, escrever_jsonl


def test_registry_valido_e_completo():
    dados = registry.carregar_registry()
    assert set(dados["datasets"]) == {"told_br", "hatebr"}
    for ds_id, ds in dados["datasets"].items():
        for campo in registry.CAMPOS_OBRIGATORIOS:
            assert campo in ds, f"{ds_id} sem {campo}"


def test_politicas_do_catalogo():
    pol = registry.carregar_registry()["politica_geral"]
    assert pol["corpora_brutos_no_git"] is False
    assert pol["contornar_controle_de_acesso"] is False
    assert pol["reidentificar_autores_ou_anotadores"] is False
    assert pol["usar_tybyria_como_classificador"] is False


def test_catalogo_so_tem_datasets_abertos_e_acessados():
    for ds_id in registry.listar_datasets():
        ds = registry.dataset(ds_id)
        assert ds["acesso"] == "aberto" and ds["status_acesso"] == "acessado", ds_id
        assert ds["registros_confirmados"] > 0


def test_datasets_abertos_tem_hash_de_integridade():
    for ds_id in ("told_br", "hatebr"):
        for arq in registry.dataset(ds_id)["url_arquivos"]:
            assert len(arq["sha256"]) == 64


def test_registry_rejeita_dataset_restrito_marcado_como_acessado():
    ruim = {"politica_geral": {"corpora_brutos_no_git": False, "contornar_controle_de_acesso": False},
            "datasets": {"x": {**registry.dataset("told_br"), "acesso": "restrito_autorizacao", "status_acesso": "acessado"}}}
    with pytest.raises(registry.CatalogoInvalido):
        registry.validar_registry(ruim)


def test_mapeamento_valido_e_sem_equivalente_sem_alvo():
    registry.validar_mapeamento()
    for c in registry.correspondencias():
        assert c.relacao in ("equivalente", "aproximado", "incompativel")
        if c.alvo is None:
            assert c.relacao == "incompativel"


def test_taxonomia_tem_supervisionadas_exploratorias_e_salvaguardas():
    tipos = {r["tipo"] for r in registry.rotulos_taxonomia().values()}
    assert tipos == {"supervisionado", "exploratorio", "salvaguarda"}
    for obrigatoria in ("critica_politica_legitima", "ironia_humor", "ambigua", "possivel_assedio_eleitoral_contextual",
                        "racismo", "xenofobia", "misoginia", "lgbtfobia", "desumanizacao", "discriminacao_regional"):
        assert obrigatoria in registry.rotulos_taxonomia()


def test_classes_sem_dataset_sao_exploratorias():
    com_suporte = {c.alvo for c in registry.correspondencias() if c.alvo}
    for rid, r in registry.rotulos_taxonomia().items():
        if r["tipo"] == "supervisionado":
            assert rid in com_suporte, f"{rid} marcada como supervisionada sem rótulo mapeado"
        if r["tipo"] == "exploratorio":
            assert rid not in com_suporte, f"{rid} exploratória não deveria ter rótulo mapeado"


def test_docs_gerados_em_sincronia_com_os_catalogos():
    for nome, fn in (("MAPEAMENTO_ROTULOS.md", docsgen.mapeamento_md), ("TAXONOMIA.md", docsgen.taxonomia_md), ("DATASETS.md", docsgen.datasets_md)):
        atual = (paths.DOCS / nome).read_text(encoding="utf-8")
        assert atual == fn(), f"{nome} desatualizado: rode `python -m eh_so_opiniao docs`"


def test_codigo_nao_referencia_tybyria():
    for arq in Path(paths.RAIZ).rglob("*.py"):
        partes = arq.relative_to(paths.RAIZ).parts
        if "tests" in partes or any(p.startswith(".") or p.endswith(".egg-info") for p in partes):
            continue  # testes e ambientes virtuais  # os testes citam a TybyrIA justamente para garantir que a política a proíbe
        assert "tybyr" not in arq.read_text(encoding="utf-8").lower(), arq


def test_gitignore_protege_corpora_brutos():
    texto = (paths.RAIZ / ".gitignore").read_text(encoding="utf-8")  # .gitignore dentro da própria pasta
    for linha in ("datasets/_local/", "relatorios/local/", "site/data/_rascunho/", ".env"):
        assert linha in texto.splitlines()


def _amostra(**mudancas) -> NormalizedTextSample:
    base = dict(sample_id="x:1", dataset_id="told_br", source_platform="twitter", text="texto",
                license="CC", provenance={"origem": "fixture_sintetica"})
    base.update(mudancas)
    return NormalizedTextSample(**base)


def test_esquema_valida_e_rejeita():
    _amostra().validar()
    with pytest.raises(AmostraInvalida):
        _amostra(text="  ").validar()
    with pytest.raises(AmostraInvalida):
        _amostra(license="").validar()
    with pytest.raises(AmostraInvalida):
        _amostra(provenance={"origem": "inventada"}).validar()
    with pytest.raises(AmostraInvalida):
        _amostra(toxic_spans=[{"start": 0, "end": 999, "origin": "anotado"}]).validar()
    with pytest.raises(AmostraInvalida):
        _amostra(normalized_labels={"racismo": {"value": 1, "relation": "equivalente"}}).validar()
    with pytest.raises(AmostraInvalida):
        _amostra(split="treino").validar()


def test_esquema_aceita_valor_ausente_e_faz_roundtrip(tmp_path):
    a = _amostra(normalized_labels={"racismo": {"value": None, "relation": "aproximado"}}).validar()
    assert a.valor("racismo") is None and a.valor("inexistente") is None
    destino = tmp_path / "a.jsonl"
    assert escrever_jsonl([a], destino) == 1
    assert list(ler_jsonl(destino))[0].to_dict() == a.to_dict()
