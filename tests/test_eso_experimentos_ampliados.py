"""Protocolos AMP-A a AMP-G sobre corpora SINTÉTICOS: contrato dos resultados, travas e ausência de texto bruto."""

from __future__ import annotations

import csv
import json
import random

import pytest

from eh_so_opiniao import cli_extra, paths
from eh_so_opiniao.evaluation import experiments as X
from eh_so_opiniao.evaluation import experiments_ampliados as AMP
from eh_so_opiniao.schema import NormalizedTextSample, escrever_jsonl

NEUTRAS = "casa rua festa trabalho cidade prefeito saude escola transito domingo mercado vizinho obra projeto governo".split()
OFENSIVAS = "idiota nojento lixo canalha inutil".split()
CLASSES_MDYT = AMP.CLASSES_MDYT
ORIGINAL = {"insulto_hostilidade": "insulto_de_baixo_calao", "lgbtfobia": "homofobia", "racismo": "racismo", "misoginia": "misoginia_machismo",
            "xenofobia": "xenofobia", "incitacao_violencia": "violencia_extremismo", "intolerancia_religiosa": "intolerancia_religiosa",
            "hostilidade_politica": "intolerancia_politica", "capacitismo": "anticapacitismo"}


def _rot(valor, relacao="aproximado"):
    return {"value": bool(valor), "relation": relacao, "policy": "sintetico", "source": ["sintetico"]}


def _base(ds, i, texto):
    return NormalizedTextSample(sample_id=f"{ds}:{i}", dataset_id=ds, source_platform="sintetico", text=texto, license="sintetico",
                                provenance={"origem": "fixture_sintetica"})


def _frase(rng, extra=()):
    palavras = [rng.choice(NEUTRAS) for _ in range(7)] + list(extra)
    rng.shuffle(palavras)
    return palavras


def gerar_told(n, semente):
    rng = random.Random(semente)
    saida = []
    for i in range(n):
        classes = {c: rng.random() < 0.12 for c in ("racismo", "xenofobia", "misoginia")}
        ofensivo = any(classes.values()) or rng.random() < 0.15
        extra = [f"sinal{c}" for c, v in classes.items() if v] + (["idiota"] if ofensivo else []) + (["nordestino"] if classes["xenofobia"] and rng.random() < .5 else [])
        a = _base("told_br", i, " ".join(_frase(rng, extra)) + f" t{i}")
        a.normalized_labels["linguagem_ofensiva"] = _rot(ofensivo)
        for c, v in classes.items():
            a.normalized_labels[c] = _rot(v)
        saida.append(a.validar())
    return saida


def gerar_hatebr(n, semente):
    rng = random.Random(semente)
    saida = []
    for i in range(n):
        ofensivo = rng.random() < 0.5
        pal = [rng.choice(NEUTRAS) for _ in range(6)]
        if rng.random() < 0.3:
            pal.insert(rng.randrange(len(pal)), rng.choice(("lula", "bolsonaro", "governo")))
        alvo = rng.choice(OFENSIVAS)
        texto = " ".join(pal) + (f" {alvo}" if ofensivo else "") + f" h{i}"
        a = _base("hatebr", i, texto)
        a.context = {"post_group": f"post{i % 14}"}
        a.normalized_labels["linguagem_ofensiva"] = _rot(ofensivo)
        if ofensivo:
            ini = texto.index(alvo)
            a.toxic_spans = [{"start": ini, "end": ini + len(alvo), "origin": "derivado_de_rationale"}]
            a.annotation_metadata["rationales"] = {"anotador_1": [alvo], "anotador_2": [alvo] if rng.random() < .8 else []}
        saida.append(a.validar())
    return saida


