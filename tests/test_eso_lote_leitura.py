"""Revisão em lote que muda a leitura (tipo): `sem_discriminacao` e correção de ambígua para exclusão."""

from __future__ import annotations

import csv
import json

import pytest

from eh_so_opiniao import casos, publicacao
from eh_so_opiniao.review import lote, store


@pytest.fixture
def conn(tmp_path):
    c = store.abrir(tmp_path / "rev.sqlite3")
    casos.enfileirar(c)
    yield c
    c.close()


def _folha(tmp_path, linhas):
    arq = tmp_path / "folha.csv"
    with open(arq, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=lote.COLUNAS_COMPACTAS)
        w.writeheader()
        for l in linhas:
            w.writerow({c: l.get(c, "") for c in lote.COLUNAS_COMPACTAS})
    return arq


def _ambigua(conn):
    return next(l["id"] for l in store.listar(conn) if l["tipo"] == "ambigua" and l["origem"] != store.ORIGEM_VISITANTE)


def test_sem_discriminacao_muda_a_leitura_sem_rotulos_e_registra_no_historico(conn, tmp_path):
    iid = _ambigua(conn)
    r = lote.aplicar_folha(conn, _folha(tmp_path, [{"id": iid, "decisao": "corrigir", "rotulos_finais": "sem_discriminacao", "nota": "Pergunta respeitosa."}]), "revisora-teste")
    assert r["erros"] == [] and r["aplicadas"] == 1
    l = conn.execute("SELECT * FROM itens WHERE id=?", (iid,)).fetchone()
    assert (l["estado"], l["tipo"], json.loads(l["rotulos_humanos"])) == ("Corrigido", "nao_discriminatoria", [])
    assert "ambigua -> nao_discriminatoria" in store.historico(conn, iid)[-1]["nota"]
    pub = {f["id"]: f for f in publicacao.exportar_frases(conn)["frases"]}[iid]
    assert pub["tipo"] == "nao_discriminatoria" and pub["rotulos"] == []


def test_sem_discriminacao_nao_se_mistura_com_outros_rotulos(conn, tmp_path):
    iid = _ambigua(conn)
    r = lote.aplicar_folha(conn, _folha(tmp_path, [{"id": iid, "decisao": "corrigir", "rotulos_finais": "sem_discriminacao, misoginia", "nota": "x"}]), "revisora-teste")
    assert r["aplicadas"] == 0 and "não pode vir junto" in r["erros"][0]
    assert conn.execute("SELECT estado FROM itens WHERE id=?", (iid,)).fetchone()["estado"] == "Pendente"


def test_corrigir_ambigua_com_rotulo_de_discriminacao_vira_exclusao(conn, tmp_path):
    iid = _ambigua(conn)
    lote.aplicar_folha(conn, _folha(tmp_path, [{"id": iid, "decisao": "corrigir", "rotulos_finais": "misoginia", "nota": "Não depende de contexto."}]), "revisora-teste")
    assert conn.execute("SELECT tipo FROM itens WHERE id=?", (iid,)).fetchone()["tipo"] == "exclusao"


def test_so_corrigir_pode_mudar_a_leitura_e_tipo_invalido_e_recusado(conn):
    iid = _ambigua(conn)
    with pytest.raises(store.RevisaoInvalida, match="só uma correção"):
        store._mudar(conn, iid, "Aprovado", "revisora-teste", None, tipo="exclusao")
    with pytest.raises(store.RevisaoInvalida, match="tipo inválido"):
        store.corrigir(conn, iid, "revisora-teste", [], "n", tipo="qualquer")


def test_corrigir_sem_tipo_preserva_a_leitura(conn):
    iid = next(l["id"] for l in store.listar(conn) if l["tipo"] == "exclusao" and l["origem"] != store.ORIGEM_VISITANTE)
    store.corrigir(conn, iid, "revisora-teste", ["racismo"], "só rótulo")
    assert conn.execute("SELECT tipo FROM itens WHERE id=?", (iid,)).fetchone()["tipo"] == "exclusao"
