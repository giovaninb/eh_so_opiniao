"""Importação, esquema v2, relatórios locais e retenção — sem falar com o Formspree."""

from __future__ import annotations

import importlib
import json
from email.message import EmailMessage
from pathlib import Path

import pytest

from eh_so_opiniao import analytics, participacao_esquema as esq
from eh_so_opiniao.review import store

FIXTURES = Path(__file__).parent / "fixtures" / "participacoes"


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(importlib.import_module("eh_so_opiniao.analytics.importar"), "dados_locais", lambda: tmp_path)
    c = store.abrir(tmp_path / "rev.sqlite3")
    yield c
    c.close()


def test_versao_editorial_e_deterministica():
    f = {
        "id": "EX-154",
        "texto": "Vou perguntar diretamente à pessoa com deficiência se precisa de alguma adaptação.",
        "tipo": "nao_discriminatoria",
        "contexto": "Situação de atendimento.",
        "mecanismo": "Pergunta objetiva.",
        "razoes": ["A pessoa decide."],
        "muda_se": "Se houvesse tom de pena.",
        "rotulos": [{"id": "capacitismo", "nome": "Capacitismo"}],
        "aviso_conteudo": False,
    }
    a = esq.versao_editorial(f)
    b = esq.versao_editorial({**f, "rotulos": [{"id": "capacitismo"}]})
    assert a == b and len(a) == 12
    assert esq.versao_editorial({**f, "texto": f["texto"] + " "}) != a


def test_compatibilidade_tipos_legado():
    assert esq.tipo_canonico("voto") == "avaliacoes_voluntarias"
    assert esq.tipo_canonico("frase") == "sugestao_frase"
    assert esq.tipo_canonico("discordancia") == "contestacao"
    assert esq.tipo_canonico("avaliacoes") == "avaliacoes_voluntarias"
    assert not esq.consentiu("")
    assert not esq.consentiu("presumido")
    assert esq.consentiu("sim")


def test_importa_csv_legado_e_lote_v2(conn, tmp_path):
    csv = tmp_path / "legado.csv"
    csv.write_text("tipo,frase,avaliacao,frase_id,consentimento,site\nvoto,,opiniao,EX-01,sim,\n", encoding="utf-8")
    r1 = analytics.importar(conn, csv)["resumo"]
    lote = tmp_path / "lote.json"
    lote.write_text(json.dumps({
        "schema_version": "2", "tipo": "avaliacoes_voluntarias", "consentimento": "sim",
        "avaliacoes": [
            {"frase_id": "EX-01", "conteudo_versao": "abc123abc123", "tema_id": "t", "modo": "descobrir",
             "avaliacao": "discriminacao", "contexto_exibido": "sim", "analise_revelada": "nao"},
            {"frase_id": "EX-02", "conteudo_versao": "abc123abc123", "tema_id": "t", "modo": "descobrir",
             "avaliacao": "contexto", "contexto_exibido": "nao", "analise_revelada": "nao"},
        ],
    }), encoding="utf-8")
    r2 = analytics.importar(conn, lote)["resumo"]
    assert r1["votos"] == 1
    assert r2["votos"] == 2 and r2["submissoes_lote"] == 1
    assert conn.execute("SELECT COUNT(*) FROM votos").fetchone()[0] == 3


def test_lote_maior_que_cinco_e_sem_consentimento(conn, tmp_path):
    itens = [{"frase_id": f"EX-0{i}", "avaliacao": "opiniao", "conteudo_versao": "v"} for i in range(1, 7)]
    arq = tmp_path / "grande.json"
    arq.write_text(json.dumps({"tipo": "avaliacoes_voluntarias", "consentimento": "sim", "avaliacoes": itens}), encoding="utf-8")
    # o normalizador corta em 5; não rejeita o arquivo inteiro
    r = analytics.importar(conn, arq)["resumo"]
    assert r.get("descartada_lote_maior_que_cinco") == 1
    assert conn.execute("SELECT COUNT(*) FROM votos").fetchone()[0] == 0
    sem = tmp_path / "sem.json"
    sem.write_text(json.dumps({"tipo": "avaliacoes_voluntarias", "avaliacoes": itens[:1]}), encoding="utf-8")
    assert "descartada_sem_consentimento" in analytics.importar(conn, sem)["resumo"]


