"""Linha de comando do projeto É Só Opinião?."""

from __future__ import annotations

import pytest

from eh_so_opiniao import cli, paths
from eh_so_opiniao.review import store


@pytest.fixture(autouse=True)
def dados_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("ESO_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("HF_TOKEN", raising=False)


def test_datasets_lista_catalogo(capsys):
    assert cli.main(["datasets"]) == 0
    saida = capsys.readouterr().out
    for ds in ("told_br", "hatebr", "olid_br"):
        assert ds in saida
    assert "lgbtqia" not in saida and "mina_br" not in saida


def test_mapeamento_imprime_tabela(capsys):
    assert cli.main(["mapeamento"]) == 0
    assert "| told_br | `racism` | racismo | equivalente |" in capsys.readouterr().out


def test_fluxo_de_revisao_pela_cli(capsys, tmp_path):
    assert cli.main(["casos"]) == 0
    assert "todos como Pendente" in capsys.readouterr().out
    assert cli.main(["revisao", "aprovar", "--id", "FR-06"]) == 2  # sem revisor
    assert cli.main(["revisao", "aprovar", "--id", "FR-06", "--revisor", "Revisora"]) == 0
    assert cli.main(["revisao", "corrigir", "--id", "FR-01", "--revisor", "R", "--rotulos", "inventado"]) == 2
    assert cli.main(["revisao", "listar", "--estado", "Aprovado"]) == 0
    assert "FR-06" in capsys.readouterr().out
    assert cli.main(["revisao", "historico", "--id", "FR-06"]) == 0
    assert cli.main(["revisao", "aprovar", "--id", "NAO-EXISTE", "--revisor", "R"]) == 2


def test_site_pela_cli_publica_so_aprovadas(tmp_path, monkeypatch, capsys):
    destino = tmp_path / "site_data"
    monkeypatch.setattr(paths, "SITE", tmp_path / "site")
    cli.main(["casos"])
    cli.main(["revisao", "aprovar", "--id", "FR-08", "--revisor", "R"])
    assert cli.main(["site"]) == 0
    assert "1 frase(s) revisada(s) publicada(s)" in capsys.readouterr().out
    assert (tmp_path / "site" / "data" / "frases.json").exists()
    assert destino.exists() is False
