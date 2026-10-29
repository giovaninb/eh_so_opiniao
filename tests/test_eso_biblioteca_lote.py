"""Biblioteca editorial (≥60 casos fictícios), revisão em lote, campos editoriais publicados e migração do banco."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from collections import Counter

import pytest

from eh_so_opiniao import casos, publicacao
from eh_so_opiniao.review import lote, store

# nomes que revelariam lugares ou eventos reais (a anonimização é uma regra do projeto)
PROIBIDOS = re.compile(r"bento gon[cç]alves|festa da uva|\bRS\b|rio grande do sul|\bPT\b|\bPL\b|bolsonaro|\blula\b|\bSTF\b", re.I)


@pytest.fixture
def conn(tmp_path):
    c = store.abrir(tmp_path / "rev.sqlite3")
    yield c
    c.close()


def _item(i: str, **extra):
    base = {"id": i, "origem": "sintetica_ilustrativa", "tipo": "exclusao", "texto": f"Frase fictícia de teste número {i}.",
            "mecanismo": "Mecanismo de teste.", "rotulos_propostos": ["exclusao_social_territorial"], "ia_rotulos": [], "ia_metodo": "A_regras"}
    return {**base, **extra}


# ------------------------------------------------------------------ biblioteca editorial
def test_biblioteca_tem_pelo_menos_60_casos_todos_ficticios_e_com_ids_unicos():
    frases = casos.carregar_todos()["frases"]
    assert len(frases) >= 60
    assert len({f["id"] for f in frases}) == len(frases)
    assert {f["origem"] for f in frases} == {"sintetica_ilustrativa"}


def test_biblioteca_tem_proporcao_relevante_de_casos_sem_discriminacao_e_ambiguos():
    por_tipo = Counter(f["tipo"] for f in casos.carregar_todos()["frases"])
    total = sum(por_tipo.values())
    assert por_tipo["nao_discriminatoria"] >= 15 and por_tipo["ambigua"] >= 7
    assert (por_tipo["nao_discriminatoria"] + por_tipo["ambigua"]) / total >= 0.25


def test_biblioteca_cobre_varios_temas_e_todos_existem():
    ids_tema = {t["id"] for t in casos.temas()}
    usados = {f["tema"] for f in casos.carregar_todos()["frases"] if f.get("tema")}
    assert usados <= ids_tema and len(usados) >= 10


def test_biblioteca_nao_cita_lugares_eventos_ou_pessoas_reais():
    for f in casos.carregar_todos()["frases"]:
        texto = " ".join(str(f.get(c, "")) for c in ("texto", "contexto", "mecanismo", "muda_se")) + " ".join(f.get("razoes", []))
        assert not PROIBIDOS.search(texto), f["id"]


def test_casos_novos_trazem_contexto_razoes_e_o_que_mudaria_a_leitura():
    novos = [f for f in casos.carregar_todos()["frases"] if f["id"].startswith("EX-")]
    assert len(novos) >= 60
    for f in novos:
        assert f.get("contexto") and f.get("muda_se") and f.get("razoes"), f["id"]


def test_casos_espelho_apontam_um_para_o_outro():
    por_id = {f["id"]: f for f in casos.carregar_todos()["frases"]}
    for f in por_id.values():
        if f.get("par_espelho"):
            assert por_id[f["par_espelho"]]["par_espelho"] == f["id"], f["id"]


def test_enfileirar_coloca_tudo_como_pendente_e_nada_e_publicado(conn):
    r = casos.enfileirar(conn)
    assert r["novos"] == r["total"] >= 60
    assert {l["estado"] for l in store.listar(conn)} == {"Pendente"}
    assert publicacao.exportar_frases(conn)["frases"] == []
    assert casos.enfileirar(conn)["novos"] == 0  # idempotente


def test_arquivo_de_casos_rejeita_id_duplicado_entre_arquivos(tmp_path):
    a = tmp_path / "a.yaml"
    a.write_text('versao: "1"\nfrases:\n  - {id: X-1, tipo: exclusao, texto: "t", origem: sintetica_ilustrativa, rotulos_editoriais: []}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicado"):
        casos.carregar_todos((a, a))


def test_caso_de_arquivo_nao_pode_ter_origem_diferente_de_ficticia(tmp_path):
    a = tmp_path / "a.yaml"
    a.write_text('versao: "1"\nfrases:\n  - {id: X-1, tipo: exclusao, texto: "t", origem: enviada_por_visitante, rotulos_editoriais: []}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="sintetica_ilustrativa"):
        casos.carregar(a)


# ------------------------------------------------------------------ publicação com campos editoriais
def test_publicacao_exporta_tema_natureza_contexto_razoes_e_muda_se_so_apos_aprovacao(conn):
    store.adicionar(conn, _item("E-1", editorial={"tema": "racismo", "contexto": "Cena imaginada.", "razoes": ["a", "b"], "muda_se": "Se fosse X."}))
    assert publicacao.exportar_frases(conn)["frases"] == []
    store.aprovar(conn, "E-1", "Rev")
    f = publicacao.exportar_frases(conn)["frases"][0]
    assert (f["tema"], f["natureza"], f["contexto"], f["razoes"], f["muda_se"]) == ("racismo", "ficticio", "Cena imaginada.", ["a", "b"], "Se fosse X.")
    assert f["revisao"] == {"estado": "Aprovado", "por_humano": True}


def test_publicacao_nao_expoe_revisor_nem_notas(conn):
    store.adicionar(conn, _item("E-1"))
    store.aprovar(conn, "E-1", "Nome Do Revisor", nota="justificativa interna")
    bruto = json.dumps(publicacao.exportar_frases(conn), ensure_ascii=False)
    assert "Nome Do Revisor" not in bruto and "justificativa interna" not in bruto


def test_item_pendente_rejeitado_e_enviado_por_visitante_nunca_sao_exportados(conn):
    store.adicionar(conn, _item("P-1"))
    store.adicionar(conn, _item("R-1"))
    store.rejeitar(conn, "R-1", "Rev", "não serve")
    store.adicionar(conn, _item("V-1", origem=store.ORIGEM_VISITANTE))
    assert publicacao.exportar_frases(conn)["frases"] == []


# ------------------------------------------------------------------ migração do banco
def test_banco_antigo_sem_coluna_editorial_e_migrado_sem_perder_dados(tmp_path):
    caminho = tmp_path / "antigo.sqlite3"
    antigo = sqlite3.connect(caminho)
    antigo.executescript(
        """CREATE TABLE itens (id TEXT PRIMARY KEY, origem TEXT NOT NULL, tipo TEXT, texto TEXT NOT NULL, mecanismo TEXT, par_espelho TEXT,
           pode_publicar_ambigua INTEGER NOT NULL DEFAULT 0, ia_rotulos TEXT NOT NULL DEFAULT '[]', ia_metodo TEXT, ia_versao TEXT,
           rotulos_propostos TEXT NOT NULL DEFAULT '[]', rotulos_humanos TEXT, estado TEXT NOT NULL DEFAULT 'Pendente', nota TEXT,
           revisor TEXT, taxonomia_versao TEXT, criado_em TEXT NOT NULL, atualizado_em TEXT NOT NULL);
           INSERT INTO itens (id, origem, tipo, texto, estado, criado_em, atualizado_em)
           VALUES ('OLD-1', 'sintetica_ilustrativa', 'exclusao', 'Texto antigo.', 'Aprovado', 'x', 'x');"""
    )
    antigo.commit()
    antigo.close()
    c = store.abrir(caminho)
    try:
        assert "editorial" in {col["name"] for col in c.execute("PRAGMA table_info(itens)")}
        assert c.execute("SELECT texto, estado, editorial FROM itens").fetchone()[:] == ("Texto antigo.", "Aprovado", None)
        store.abrir(caminho).close()  # abrir de novo não repete a migração
    finally:
        c.close()


# ------------------------------------------------------------------ revisão em lote
def _preencher(caminho, **decisoes):
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))
    for l in linhas:
        l.update(decisoes.get(l["id"], {}))
    with caminho.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=lote.COLUNAS)
        w.writeheader()
        w.writerows(linhas)


@pytest.fixture
def folha(conn, tmp_path):
    for i in ("A", "B", "C"):
        store.adicionar(conn, _item(i, editorial={"tema": "racismo", "contexto": "ctx", "razoes": ["r1", "r2"], "muda_se": "m"}))
    caminho = tmp_path / "folha.csv"
    assert lote.exportar_folha(conn, caminho) == 3
    return caminho


def test_folha_exportada_traz_texto_contexto_razoes_e_colunas_de_decisao_vazias(folha):
    with folha.open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))
    assert list(linhas[0]) == lote.COLUNAS
    assert linhas[0]["contexto"] == "ctx" and linhas[0]["razoes"] == "r1 | r2" and linhas[0]["decisao"] == ""


def test_lote_exige_revisor_nomeado(conn, folha):
    _preencher(folha, A={"decisao": "aprovar"})
    with pytest.raises(store.RevisaoInvalida):
        lote.aplicar_folha(conn, folha, "  ")
    assert {l["estado"] for l in store.listar(conn)} == {"Pendente"}


def test_lote_aprova_com_revisor_e_historico_e_deixa_linhas_vazias_pendentes(conn, folha):
    _preencher(folha, A={"decisao": "aprovar", "nota": "ok"}, B={"decisao": "ambiguo", "nota": "depende do contexto"})
    r = lote.aplicar_folha(conn, folha, "Revisor X")
    assert r["aplicadas"] == 2 and r["erros"] == []
    estados = {l["id"]: l["estado"] for l in store.listar(conn)}
    assert estados == {"A": "Aprovado", "B": "Ambíguo", "C": "Pendente"}
    hist = store.historico(conn, "B")[-1]
    assert (hist["revisor"], hist["nota"], hist["para_estado"]) == ("Revisor X", "depende do contexto", "Ambíguo")


def test_lote_e_tudo_ou_nada_um_erro_impede_todas_as_decisoes(conn, folha):
    _preencher(folha, A={"decisao": "aprovar"}, B={"decisao": "rejeitar"})  # rejeitar sem nota é inválido
    r = lote.aplicar_folha(conn, folha, "Revisor X")
    assert r["aplicadas"] == 0 and any("justificativa" in e for e in r["erros"])
    assert {l["estado"] for l in store.listar(conn)} == {"Pendente"}


def test_lote_simulado_nao_altera_nada(conn, folha):
    _preencher(folha, A={"decisao": "aprovar"})
    r = lote.aplicar_folha(conn, folha, "Revisor X", simular=True)
    assert r["aplicadas"] == 0 and r["previstas"] == {"aprovar": 1}
    assert {l["estado"] for l in store.listar(conn)} == {"Pendente"}


@pytest.mark.parametrize("decisao,esperado", [
    ({"decisao": "talvez"}, "decisão inválida"),
    ({"decisao": "corrigir", "nota": "x"}, "rotulos_finais"),
    ({"decisao": "corrigir", "nota": "x", "rotulos_finais": "rotulo_que_nao_existe"}, "fora da taxonomia"),
])
def test_lote_valida_decisoes(conn, folha, decisao, esperado):
    _preencher(folha, A=decisao)
    r = lote.aplicar_folha(conn, folha, "Revisor X")
    assert r["aplicadas"] == 0 and any(esperado in e for e in r["erros"])


def test_lote_nao_decide_de_novo_sem_reabrir_e_nao_repete_ids(conn, folha):
    store.aprovar(conn, "A", "Outro revisor")
    _preencher(folha, A={"decisao": "rejeitar", "nota": "mudei de ideia"})
    assert any("já está Aprovado" in e for e in lote.aplicar_folha(conn, folha, "R")["erros"])
    assert lote.aplicar_folha(conn, folha, "R", reabrir=True)["aplicadas"] == 1
    assert [h["revisor"] for h in store.historico(conn, "A")][-2:] == ["Outro revisor", "R"]  # histórico preservado


def test_lote_nunca_aprova_frase_de_visitante_nao_anonimizada(conn, tmp_path):
    store.adicionar(conn, _item("V-1", origem=store.ORIGEM_VISITANTE))
    caminho = tmp_path / "f.csv"
    lote.exportar_folha(conn, caminho)
    _preencher(caminho, **{"V-1": {"decisao": "aprovar"}})
    r = lote.aplicar_folha(conn, caminho, "R")
    assert r["aplicadas"] == 0 and any("anonimizar" in e for e in r["erros"])
    assert store.listar(conn)[0]["estado"] == "Pendente"


def test_revisao_interativa_registra_revisor_e_permite_sair(conn):
    store.adicionar(conn, _item("A"))
    store.adicionar(conn, _item("B"))
    respostas = iter(["a", "", "s"])  # aprova A (sem nota), depois sai
    saidas: list[str] = []
    lote.interativa(conn, "Revisor X", entrada=lambda _: next(respostas), saida=saidas.append)
    estados = {l["id"]: l["estado"] for l in store.listar(conn)}
    assert estados["A"] == "Aprovado" and estados["B"] == "Pendente"


# ------------------------------------------------------------------ biblioteca ampliada e revisão compacta
def test_biblioteca_ampliada_cobre_os_temas_pedidos_com_contrapontos():
    frases = casos.carregar_todos()["frases"]
    assert len(frases) >= 160
    por_rotulo = Counter(r for f in frases for r in f["rotulos_editoriais"])
    for rotulo, minimo in (("racismo", 12), ("lgbtfobia", 12), ("intolerancia_religiosa", 8), ("capacitismo", 8), ("misoginia", 10), ("xenofobia", 8)):
        assert por_rotulo[rotulo] >= minimo, rotulo
    por_tipo = Counter(f["tipo"] for f in frases)
    assert (por_tipo["nao_discriminatoria"] + por_tipo["ambigua"]) / len(frases) >= 0.3  # o outro lado da linha continua representado
    # cada um dos temas pedidos tem também um exemplo sem discriminação ou ambíguo (pelas razões editoriais, não pelo tema)
    textos = " ".join(f["texto"].lower() for f in frases if f["tipo"] != "exclusao")
    for palavra in ("racismo", "gay", "religios", "cadeirante", "autista"):
        assert palavra in textos, palavra


def test_biblioteca_ampliada_nao_traz_texto_de_corpus_cientifico():
    ampliada = casos.carregar((casos.paths.CASOS / "biblioteca_ampliada.yaml"))["frases"]
    assert ampliada and {f["origem"] for f in ampliada} == {"sintetica_ilustrativa"}
    for f in ampliada:
        assert f.get("contexto") and f.get("muda_se") and len(f.get("razoes", [])) >= 2, f["id"]


def test_folha_compacta_so_tem_o_essencial_e_vem_ordenada_por_tema(conn, tmp_path):
    store.adicionar(conn, _item("B", editorial={"tema": "racismo", "contexto": "ctx", "razoes": ["a"], "muda_se": "m"}))
    store.adicionar(conn, _item("A", editorial={"tema": "capacitismo", "contexto": "ctx", "razoes": ["a"], "muda_se": "m"}))
    caminho = tmp_path / "c.csv"
    assert lote.exportar_folha(conn, caminho, compacta=True) == 2
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f))
    assert list(linhas[0]) == lote.COLUNAS_COMPACTAS and "contexto" not in linhas[0]
    assert [l["id"] for l in linhas] == ["A", "B"]  # capacitismo antes de racismo


def test_sem_a_flag_linha_sem_decisao_continua_pendente(conn, folha):
    _preencher(folha, B={"decisao": "rejeitar", "nota": "não serve"})
    r = lote.aplicar_folha(conn, folha, "Revisor X")
    assert r["aplicadas"] == 1
    assert {l["id"]: l["estado"] for l in store.listar(conn)} == {"A": "Pendente", "B": "Rejeitado", "C": "Pendente"}


def test_aprovar_restantes_aprova_o_que_sobrou_com_nota_de_lote(conn, folha):
    _preencher(folha, B={"decisao": "rejeitar", "nota": "não serve"})
    r = lote.aplicar_folha(conn, folha, "Revisor X", aprovar_restantes=True)
    assert r["erros"] == [] and r["aprovadas_em_lote"] == 2 and r["aplicadas"] == 3
    assert {l["id"]: l["estado"] for l in store.listar(conn)} == {"A": "Aprovado", "B": "Rejeitado", "C": "Aprovado"}
    hist = store.historico(conn, "A")[-1]
    assert hist["revisor"] == "Revisor X" and "em lote" in hist["nota"]


def test_aprovar_restantes_simulado_nao_grava_e_nunca_inclui_frase_de_visitante(conn, tmp_path):
    store.adicionar(conn, _item("A"))
    store.adicionar(conn, _item("V-1", origem=store.ORIGEM_VISITANTE))
    caminho = tmp_path / "f.csv"
    lote.exportar_folha(conn, caminho, compacta=True)
    r = lote.aplicar_folha(conn, caminho, "R", simular=True, aprovar_restantes=True)
    assert r["aplicadas"] == 0 and r["previstas"] == {"aprovar": 1}
    assert {l["estado"] for l in store.listar(conn)} == {"Pendente"}
    lote.aplicar_folha(conn, caminho, "R", aprovar_restantes=True)
    assert {l["id"]: l["estado"] for l in store.listar(conn)} == {"A": "Aprovado", "V-1": "Pendente"}


def test_aprovar_restantes_continua_exigindo_revisor_nomeado(conn, folha):
    with pytest.raises(store.RevisaoInvalida):
        lote.aplicar_folha(conn, folha, "", aprovar_restantes=True)
    assert {l["estado"] for l in store.listar(conn)} == {"Pendente"}
