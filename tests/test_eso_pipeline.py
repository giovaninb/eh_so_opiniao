"""Download com integridade, travas de acesso, normalização e splits sem vazamento."""

from __future__ import annotations

import hashlib
import io
import urllib.error

import pytest

from eh_so_opiniao import registry
from eh_so_opiniao.adapters import HateBrAdapter, ToldBrAdapter
from eh_so_opiniao.adapters.base import marcar_como_fixture
from eh_so_opiniao.paths import RAIZ
from eh_so_opiniao.pipeline import download, normalize, splits
from eh_so_opiniao.schema import NormalizedTextSample

FX = RAIZ / "fixtures"
CONTEUDO = b"id,texto\n1,exemplo sintetico\n"


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def dados_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("ESO_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("HF_TOKEN", raising=False)
    return tmp_path


def _falso_dataset(monkeypatch, sha: str | None = None, acesso: str = "aberto", **extra):
    info = {**registry.dataset("told_br"), "acesso": acesso, "status_acesso": "acessado" if acesso == "aberto" else "pendente_autorizacao",
            "url_arquivos": [{"arquivo": "dados.csv", "url": "https://exemplo.invalid/dados.csv",
                              "sha256": sha or hashlib.sha256(CONTEUDO).hexdigest(), **extra}]}
    monkeypatch.setattr(registry, "dataset", lambda ds_id: info)
    return info


def test_download_valida_hash_grava_manifest_e_usa_cache(dados_tmp, monkeypatch):
    _falso_dataset(monkeypatch)
    chamadas = []

    def abrir(req):
        chamadas.append(req.full_url)
        return _Resp(CONTEUDO)

    r = download.baixar("falso", abrir=abrir)[0]
    assert r.status == "baixado" and (dados_tmp / "bruto" / "falso" / "dados.csv").read_bytes() == CONTEUDO
    assert (dados_tmp / "bruto" / "falso" / "manifest.json").exists()
    r2 = download.baixar("falso", abrir=abrir)[0]
    assert r2.status == "em_cache" and len(chamadas) == 1  # não baixou de novo


def test_download_com_hash_divergente_descarta_arquivo(dados_tmp, monkeypatch):
    _falso_dataset(monkeypatch, sha="0" * 64)
    r = download.baixar("falso", abrir=lambda req: _Resp(CONTEUDO))[0]
    assert r.status == "falha_integridade"
    assert not (dados_tmp / "bruto" / "falso" / "dados.csv").exists()
    assert not list((dados_tmp / "bruto" / "falso").glob("*.parte"))


def test_cache_corrompido_e_rebaixado(dados_tmp, monkeypatch):
    _falso_dataset(monkeypatch)
    download.baixar("falso", abrir=lambda req: _Resp(CONTEUDO))
    (dados_tmp / "bruto" / "falso" / "dados.csv").write_bytes(b"corrompido")
    r = download.baixar("falso", abrir=lambda req: _Resp(CONTEUDO))[0]
    assert r.status == "baixado"


def test_dataset_restrito_sem_token_nao_tenta_rede(dados_tmp, monkeypatch):
    _falso_dataset(monkeypatch, acesso="restrito_autorizacao")

    def proibido(req):
        raise AssertionError("não deveria acessar a rede sem credencial")

    r = download.baixar("falso", abrir=proibido)[0]
    assert r.status == "pendente_autorizacao"


def test_dataset_restrito_com_401_fica_pendente_sem_derrubar(dados_tmp, monkeypatch):
    _falso_dataset(monkeypatch, acesso="restrito_autorizacao")

    def nega(req):
        raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, None)

    r = download.baixar("falso", token="token-qualquer", abrir=nega)[0]
    assert r.status == "pendente_autorizacao" and "401" in r.detalhe


def test_token_vai_so_no_cabecalho_do_pedido(dados_tmp, monkeypatch):
    _falso_dataset(monkeypatch, acesso="restrito_autorizacao", sha256=None)
    info = registry.dataset("falso")
    info["url_arquivos"][0]["sha256"] = None
    info["url_arquivos"][0]["md5"] = hashlib.md5(CONTEUDO).hexdigest()  # noqa: S324
    vistos = {}

    def abrir(req):
        vistos["auth"] = req.get_header("Authorization")
        vistos["url"] = req.full_url
        return _Resp(CONTEUDO)

    r = download.baixar("falso", token="abc", abrir=abrir)[0]
    assert r.status == "baixado" and vistos["auth"] == "Bearer abc" and "abc" not in vistos["url"]