def gerar_mdyt(n, semente):
    rng = random.Random(semente)
    saida = []
    for i in range(n):
        votos = {ORIGINAL[c]: 0 for c in CLASSES_MDYT}
        marcados = []
        for c in CLASSES_MDYT:
            p = 0.25 if c == "insulto_hostilidade" else 0.05 if c != "capacitismo" else 0.01
            if rng.random() < p:
                votos[ORIGINAL[c]] = rng.choice((1, 2, 3, 3))
                if votos[ORIGINAL[c]] >= 2:
                    marcados.append(c)
        extra = [f"sinal{c}" for c in marcados] + (["idiota"] if marcados else [])
        if rng.random() < 0.25:
            extra.append(rng.choice(("lula", "bolsonaro", "governo")))
        a = _base("multidomain_yt_toxbr", i, " ".join(_frase(rng, extra)) + f" y{i}")
        for c in CLASSES_MDYT:
            a.normalized_labels[c] = _rot(c in marcados)
        a.normalized_labels["linguagem_ofensiva"] = _rot(bool(marcados))
        a.annotation_metadata = {"votos_por_classe": votos, "grupo_anotadores": 1 if i % 2 else 2,
                                 "unanime_em_todas_as_classes": all(v in (0, 3) for v in votos.values())}
        saida.append(a.validar())
    return saida


