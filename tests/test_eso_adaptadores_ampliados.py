"""Adaptadores do MultiDomainYT-ToxBR e do RacismoBR, leitor de .xlsx e concordância; só fixtures SINTÉTICAS."""

from __future__ import annotations

import csv
import json
import zipfile

import pytest

from eh_so_opiniao import paths
from eh_so_opiniao.adapters import EsquemaInesperado
from eh_so_opiniao.adapters.multidomain_yt import CLASSES_VETOR, MultiDomainYtToxBrAdapter
from eh_so_opiniao.adapters.racismobr import ESPERADO_NO_ARTIGO, RacismoBrAdapter
from eh_so_opiniao.adapters.xlsx_leve import PlanilhaInvalida, ler_xlsx
from eh_so_opiniao.evaluation import concordancia as C

import fixtures_multidomain as F  # noqa: E402  (módulo auxiliar em tests/)

FX = paths.RAIZ / "fixtures"


@pytest.fixture
def mdyt(tmp_path):
    b, m = F.escrever_csvs(tmp_path)
    return b, m, F.escrever_planilhas(tmp_path / "xlsx")


# ----------------------------------------------------------------------- ordem do vetor
def test_ordem_das_classes_e_a_verificada_nos_dados_e_nao_a_do_readme():
    assert CLASSES_VETOR == F.CLASSES
    assert CLASSES_VETOR[0] == "insulto_de_baixo_calao" and CLASSES_VETOR[-1] == "anticapacitismo"
    assert "obsceno" not in " ".join(CLASSES_VETOR)  # o README cita 'obsceno', que não existe nos dados


def test_mdyt_ambos_modos_preservam_vetor_binario_e_votos(mdyt):
    b, m, x = mdyt
    ad = MultiDomainYtToxBrAdapter(b, m, x)
    am = ad.todas()
    assert len(am) == 12 and ad.relatorio["ordem_vetor"] == "confirmada_pelas_planilhas"
    a = am[3]  # racismo 2 votos, insulto 1
    assert a.original_labels["label_binario"] == 1
    assert a.original_labels["classes"]["racismo"] == 1 and a.original_labels["classes"]["insulto_de_baixo_calao"] == 0
    assert a.valor("racismo") is True and a.valor("insulto_hostilidade") is False
    assert a.valor("linguagem_ofensiva") is True
    assert a.annotation_metadata["votos_por_classe"]["racismo"] == 2
    assert a.annotation_metadata["classes_com_dissenso"] == ["insulto_de_baixo_calao", "racismo"]
    assert a.annotation_metadata["unanime_em_todas_as_classes"] is False
    assert a.annotation_metadata["dominio_tematico"] == "indisponivel_na_fonte" and a.annotation_metadata["id_do_video"] == "indisponivel_na_fonte"
    assert all(v["relation"] == "aproximado" for k, v in a.normalized_labels.items())  # nenhuma classe é equivalente
    assert a.source_platform == "youtube"


def test_mdyt_concordancia_e_grupos_vem_das_planilhas(mdyt):
    b, m, x = mdyt
    am = MultiDomainYtToxBrAdapter(b, m, x).todas()
    assert [a.annotation_metadata["grupo_anotadores"] for a in am] == [1] * 6 + [2] * 6
    assert am[1].annotation_metadata["unanime_em_todas_as_classes"] is True  # insulto 3/3
    assert am[0].annotation_metadata["unanime_em_todas_as_classes"] is True  # nenhum voto


def test_mdyt_coluna_invalido_nao_vira_rotulo(mdyt):
    b, m, x = mdyt
    am = MultiDomainYtToxBrAdapter(b, m, x).todas()
    assert "invalido" not in am[8].normalized_labels
    assert am[8].annotation_metadata["votos_invalido"] == 1
    assert am[8].valor("linguagem_ofensiva") is False  # só 1 voto de violência: sem consenso