def test_normalizacao_sem_cache_nao_derruba_o_pipeline(dados_tmp):
    relatorio = normalize.normalizar_todos()
    assert set(relatorio) == {"told_br", "hatebr", "multidomain_yt_toxbr", "racismobr", "tupye"}
    esperado = {"told_br": "ausente_no_cache", "hatebr": "ausente_no_cache", "multidomain_yt_toxbr": "ausente_no_cache",  # cache vazio: não é falha
                "racismobr": "pendente_fonte", "tupye": "nao_normalizado"}
    assert {k: r["status"] for k, r in relatorio.items()} == esperado
    assert all(r["amostras"] == 0 for r in relatorio.values())


# ----------------------------------------------------------------------- splits
def _amostras_hatebr(n_posts=10, por_post=12):
    out = []
    for p in range(n_posts):
        for i in range(por_post):
            a = NormalizedTextSample(sample_id=f"h:{p}:{i}", dataset_id="hatebr", source_platform="instagram", text=f"comentario {p} numero {i} unico {p*100+i}",
                                     license="x", provenance={"origem": "fixture_sintetica"}, context={"post_group": f"post{p}"})
            out.append(a)
    return out


def test_split_por_publicacao_nao_mistura_publicacoes():
    am = _amostras_hatebr()
    destino = splits.dividir(am, splits.grupo_por_publicacao, None, 7)
    splits.aplicar(am, destino)
    assert splits.auditar_vazamento(am)["publicacoes_em_mais_de_um_split"] == 0
    assert {a.split for a in am} == {"train", "validation", "test"}


def test_split_agrupa_quase_duplicatas_e_e_deterministico():
    base = ["Exemplo sintético número {}".format(i) for i in range(60)]
    am = []
    for i, t in enumerate(base):
        for j, variante in enumerate((t, "RT @alguem " + t.upper() + "!!", t + " http://x.invalid/abc")):
            am.append(NormalizedTextSample(sample_id=f"t:{i}:{j}", dataset_id="told_br", source_platform="twitter", text=variante,
                                           license="x", provenance={"origem": "fixture_sintetica"}))
    d1 = splits.dividir(am, splits.grupo_por_texto, None, 3)
    d2 = splits.dividir(am, splits.grupo_por_texto, None, 3)
    d3 = splits.dividir(am, splits.grupo_por_texto, None, 4)
    assert d1 == d2 and d1 != d3
    splits.aplicar(am, d1)
    assert splits.auditar_vazamento(am)["textos_em_mais_de_um_split"] == 0


def test_remocao_de_duplicatas_cruzadas_cobre_treino_validacao_e_teste():
    def mk(i, t, s):
        return NormalizedTextSample(sample_id=f"x:{i}", dataset_id="d", source_platform=None, text=t, license="x",
                                    provenance={"origem": "fixture_sintetica"}, split=s)
    am = [mk(1, "mesmo texto", "train"), mk(2, "Mesmo texto!", "test"), mk(3, "outro texto", "validation"),
          mk(4, "OUTRO texto", "test"), mk(5, "único no teste", "test")]
    mantidas, removidas = splits.remover_duplicatas_cruzadas(am)
    assert {a.sample_id for a in mantidas} == {"x:1", "x:3", "x:5"}
    assert removidas == {"test": 2}
    assert splits.auditar_vazamento(mantidas)["textos_em_mais_de_um_split"] == 0


def test_sobreposicao_entre_corpora():
    a = marcar_como_fixture(ToldBrAdapter(FX / "told_br_sintetico.csv").todas())
    b = marcar_como_fixture(HateBrAdapter(FX / "hatebr_sintetico.csv").todas())
    assert splits.sobreposicao_entre_corpora(a, b) == set()
    assert len(splits.sobreposicao_entre_corpora(a, a)) > 0