def test_json_malformado_e_campo_proibido(conn, tmp_path):
    ruim = tmp_path / "ruim.json"
    ruim.write_text("{nao json", encoding="utf-8")
    r = analytics.importar(conn, ruim)
    assert r["resumo"]["arquivo_invalido"] == 1
    email = tmp_path / "email.json"
    email.write_text(json.dumps({
        "tipo": "sugestao_frase", "frase": "Frase boa o bastante para valer",
        "avaliacao": "opiniao", "consentimento": "sim", "email": "a@b.c",
    }), encoding="utf-8")
    assert "descartada_campo_proibido_email" in analytics.importar(conn, email)["resumo"]


def test_contestacao_e_sugestao(conn, tmp_path):
    arq = tmp_path / "c.json"
    arq.write_text(json.dumps([
        {"tipo": "contestacao", "frase_id": "EX-01", "motivo": "falta_contexto",
         "comentario": "Falta o cenário.", "consentimento": "sim", "schema_version": "2"},
        {"tipo": "sugestao_frase", "frase": "Qual nome você prefere que eu use agora?",
         "avaliacao": "contexto", "contexto": "Pergunta a uma pessoa, sem tom pejorativo.",
         "consentimento": "sim"},
    ]), encoding="utf-8")
    r = analytics.importar(conn, arq)["resumo"]
    assert r["contestacoes"] == 1 and r["frases_novas"] == 1


def test_eml_heuristico(conn, tmp_path):
    msg = EmailMessage()
    msg["From"] = "form@example.test"
    msg["Subject"] = "New submission"
    msg.set_content("tipo: contestacao\nfrase_id: EX-01\nmotivo: erro_no_texto\ncomentario: Há um typo.\nconsentimento: sim\n")
    arq = tmp_path / "aviso.eml"
    arq.write_bytes(bytes(msg))
    r = analytics.importar(conn, arq)["resumo"]
    assert r["contestacoes"] == 1


def test_duplicata_operacional_nao_e_fingerprint(conn, tmp_path):
    linha = "voto,,opiniao,EX-01,sim,"
    arq = tmp_path / "dup.csv"
    arq.write_text("tipo,frase,avaliacao,frase_id,consentimento,site\n" + linha + "\n" + linha + "\n", encoding="utf-8")
    r = analytics.importar(conn, arq)["resumo"]
    assert r["votos"] == 2
    assert analytics.importar(conn, arq)["resumo"]["ja_importadas"] == 2


def test_relatorios_contam_submissao_e_avaliacoes_separadas(conn, tmp_path):
    lote = tmp_path / "lote.json"
    lote.write_text(json.dumps({
        "tipo": "avaliacoes_voluntarias", "consentimento": "sim",
        "avaliacoes": [
            {"frase_id": "EX-01", "avaliacao": "opiniao", "conteudo_versao": "v1", "tema_id": "racismo"},
            {"frase_id": "EX-01", "avaliacao": "discriminacao", "conteudo_versao": "v1", "tema_id": "racismo"},
            {"frase_id": "EX-01", "avaliacao": "contexto", "conteudo_versao": "v1", "tema_id": "racismo"},
            {"frase_id": "EX-02", "avaliacao": "opiniao", "conteudo_versao": "v1", "tema_id": "racismo"},
            {"frase_id": "EX-01", "avaliacao": "opiniao", "conteudo_versao": "v2", "tema_id": "racismo"},
        ],
    }), encoding="utf-8")
    analytics.importar(conn, lote)
    contest = tmp_path / "c.json"
    contest.write_text(json.dumps({
        "tipo": "contestacao", "frase_id": "EX-01", "motivo": "discordo_classificacao",
        "comentario": "A leitura me parece excessiva.", "consentimento": "sim",
    }), encoding="utf-8")
    analytics.importar(conn, contest)
    dest = tmp_path / "rel"
    saidas = analytics.gerar_relatorios(dest)
    resumo = json.loads(saidas["json"].read_text(encoding="utf-8"))
    assert resumo["submissoes"] == 2
    assert resumo["avaliacoes"] == 5
    assert "não representa a população" in resumo["aviso"].lower() or "Não representa" in resumo["aviso"]
    atencao = json.loads(saidas["atencao"].read_text(encoding="utf-8"))
    ids = {i["frase_id"] for i in atencao}
    assert "EX-01" in ids
    md = saidas["markdown"].read_text(encoding="utf-8")
    assert "amostra voluntária" in md.lower() or "Amostra voluntária" in md
    assert dest.joinpath("painel.html").exists()
    assert "Não publicar" in dest.joinpath("painel.html").read_text(encoding="utf-8") or "Não publicar" in saidas["html"].read_text(encoding="utf-8")