def test_mdyt_modo_binario_nao_inventa_categorias(mdyt):
    b, m, _ = mdyt
    am = MultiDomainYtToxBrAdapter(b, None, None, modo="binario").todas()
    assert len(am) == 12 and am[3].valor("racismo") is None  # sem vetor, sem categoria
    assert am[3].valor("linguagem_ofensiva") is True
    assert am[3].annotation_metadata["concordancia"] == "indisponivel_sem_planilhas_dos_anotadores"
    assert am[3].annotation_metadata["ordem_vetor"].startswith("nao_verificavel")


def test_mdyt_modo_multilabel_sem_planilhas_usa_ordem_registrada_e_avisa(mdyt):
    b, m, _ = mdyt
    ad = MultiDomainYtToxBrAdapter(None, m, None, modo="multilabel")
    am = ad.todas()
    assert am[6].valor("xenofobia") is True and ad.relatorio["ordem_vetor"].startswith("nao_verificavel")


def test_mdyt_vetor_com_ordem_diferente_da_registrada_e_recusado(tmp_path):
    b, m = F.escrever_csvs(tmp_path, rotacionar_vetor=True)  # vetor segue OUTRA ordem
    x = F.escrever_planilhas(tmp_path / "xlsx")
    with pytest.raises(EsquemaInesperado, match="NÃO confere"):
        MultiDomainYtToxBrAdapter(b, m, x).todas()


def test_mdyt_vetor_com_tamanho_diferente_e_recusado(tmp_path):
    b, m = F.escrever_csvs(tmp_path)
    linhas = list(csv.reader(m.open(encoding="utf-8")))
    with m.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(linhas[0])
        for t, v in linhas[1:]:
            w.writerow([t, json.dumps(json.loads(v) + [0])])  # 10 posições
    with pytest.raises(EsquemaInesperado, match="posições"):
        MultiDomainYtToxBrAdapter(None, m, None, modo="multilabel").todas()


def test_mdyt_texto_vazio_e_vetor_invalido_sao_descartados_e_contados(tmp_path):
    b = tmp_path / "b.csv"
    m = tmp_path / "m.csv"
    b.write_text("text,label\nok,1\n,0\nruim,1\n", encoding="utf-8")
    m.write_text('text,label\nok,"[1, 0, 0, 0, 0, 0, 0, 0, 0]"\n,"[0, 0, 0, 0, 0, 0, 0, 0, 0]"\nruim,nao-e-vetor\n', encoding="utf-8")
    ad = MultiDomainYtToxBrAdapter(b, m, None)
    am = ad.todas()
    assert len(am) == 1 and ad.relatorio["descartadas"] == {"texto_vazio": 1, "vetor_invalido": 1}


def test_mdyt_esquema_inesperado_e_modo_invalido(tmp_path):
    b = tmp_path / "b.csv"
    b.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(EsquemaInesperado):
        MultiDomainYtToxBrAdapter(b, None, None, modo="binario").todas()
    with pytest.raises(ValueError):
        MultiDomainYtToxBrAdapter(b, None, None, modo="inventado")
    with pytest.raises(ValueError):
        MultiDomainYtToxBrAdapter(None, None, None, modo="binario")
    with pytest.raises(ValueError):
        MultiDomainYtToxBrAdapter(b, None, [b], modo="binario")  # planilhas: 6 ou nenhuma


