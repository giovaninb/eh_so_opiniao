"""Catálogo ampliado: validação do registry, porta de licença, pendente_fonte, referências, docs e relatórios sem texto bruto."""

from __future__ import annotations

import copy
import hashlib
import io
import json

import pytest

from eh_so_opiniao import docsgen, paths, registry
from eh_so_opiniao.pipeline import download, normalize

import fixtures_multidomain as F  # noqa: E402

CONTEUDO = b"text,label\nexemplo sintetico,1\n"


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _registry_com(ds_id: str, **mudancas):
    base = copy.deepcopy(registry.carregar_registry())
    base["datasets"][ds_id].update(mudancas)
    return base


@pytest.fixture
def dados_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("ESO_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("ESO_ACEITE_LICENCA", raising=False)
    return tmp_path


def _falso_com_licenca_pendente(monkeypatch, exige: bool = True):
    info = copy.deepcopy(registry.dataset("multidomain_yt_toxbr"))
    info["condicoes_licenca"]["exige_reconhecimento_do_operador"] = exige
    info["url_arquivos"] = [{"arquivo": "dados.csv", "url": "https://exemplo.invalid/dados.csv", "sha256": hashlib.sha256(CONTEUDO).hexdigest()}]
    monkeypatch.setattr(registry, "dataset", lambda ds_id: info)
    return info


# --------------------------------------------------------------------- validação do registry
def test_racismobr_e_pendente_de_fonte_sem_numero_inventado():
    r = registry.dataset("racismobr")
    assert r["status_acesso"] == "pendente_fonte" and r["integracao"] == "pendente_fonte" and r["acesso"] == "sem_fonte_publica"
    assert r["registros_confirmados"] is None and r["url_arquivos"] == []
    assert r["registros_declarados_no_artigo"]  # o número do artigo fica separado do confirmado
    assert any("404" in f["resultado"] for f in r["fontes_verificadas"])
    ficha = r["ficha_cientifica"]
    for campo in ("definicao_operacional", "rotulos_originais_binarios", "proveniencia", "composicao_de_classes", "anotacao_e_consenso", "limitacoes_de_amostragem"):
        assert campo in ficha, campo
    assert "subconjunto_experimental_balanceado" in ficha["composicao_de_classes"]  # separado do corpus original


def test_mdyt_registra_condicoes_de_licenca_antes_de_integrar():
    m = registry.dataset("multidomain_yt_toxbr")
    c = m["condicoes_licenca"]
    assert c["declarada"] is False and c["exige_reconhecimento_do_operador"] is True
    assert m["redistribuicao"].lower().startswith("não")
    assert any("fins acadêmicos" in r for r in c["restricoes"])
    assert m["ficha_cientifica"]["ordem_do_vetor_multirrotulo"]["divergencia_do_readme"]


def test_tupye_so_serve_para_sobreposicao():
    t = registry.dataset("tupye")
    assert t["integracao"] == "somente_sobreposicao"
    assert not any(c.alvo for c in registry.correspondencias("tupye") if c.relacao == "equivalente")


def test_licenca_nao_declarada_exige_reconhecimento_e_nao_redistribui():
    ruim = _registry_com("multidomain_yt_toxbr")
    ruim["datasets"]["multidomain_yt_toxbr"]["condicoes_licenca"]["exige_reconhecimento_do_operador"] = False
    with pytest.raises(registry.CatalogoInvalido, match="reconhecimento"):
        registry.validar_registry(ruim)
    ruim = _registry_com("multidomain_yt_toxbr", redistribuicao="Sim, livre.")
    with pytest.raises(registry.CatalogoInvalido, match="redistribuição"):
        registry.validar_registry(ruim)


def test_pendente_fonte_nao_aceita_arquivos_nem_contagem_nem_acesso_aberto():
    for mud, trecho in (({"url_arquivos": [{"arquivo": "x", "url": "https://x"}]}, "arquivos"), ({"registros_confirmados": 1054}, "registros_confirmados"),
                        ({"acesso": "aberto"}, "sem_fonte_publica"), ({"integracao": "integrado"}, "andar juntos"), ({"fontes_verificadas": []}, "fontes_verificadas")):
        with pytest.raises(registry.CatalogoInvalido, match=trecho):
            registry.validar_registry(_registry_com("racismobr", **mud))


def test_acesso_sem_fonte_publica_exige_status_pendente_fonte():
    with pytest.raises(registry.CatalogoInvalido):
        registry.validar_registry(_registry_com("told_br", acesso="sem_fonte_publica"))


def test_dataset_aberto_sem_hash_e_rejeitado():
    ruim = _registry_com("told_br")
    ruim["datasets"]["told_br"]["url_arquivos"] = [{"arquivo": "x.csv", "url": "https://exemplo.invalid/x.csv"}]
    with pytest.raises(registry.CatalogoInvalido, match="hash"):
        registry.validar_registry(ruim)


def test_condicoes_de_licenca_incompletas_sao_rejeitadas():
    ruim = _registry_com("hatebr")
    del ruim["datasets"]["hatebr"]["condicoes_licenca"]["restricoes"]
    with pytest.raises(registry.CatalogoInvalido, match="condicoes_licenca"):
        registry.validar_registry(ruim)


# ------------------------------------------------------------------ taxonomia e mapeamento
def test_classes_novas_existem_e_relacoes_do_mdyt_sao_todas_aproximadas():
    tax = registry.rotulos_taxonomia()
    for classe in ("capacitismo", "intolerancia_religiosa", "hostilidade_politica", "incitacao_violencia"):
        assert classe in tax and tax[classe]["tipo"] == "supervisionado"
    mdyt = [c for c in registry.correspondencias("multidomain_yt_toxbr")]
    assert {c.original for c in mdyt} >= set(F.CLASSES)
    assert all(c.relacao in ("aproximado", "incompativel") for c in mdyt)  # nenhuma equivalência assumida
    assert registry.correspondencia("multidomain_yt_toxbr", "invalido").alvo is None


def test_classes_regionais_continuam_exploratorias():
    com_dataset = {c.alvo for c in registry.correspondencias() if c.alvo}
    for classe in ("discriminacao_regional", "possivel_assedio_eleitoral_contextual", "critica_politica_legitima"):
        assert classe not in com_dataset
        assert registry.rotulos_taxonomia()[classe]["tipo"] != "supervisionado"


def test_escala_de_preconceito_e_referencia_teorica_e_nao_gera_rotulo():
    refs = {r["id"]: r for r in registry.carregar_referencias()}
    epn = refs["epn_psico_2025"]
    assert epn["tipo"] == "referencia_teorica" and epn["usar_como_dataset_supervisionado"] is False
    assert not any("epn" in c.dataset_id for c in registry.correspondencias())


def test_referencia_teorica_nao_pode_ser_marcada_como_dataset(monkeypatch):
    registry.carregar_referencias.cache_clear()
    monkeypatch.setattr(registry, "_ler", lambda p: {"referencias": [{c: "x" for c in registry.CAMPOS_REFERENCIA} | {"tipo": "referencia_teorica", "id": "r1",
                                                                       "usar_como_dataset_supervisionado": True}]})
    with pytest.raises(registry.CatalogoInvalido, match="usar_como_dataset_supervisionado"):
        registry.carregar_referencias()
    registry.carregar_referencias.cache_clear()


# ------------------------------------------------------------------------ porta de licença
def test_download_sem_reconhecimento_de_licenca_nao_toca_a_rede(dados_tmp, monkeypatch):
    _falso_com_licenca_pendente(monkeypatch)

    def proibido(req):
        raise AssertionError("não deveria abrir conexão")

    r = download.baixar("falso", abrir=proibido)[0]
    assert r.status == "pendente_licenca" and not (dados_tmp / "bruto" / "falso" / "dados.csv").exists()


def test_download_com_reconhecimento_grava_aceite_no_manifest(dados_tmp, monkeypatch):
    _falso_com_licenca_pendente(monkeypatch)
    r = download.baixar("falso", abrir=lambda req: _Resp(CONTEUDO), aceito_licenca=True)[0]
    assert r.status == "baixado"
    manifest = json.loads((dados_tmp / "bruto" / "falso" / "manifest.json").read_text(encoding="utf-8"))
    aceite = manifest["aceite_de_licenca"]
    assert aceite["reconhecido_pelo_operador"] is True and aceite["restricoes"] and aceite["em"]


def test_reconhecimento_por_variavel_de_ambiente_so_vale_para_o_dataset_nomeado(dados_tmp, monkeypatch):
    monkeypatch.setenv("ESO_ACEITE_LICENCA", "outro_dataset, multidomain_yt_toxbr")
    assert download.licenca_reconhecida("multidomain_yt_toxbr") and not download.licenca_reconhecida("racismobr")
    monkeypatch.setenv("ESO_ACEITE_LICENCA", "outro_dataset")
    assert not download.licenca_reconhecida("multidomain_yt_toxbr")


def test_dataset_com_licenca_declarada_nao_exige_reconhecimento(dados_tmp, monkeypatch):
    _falso_com_licenca_pendente(monkeypatch, exige=False)
    assert download.baixar("falso", abrir=lambda req: _Resp(CONTEUDO))[0].status == "baixado"


def test_cache_existente_nao_pede_licenca_de_novo(dados_tmp, monkeypatch):
    _falso_com_licenca_pendente(monkeypatch)
    download.baixar("falso", abrir=lambda req: _Resp(CONTEUDO), aceito_licenca=True)
    assert download.baixar("falso", abrir=lambda req: pytest.fail("rede"))[0].status == "em_cache"


def test_baixar_dataset_pendente_fonte_nao_tenta_rede(dados_tmp):
    def proibido(req):
        raise AssertionError("não deveria abrir conexão")

    r = download.baixar("racismobr", abrir=proibido)
    assert [x.status for x in r] == ["pendente_fonte"]


def test_hash_do_mdyt_diverge_e_arquivo_e_descartado(dados_tmp, monkeypatch):
    info = _falso_com_licenca_pendente(monkeypatch)
    info["url_arquivos"][0]["sha256"] = "0" * 64
    r = download.baixar("falso", abrir=lambda req: _Resp(CONTEUDO), aceito_licenca=True)[0]
    assert r.status == "falha_integridade" and not (dados_tmp / "bruto" / "falso" / "dados.csv").exists()


# ------------------------------------------------------------------------- normalização
def test_normalizar_pendente_fonte_e_somente_sobreposicao_nao_leem_dados(dados_tmp):
    r = normalize.normalizar_dataset("racismobr")
    assert r["status"] == "pendente_fonte" and r["amostras"] == 0
    t = normalize.normalizar_dataset("tupye")
    assert t["status"] == "nao_normalizado" and t["amostras"] == 0
    assert not (dados_tmp / "normalizado" / "racismobr.jsonl").exists() and not (dados_tmp / "normalizado" / "tupye.jsonl").exists()


def test_normalizar_mdyt_com_cache_sintetico(dados_tmp, monkeypatch):
    b, m = F.escrever_csvs(dados_tmp / "src")
    x = F.escrever_planilhas(dados_tmp / "src" / "xlsx")
    arquivos = {"multiDomainYtBinary.csv": b, "multiDomainYtMultilabel.csv": m, **{f"comentariosParaAnotacao{k}.xlsx": x[k - 1] for k in range(1, 7)}}

    def valida(ds_id, arq):
        return type("R", (), {"status": "integridade_ok", "caminho": str(arquivos[arq["arquivo"]])})()

    monkeypatch.setattr(download, "validar_integridade", valida)
    r = normalize.normalizar_dataset("multidomain_yt_toxbr")
    assert r["status"] == "normalizado" and r["amostras"] == 12
    assert r["relatorio_adaptador"]["ordem_vetor"] == "confirmada_pelas_planilhas"
    assert set(r["rotulos_normalizados"]) >= {"racismo", "xenofobia", "capacitismo", "linguagem_ofensiva"}
    assert (dados_tmp / "normalizado" / "multidomain_yt_toxbr.jsonl").exists()


# -------------------------------------------------------------------------------- docs
def test_docs_gerados_em_sincronia(tmp_path):
    for nome, fn in docsgen.GERADOS.items():
        if nome == "RESULTADOS.md":
            continue  # depende dos relatórios locais, validados à parte
        assert (paths.DOCS / nome).read_text(encoding="utf-8") == fn(), f"{nome} desatualizado: rode `python -m eh_so_opiniao docs`"


def test_referencias_md_lista_todos_os_datasets_e_deixa_a_escala_como_teorica():
    md = docsgen.referencias_md()
    for ds_id in registry.listar_datasets():
        assert registry.dataset(ds_id)["url_origem"] in md
    assert "Referências teóricas (não são datasets)" in md and "NÃO é dataset de comentários" in md
    assert "https://aclanthology.org/2026.propor-1.76/" in md and "https://aclanthology.org/2026.stil-1.36/" in md


def test_compatibilidade_md_nao_funde_datasets_e_cita_sobreposicao():
    md = docsgen.compatibilidade_md()
    assert "NÃO são fundidos" in md and "Sobreposição de textos" in md
    for ds_id in registry.listar_datasets():
        assert ds_id in md


def test_datasets_md_mostra_pendencia_e_condicoes_de_licenca():
    md = docsgen.datasets_md()
    assert "não confirmado (nenhum arquivo foi lido)" in md and "**Pendência**" in md
    assert "reconhecimento explícito do operador" in md


# ------------------------------------------------- relatórios versionados sem texto bruto
def _todos_os_textos_locais():
    pasta = paths.normalizados()
    textos = []
    if pasta.exists():
        for arq in pasta.glob("*.jsonl"):
            with arq.open(encoding="utf-8") as f:
                textos += [json.loads(l)["text"] for l in f if l.strip()]
    return [t for t in textos if len(t) >= 40]


def test_relatorios_e_site_nao_contem_texto_dos_corpora():
    textos = _todos_os_textos_locais()
    if not textos:
        pytest.skip("corpora não normalizados neste ambiente")
    publico = ""
    for pasta in (paths.RELATORIOS, paths.SITE / "data", paths.DOCS):
        for arq in pasta.glob("*.json" if pasta != paths.DOCS else "*.md"):
            publico += arq.read_text(encoding="utf-8")
    achados = [t for t in textos if t in publico]
    assert not achados, f"{len(achados)} texto(s) de corpus em arquivos publicáveis"