def gerar_racismobr(n, semente):
    rng = random.Random(semente)
    saida = []
    for i in range(n):
        racista = rng.random() < 0.4
        a = _base("racismobr", i, " ".join(_frase(rng, ["sinalracista"] if racista else [])) + f" r{i}")
        a.normalized_labels["racismo"] = _rot(racista)
        saida.append(a.validar())
    return saida


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("ESO_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(paths, "RELATORIOS", tmp_path / "relatorios")
    pasta = tmp_path / "normalizado"
    corpora = {"told_br": gerar_told(1100, 1), "hatebr": gerar_hatebr(900, 2), "multidomain_yt_toxbr": gerar_mdyt(1300, 3)}
    # um texto em comum entre ToLD-Br e MDYT para exercitar a exclusão de sobreposição
    comum = corpora["told_br"][5]
    sobre = NormalizedTextSample(sample_id="multidomain_yt_toxbr:comum", dataset_id="multidomain_yt_toxbr", source_platform="sintetico", text=comum.text,
                                 license="sintetico", provenance={"origem": "fixture_sintetica"})
    sobre.normalized_labels = {k: _rot(False) for k in ("linguagem_ofensiva", *CLASSES_MDYT)}
    sobre.annotation_metadata = {"votos_por_classe": {ORIGINAL[c]: 0 for c in CLASSES_MDYT}, "grupo_anotadores": 1, "unanime_em_todas_as_classes": True}
    corpora["multidomain_yt_toxbr"].append(sobre.validar())
    for ds, am in corpora.items():
        escrever_jsonl(am, pasta / f"{ds}.jsonl")

    def limpar():
        X._bruto.cache_clear()
        X.corpus.cache_clear()
        X.treinar_ofensivo.cache_clear()
        AMP.limpar_caches()

    limpar()
    yield corpora
    limpar()


def _texto_publico(resultado) -> str:
    return json.dumps(resultado, ensure_ascii=False)


def _nenhum_texto_de_corpus(resultado, corpora):
    bruto = _texto_publico(resultado)
    vazados = [a.text for am in corpora.values() for a in am if len(a.text) > 25 and a.text in bruto]
    assert not vazados


# ----------------------------------------------------------------------------- AMP-A
def test_amp_a_racismobr_pendente_de_fonte_nao_inventa_numero(ambiente):
    r = AMP.experimento_amp_a()
    assert r["status"] == "pendente_fonte" and r["resultado"] is None
    assert "fixtures sintéticas" in r["nota"] and "858" in r["protocolo"]["subconjunto_experimental"]


def test_amp_a_roda_o_protocolo_quando_ha_arquivo(ambiente, tmp_path, monkeypatch):
    escrever_jsonl(gerar_racismobr(260, 9), paths.normalizados() / "racismobr.jsonl")
    X._bruto.cache_clear()
    original = AMP._pendente
    monkeypatch.setattr(AMP, "_pendente", lambda ds: None if ds == "racismobr" else original(ds))
    r = AMP.experimento_amp_a()
    assert r["status"] == "executado"
    sub, orig = r["resultado"]["subconjunto_balanceado"], r["resultado"]["corpus_original"]
    assert sub["racistas"] * 2 == sub["n"] and sub["origem"].startswith("reconstruido") and orig["n"] == 260
    assert sub["n"] < orig["n"]  # balanceado é DIFERENTE do original
    for modelo in ("lr", "svm"):
        assert sub[modelo]["dobras"] == 5 and sub[modelo]["f1_racista"]["media"] > 0.8  # sinal sintético óbvio
    assert sub["chute_trivial_sempre_racista"]["precision"] == 0.5


# ----------------------------------------------------------------------------- AMP-B
def test_amp_b_matriz_separada_por_rotulo_e_dataset(ambiente):
    r = AMP.experimento_amp_b(sementes=(42,))
    racismo, ofensiva = r["alvos"]["racismo"], r["alvos"]["linguagem_ofensiva"]
    assert racismo["datasets_indisponiveis"]["racismobr"]["status"] == "pendente_fonte"
    assert set(racismo["datasets_usados"]) == {"told_br", "multidomain_yt_toxbr"}
    assert set(ofensiva["matriz"]) == {f"{a}->{b}" for a in ("told_br", "hatebr", "multidomain_yt_toxbr") for b in ("told_br", "hatebr", "multidomain_yt_toxbr")}
    celula = ofensiva["matriz"]["told_br->hatebr"]
    assert not celula["em_dominio"] and celula["relacao_treino"]["relacao"] == "aproximado" and "f1" in celula
    assert ofensiva["matriz"]["told_br->told_br"]["em_dominio"]
    assert any("fundido" in a for a in r["avisos"])


def test_amp_b_exclui_textos_em_comum_entre_treino_e_avaliacao(ambiente):
    r = AMP.experimento_amp_b(sementes=(42,))
    cel = r["alvos"]["linguagem_ofensiva"]["matriz"]["told_br->multidomain_yt_toxbr"]
    assert cel["excluidos_por_sobreposicao_por_semente"][0] >= 1  # o texto comum foi retirado
    assert r["alvos"]["linguagem_ofensiva"]["matriz"]["told_br->told_br"]["excluidos_por_sobreposicao_por_semente"] == [0]


def test_amp_b_celula_com_poucos_positivos_e_sinalizada(ambiente):
    r = AMP.experimento_amp_b(sementes=(42,))
    pouco = [c for c in r["alvos"]["racismo"]["matriz"].values() if c.get("positivos_por_semente") and max(c["positivos_por_semente"]) < 30]
    assert pouco and all(c["suporte_insuficiente"] and "aviso" in c for c in pouco)


# ----------------------------------------------------------------------------- AMP-C
def test_amp_c_aguarda_anotacao_humana_e_cria_folha_local(ambiente):
    r = AMP.experimento_amp_c(sementes=(42,))
    assert r["status"] == "aguardando_anotacao_humana" and r["resultado"] is None
    folha = paths.pasta_experimentos_locais() / AMP.FOLHA
    assert folha.exists() and str(paths.dados_locais()) in r["folha"]["arquivo_local"]
    with folha.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    assert linhas and all(l["avaliacao_humana"] == "" for l in linhas)  # nenhum rótulo automático
    assert {l["dataset_id"] for l in linhas} <= {"told_br", "multidomain_yt_toxbr"}
    _nenhum_texto_de_corpus(r, ambiente)  # o texto fica só na folha local


def test_amp_c_nao_sobrescreve_anotacoes_e_roda_quando_ha_anotacao_suficiente(ambiente):
    AMP.gerar_folha_explicito_implicito(maximo_por_dataset=200)
    folha = paths.pasta_experimentos_locais() / AMP.FOLHA
    with folha.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    told = [l for l in linhas if l["dataset_id"] == "told_br"]
    assert len(told) >= 40
    for k, l in enumerate(told):
        l["avaliacao_humana"] = "explicito" if k % 2 else "implicito"
    with folha.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    n = AMP.gerar_folha_explicito_implicito(maximo_por_dataset=200)
    assert n["novas"] == 0  # reexecutar não duplica nem apaga
    r = AMP.experimento_amp_c(sementes=(42,))
    assert r["status"] == "executado" and set(r["resultado"]["revocacao_por_estrato"]) == {"explicito", "implicito"}


def test_amp_c_ignora_valores_de_anotacao_invalidos(ambiente):
    AMP.gerar_folha_explicito_implicito()
    folha = paths.pasta_experimentos_locais() / AMP.FOLHA
    with folha.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    for l in linhas:
        l["avaliacao_humana"] = "talvez"
    with folha.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    assert AMP.experimento_amp_c(sementes=(42,))["folha"]["anotadas"] == 0


# ----------------------------------------------------------------------------- AMP-D
def test_amp_d_xenofobia_por_dataset_e_composicao_sem_rotulo_regional(ambiente):
    r = AMP.experimento_amp_d(sementes=(42,))
    assert set(r["matriz_xenofobia"]) == {f"{a}->{b}" for a in ("told_br", "multidomain_yt_toxbr") for b in ("told_br", "multidomain_yt_toxbr")}
    comp = r["composicao_dos_positivos"]["told_br"]
    assert comp["positivos_xenofobia"] == comp["com_marcador_regional"] + comp["com_marcador_nacionalidade"] + comp["com_ambos"] + comp["sem_marcador_da_lista"]
    assert comp["com_marcador_regional"] > 0 and "não rótulo" in comp["leitura"]
    assert r["discriminacao_regional"]["status"] == "sem_rotulo_anotado"
    assert any("Nenhuma outra ferramenta de IA do projeto" in a for a in r["avisos"])


# ----------------------------------------------------------------------------- AMP-E
def test_amp_e_falsos_positivos_politicos_com_ids_so_localmente(ambiente):
    r = AMP.experimento_amp_e(sementes=(42,))
    assert "multidomain_yt_toxbr:hostilidade_politica" in r["resultado_por_modelo_e_corpus"]
    cel = r["resultado_por_modelo_e_corpus"]["hatebr:linguagem_ofensiva"]["multidomain_yt_toxbr"]
    k = cel["contagens_por_semente"][0]
    assert k["n_politico_nao_toxico"] > 0 and 0 <= k["fp_politico"] <= k["n_politico_nao_toxico"] and len(k["ic95_wilson_politico"]) == 2
    assert not cel["em_dominio"]
    assert (paths.pasta_experimentos_locais() / "amp_e_falsos_positivos_ids.json").exists()
    assert "proxy" in r["definicao_de_alvo"]
    _nenhum_texto_de_corpus(r, ambiente)


# ----------------------------------------------------------------------------- AMP-F
def test_amp_f_compara_humano_com_modelo_sem_afirmar_causa(ambiente):
    r = AMP.experimento_amp_f()
    assert r["status"] == "executado"
    h = r["teto_humano_anotador_1_vs_2"]
    assert 0 <= h["f1"] <= 1 and h["kappa_de_cohen_por_token"] is not None
    assert set(r["metodos"]) == {"coeficientes_tfidf", "oclusao_do_modelo_completo", "tudo", "aleatorio_prob_0.3"}
    assert r["metodos"]["aleatorio_prob_0.3"]["contra_uniao_dos_dois_anotadores"]["f1"] < r["metodos"]["coeficientes_tfidf"]["contra_uniao_dos_dois_anotadores"]["f1"]
    assert "ranking_independente_de_limiar" in r
    sv = r["sensibilidade_do_modelo_a_remocao"]
    assert sv["remover_trechos_humanos"]["queda_media_da_pontuacao"]["media"] > sv["remover_aleatorios_mesmo_numero"]["queda_media_da_pontuacao"]["media"]
    assert "não prova" in sv["leitura"] and any("SHAP" in a for a in r["avisos"])
    assert (paths.pasta_experimentos_locais() / "amp_f_casos_explicados.jsonl").exists()
    _nenhum_texto_de_corpus(r, ambiente)


# ----------------------------------------------------------------------------- AMP-G
def test_amp_g_portao_de_validacao_por_classe(ambiente):
    r = AMP.experimento_amp_g(sementes=(42,))
    assert r["status"] == "executado"
    por = r["por_classe_em_dominio"]
    assert set(por) == {"linguagem_ofensiva", *CLASSES_MDYT}
    assert por["insulto_hostilidade"]["validada"] is True  # classe frequente com sinal claro
    for rara in ("capacitismo", "incitacao_violencia"):
        if "f1" in por[rara]:
            assert por[rara]["validada"] is False and por[rara]["motivo_nao_validada"]
    assert set(r["classes_nao_validadas"]).isdisjoint(r["classes_validadas"])
    assert any("não indica capacidade" in a or "NÃO indica" in a for a in r["avisos"])
    assert any("multirrótulo" in a for a in r["avisos"])


def test_amp_g_concordancia_estratos_e_curva(ambiente):
    r = AMP.experimento_amp_g(sementes=(42,))
    cc = r["concordancia_e_desempenho"]
    assert cc["disponivel"]
    assert set(cc["desempenho_binario_por_nivel_de_acordo"]) == {"unanimes_em_todas_as_classes", "com_voto_dividido_em_alguma_classe"}
    assert set(cc["desempenho_binario_por_grupo_de_anotadores"]) == {"grupo_1", "grupo_2"}
    assert "prevalência" in cc["nota_nivel_de_acordo"]
    curva = r["curva_de_aprendizado_por_positivos"]["insulto_hostilidade"]
    assert [p["positivos_no_treino"] for p in curva][-1] == "todos" and len(curva) >= 3
    assert "kappa_por_classe_e_grupo" in cc and set(cc["kappa_por_classe_e_grupo"]) == set(CLASSES_MDYT)
    _nenhum_texto_de_corpus(r, ambiente)


def test_amp_g_sem_dados_do_mdyt_devolve_status_claro(tmp_path, monkeypatch):
    monkeypatch.setenv("ESO_DATA_DIR", str(tmp_path))
    r = AMP.experimento_amp_g()
    assert r["status"] == "ausente_no_cache" and r["resultado"] is None


# ------------------------------------------------------------------ utilitários e execução
def test_wilson_e_spearman():
    assert AMP._wilson(0, 0) is None
    lo, hi = AMP._wilson(8, 78)
    assert 0.05 < lo < 0.103 < hi < 0.19
    assert AMP._spearman([1, 2, 3, 4], [2, 4, 6, 8]) == 1.0 and AMP._spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    assert AMP._spearman([1, 2, 3], [1, 2, 3]) is None  # n pequeno demais


def test_executar_grava_json_por_protocolo(ambiente):
    saida = AMP.executar(["amp_a", "amp_c"])
    assert set(saida) == {"amp_a", "amp_c"}
    for chave in saida:
        assert (paths.RELATORIOS / f"experimento_{chave}.json").exists()
    assert set(AMP.EXPERIMENTOS) == {f"amp_{x}" for x in "abcdefg"}


def test_cli_rejeita_experimento_desconhecido(capsys):
    import argparse

    rc = cli_extra.cmd_experimentos(argparse.Namespace(quais="amp_z", ampliados=False))
    assert rc == 2 and "desconhecido" in capsys.readouterr().err