def test_mdyt_planilhas_com_tamanho_diferente_do_csv_sao_recusadas(tmp_path):
    b, m = F.escrever_csvs(tmp_path)
    x = F.escrever_planilhas(tmp_path / "xlsx")
    linhas = m.read_text(encoding="utf-8").splitlines()
    m.write_text("\n".join(linhas[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(EsquemaInesperado, match="mesmo tamanho"):
        MultiDomainYtToxBrAdapter(None, m, x, modo="multilabel").todas()


def test_mdyt_fixtures_do_repositorio_batem_com_o_gerador(tmp_path):
    b, m = F.escrever_csvs(tmp_path)
    for nome, gerado in (("multidomain_yt_toxbr_binary_sintetico.csv", b), ("multidomain_yt_toxbr_multilabel_sintetico.csv", m)):
        assert (FX / nome).read_text(encoding="utf-8") == gerado.read_text(encoding="utf-8")


def test_mdyt_nao_carrega_licenca_inventada(mdyt):
    b, m, x = mdyt
    a = MultiDomainYtToxBrAdapter(b, m, x).todas()[0]
    assert "Não declarada" in a.license and "acadêmicos" in a.license


# ------------------------------------------------------------------------- leitor de xlsx
def test_xlsx_le_texto_numero_e_celula_vazia(tmp_path):
    arq = tmp_path / "a.xlsx"
    F.escrever_xlsx(arq, [["comentario", "x"], ["olá, mundo", 1], ["sem número", None]])
    assert ler_xlsx(arq) == [["comentario", "x"], ["olá, mundo", "1"], ["sem número"]]  # células vazias à direita são descartadas


def test_xlsx_invalido_levanta_erro_claro(tmp_path):
    arq = tmp_path / "ruim.xlsx"
    arq.write_bytes(b"isto nao e um zip")
    with pytest.raises(PlanilhaInvalida):
        ler_xlsx(arq)
    vazio = tmp_path / "vazio.xlsx"
    with zipfile.ZipFile(vazio, "w") as z:
        z.writestr("qualquer.txt", "x")
    with pytest.raises(PlanilhaInvalida):
        ler_xlsx(vazio)


def test_cabecalho_de_planilha_com_quebras_de_linha_e_acentos_e_reconhecido(mdyt):
    # o cabeçalho sintético reproduz o formato real ("insulto de \nbaixo calão", "intolerância\n religiosa")
    assert any("\n" in h for h in F.CABECALHO_XLSX)
    _, _, x = mdyt
    assert len(MultiDomainYtToxBrAdapter(None, mdyt[1], x, modo="multilabel").todas()) == 12


def test_planilha_sem_coluna_obrigatoria_e_recusada(tmp_path, mdyt):
    b, m, x = mdyt
    F.escrever_xlsx(x[0], [["comentario", "racismo"], ["t", 1]])
    with pytest.raises(EsquemaInesperado, match="colunas ausentes"):
        MultiDomainYtToxBrAdapter(None, m, x, modo="multilabel").todas()


# ------------------------------------------------------------------------ concordância
def test_kappa_e_alfa_conhecidos():
    assert C.kappa_fleiss_binario([0, 3, 3, 0]) == pytest.approx(1.0)
    assert C.alfa_krippendorff_binario([0, 3, 3, 0]) == pytest.approx(1.0)
    assert C.kappa_fleiss_binario([0, 0, 0]) is None  # sem variação: indefinido, não 1
    assert C.alfa_krippendorff_binario([0, 0, 0]) is None
    assert C.kappa_fleiss_binario([]) is None
    # acordo igual ao acaso: kappa ~ 0 (2 de 3 anotadores marcam sempre, itens idênticos)
    k = C.kappa_fleiss_binario([1, 2, 1, 2, 1, 2, 1, 2])
    assert -0.5 < k < 0.0


def test_kappa_de_fleiss_valor_calculado_a_mao():
    # 4 itens, 3 anotadores: contagens 3,0,2,1. p1=6/12=0,5 -> Pe=0,5.
    # Pi: 3 -> (6+0)/6=1 ; 0 -> 1 ; 2 -> (2+0)/6=1/3 ; 1 -> 1/3 ; Po=(1+1+1/3+1/3)/4=2/3 ; kappa=(2/3-1/2)/(1/2)=1/3
    assert C.kappa_fleiss_binario([3, 0, 2, 1]) == pytest.approx(1 / 3)


def test_concordancia_calcular_sobre_planilhas_sinteticas(mdyt):
    _, _, x = mdyt
    r = C.calcular(x)
    g1 = r["por_grupo"]["grupo_1"]
    assert g1["comentarios"] == 6
    ins = g1["classes"]["insulto_de_baixo_calao"]
    assert ins["comentarios_com_algum_voto"] == 4 and ins["positivos_por_maioria"] == 2  # linhas 1 (3 votos) e 4 (2 votos)
    assert "leitura" in r and set(r["por_grupo"]) == {"grupo_1", "grupo_2"}


# ------------------------------------------------------------------------------ RacismoBR
def test_racismobr_contrato_com_fixture_sintetica():
    ad = RacismoBrAdapter(FX / "racismobr_sintetico.csv")
    am = ad.todas()
    assert len(am) == ad.relatorio["emitidas"] > 0
    assert all(a.provenance["origem"] == "fixture_sintetica" or a.license for a in am)
    a = am[0]
    assert a.original_labels == {"racist": 1} and a.valor("racismo") is True
    assert a.normalized_labels["racismo"]["relation"] == "aproximado"
    assert a.annotation_metadata["contrato_verificado_contra_arquivo_real"] is False
    assert a.context["subconjunto"] in ("experimental_balanceado", "reservatorio", "indisponivel")
    assert "SUPOSTO" in ad.relatorio["contrato"]


def test_racismobr_separa_corpus_original_do_subconjunto_balanceado():
    ad = RacismoBrAdapter(FX / "racismobr_sintetico.csv")
    am = ad.todas()
    sub = [a for a in am if a.context["subconjunto"] == "experimental_balanceado"]
    assert 0 < len(sub) < len(am)  # o subconjunto é parte do corpus, nunca o corpus inteiro
    r = ad.relatorio
    assert r["subconjunto_experimental"]["racista"] + r["subconjunto_experimental"]["nao_racista"] == len(sub)
    assert r["racista"] + r["nao_racista"] == len(am)


def test_racismobr_comparacao_com_o_artigo_nao_corrige_divergencia():
    ad = RacismoBrAdapter(FX / "racismobr_sintetico.csv")
    ad.todas()
    cmp = ad.comparar_com_o_artigo()
    assert set(cmp) == set(ESPERADO_NO_ARTIGO)
    assert cmp["subconjunto_experimental"]["declarado"] == 858 and cmp["corpus_original_derivado"]["declarado"] == 1054
    assert not any(v["confere"] for v in cmp.values())  # fixture sintética não é o corpus real


def test_racismobr_rotulo_inesperado_e_recusado(tmp_path):
    arq = tmp_path / "r.csv"
    arq.write_text("text,label\nok,1\nruim,talvez\n", encoding="utf-8")
    with pytest.raises(EsquemaInesperado, match="rótulo inesperado"):
        RacismoBrAdapter(arq).todas()


def test_racismobr_colunas_ausentes_e_mapa_de_colunas(tmp_path):
    arq = tmp_path / "r.csv"
    arq.write_text("tweet,racista\num post,1\noutro post,0\n", encoding="utf-8")
    with pytest.raises(EsquemaInesperado, match="colunas ausentes"):
        RacismoBrAdapter(arq).todas()
    am = RacismoBrAdapter(arq, mapa_colunas={"text": "tweet", "label": "racista"}).todas()
    assert [a.valor("racismo") for a in am] == [True, False]


def test_racismobr_valor_inesperado_de_origem_e_recusado(tmp_path):
    arq = tmp_path / "r.csv"
    arq.write_text("text,label,origin\nok,1,fonte_desconhecida\n", encoding="utf-8")
    with pytest.raises(EsquemaInesperado, match="valor inesperado"):
        RacismoBrAdapter(arq).todas()


def test_racismobr_mapa_de_rotulos_invalido(tmp_path):
    arq = tmp_path / "r.csv"
    arq.write_text("text,label\nx,1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        RacismoBrAdapter(arq, mapa_rotulos={"racista": 2})