def test_retencao_apaga_texto_antigo_e_mantem_estrutura(conn, tmp_path):
    arq = tmp_path / "participacoes" / "submissoes.jsonl"
    arq.parent.mkdir(parents=True)
    rec = {
        "tipo": "sugestao_frase", "frase": "texto privado de teste aqui", "avaliacao": "opiniao",
        "consentimento": "sim", "recebido_em": "2020-01-01T00:00:00+00:00", "importado_em": "2020-01-01T00:00:00+00:00",
    }
    arq.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    r = analytics.aplicar_retencao(30, tmp_path / "rel")
    assert r["expurgadas"] == 1
    salvo = json.loads(arq.read_text(encoding="utf-8").splitlines()[0])
    assert salvo["frase"] == ""
    assert salvo["_texto_expurgado"] is True


def test_site_js_nao_tem_identificadores_proibidos():
    from eh_so_opiniao import paths
    js = "\n".join(p.read_text(encoding="utf-8") for p in (paths.SITE / "js").rglob("*.js"))
    for termo in ("localStorage", "sessionStorage", "indexedDB", "document.cookie", "geolocation", "fingerprint"):
        assert termo not in js
    assert "avaliacoes_voluntarias" in js
    assert "contribuicoes_abertas" in js
    assert "_gotcha" in js and "guardaInteracao" in js
    assert "formspree.io" not in js
    assert "analytics" not in js.lower()
    assert "challenges.cloudflare.com/turnstile/v0/api.js" in js
    assert "provedor" in js


def test_alias_cloudflare_na_importacao(conn, tmp_path):
    from eh_so_opiniao import participacao
    assert participacao._avaliacao("nao_vejo_problema") == "opiniao"
    assert participacao._avaliacao("possivel_discriminacao") == "discriminacao"
    assert participacao._avaliacao("preciso_contexto") == "contexto"
    dump = {
        "submissions": [
            {"id": "550e8400-e29b-41d4-a716-446655440000", "tipo": "avaliacoes", "schema_version": "3",
             "created_at": "2026-10-30T12:00:00Z", "aviso_versao": "participacao-2", "consentimento": 1},
            {"id": "550e8400-e29b-41d4-a716-446655440001", "tipo": "sugestao_frase", "schema_version": "3",
             "created_at": "2026-10-30T12:01:00Z", "aviso_versao": "participacao-2", "consentimento": 1},
            {"id": "550e8400-e29b-41d4-a716-446655440002", "tipo": "contestacao", "schema_version": "3",
             "created_at": "2026-10-30T12:02:00Z", "aviso_versao": "participacao-2", "consentimento": 1},
        ],
        "evaluations": [
            {"submission_id": "550e8400-e29b-41d4-a716-446655440000", "frase_id": "EX-154", "tema_id": "pcd",
             "modo": "descobrir", "avaliacao": "nao_vejo_problema", "conteudo_versao": "abc123",
             "contexto_exibido": 1, "analise_revelada": 0},
        ],
        "suggestions": [
            {"submission_id": "550e8400-e29b-41d4-a716-446655440001", "texto": "Frase nova de teste.",
             "interpretacao": "preciso_contexto", "contexto": ""},
        ],
        "contestations": [
            {"submission_id": "550e8400-e29b-41d4-a716-446655440002", "frase_id": "EX-154",
             "conteudo_versao": "abc123", "motivo": "erro_texto", "comentario": "typo na frase"},
        ],
    }
    arq = tmp_path / "d1.json"
    arq.write_text(json.dumps(dump), encoding="utf-8")
    r = analytics.importar(conn, arq)["resumo"]
    assert r["votos"] == 1
    assert r["frases_novas"] == 1
    assert r["contestacoes"] == 1
    voto = conn.execute("SELECT avaliacao FROM votos").fetchone()
    assert voto["avaliacao"] == "opiniao"
