"""A cópia congelada das regras do monitor deve dar a mesma leitura que o original (quando ele existe)."""

import pytest

from eh_so_opiniao.regras_monitor.intolerancia import classificar_conteudo as copia

original = pytest.importorskip("monitor.processing.intolerancia", reason="monitor original ausente neste repositório")

TEXTOS = [
    "Quem vota nesse partido deveria sair da cidade.",
    "Discordo da gestão da saúde e vou votar contra.",
    "Esse povo que veio do Nordeste só traz atraso.",
    "Quem vive de benefício não pertence a esta cidade.",
    "Vai ter muita gente fazendo as malas depois dessa eleição kkk",
    "Se votar no candidato X, o patrão vai demitir todo mundo.",
]


@pytest.mark.parametrize("texto", TEXTOS)
def test_copia_igual_ao_original(texto):
    assert copia(texto)["labels"] == original.classificar_conteudo(texto)["labels"]
