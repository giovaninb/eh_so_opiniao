"""Participação de visitantes: mascaramento, importação, revisão obrigatória e agregados públicos."""

from __future__ import annotations

import importlib
import json
import re

import pytest

from eh_so_opiniao import anonimizacao, participacao, paths, publicacao
from eh_so_opiniao.review import store

CABECALHO = "tipo,frase,avaliacao,frase_id,consentimento,site\n"


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(importlib.import_module("eh_so_opiniao.analytics.importar"), "dados_locais", lambda: tmp_path)
    c = store.abrir(tmp_path / "rev.sqlite3")
    yield c
    c.close()


def _csv(tmp_path, linhas, nome="envios.csv"):
    arq = tmp_path / nome
    arq.write_text(CABECALHO + "\n".join(linhas) + "\n", encoding="utf-8")
    return arq


# ------------------------------------------------------------------ mascaramento
def test_mascarar_troca_dados_identificaveis_por_marcadores():
    texto, tipos = anonimizacao.mascarar("Fala @fulano_99 veja https://x.com/p/1 ou mande para ana@mail.com, tel (54) 99999-1234, cpf 123.456.789-09")
    for marcador in ("[usuário]", "[link]", "[e-mail]", "[telefone]", "[documento]"):
        assert marcador in texto
    assert "fulano" not in texto and "999" not in texto and "mail.com" not in texto and "123.456" not in texto
    assert {"usuário", "link", "e-mail", "telefone", "documento"} <= set(tipos)


def test_mascarar_nao_mexe_em_texto_limpo_e_identificaveis_ignora_marcadores():
    limpo = "Quem pensa assim não deveria morar aqui."
    assert anonimizacao.mascarar(limpo) == (limpo, [])
    assert anonimizacao.identificaveis("Veja [link] e [usuário] e [telefone]") == []
    assert anonimizacao.identificaveis("escreve pra @alguem") == ["usuário"]


def test_alertas_apontam_possiveis_nomes_proprios_sem_mascarar():
    assert "Maria Souza" in anonimizacao.alertas("Todo mundo sabe que a Maria Souza não presta")
    assert anonimizacao.alertas("Essa gente não presta.") == []


# ------------------------------------------------------------------ importação
def test_frase_importada_entra_pendente_mascarada_e_nao_publicavel(conn, tmp_path):
    arq = _csv(tmp_path, ['frase,"Quem é de fora, fala com @joao_x e vai embora daqui",discriminacao,,sim,'])
    r = participacao.importar(conn, arq)
    assert r["resumo"] == {"frases_novas": 1} and r["dados_mascarados"] == {"usuário": 1}
    (item,) = store.listar(conn)
    assert item["estado"] == "Pendente" and item["origem"] == store.ORIGEM_VISITANTE and item["tipo"] == "exclusao"
    assert "joao_x" not in item["texto"] and "[usuário]" in item["texto"]
    assert not store.publicavel(item)
    assert publicacao.exportar_frases(conn)["frases"] == []
    assert not any("joao_x" in str(tuple(l)) for l in conn.execute("SELECT * FROM itens"))


def test_importacao_descarta_sem_consentimento_armadilha_e_tamanho(conn, tmp_path):
    arq = _csv(tmp_path, [
        "frase,Frase boa o bastante para valer,opiniao,,,",
        "frase,Frase boa o bastante para valer,opiniao,,sim,spam",
        "frase,curta,opiniao,,sim,",
        f"frase,{'x' * 281},opiniao,,sim,",
        "frase,Frase boa o bastante para valer,talvez,,sim,",
        "voto,,opiniao,frase-invalida,sim,",
    ])
    r = participacao.importar(conn, arq)["resumo"]
    assert r == {"descartada_sem_consentimento": 1, "descartada_armadilha_preenchida": 1, "descartada_tamanho_invalido": 2,
                 "descartada_avaliacao_invalida": 1, "descartada_frase_id_invalido": 1}
    assert store.listar(conn) == [] and conn.execute("SELECT COUNT(*) FROM votos").fetchone()[0] == 0


def test_reimportar_o_mesmo_arquivo_nao_duplica_e_votos_iguais_contam(conn, tmp_path):
    arq = _csv(tmp_path, ["voto,,opiniao,FR-01,sim,", "voto,,opiniao,FR-01,sim,", "frase,Uma frase qualquer de teste aqui,contexto,,sim,"])
    r1 = participacao.importar(conn, arq)["resumo"]
    r2 = participacao.importar(conn, arq)["resumo"]
    assert r1 == {"votos": 2, "frases_novas": 1} and r2 == {"ja_importadas": 3}
    assert conn.execute("SELECT COUNT(*) FROM votos").fetchone()[0] == 2


def test_cabecalhos_de_formulario_com_acento_e_rotulos_longos(conn, tmp_path):
    arq = tmp_path / "gforms.csv"
    arq.write_text("Tipo,Frase,Avaliação,Consentimento\nfrase,Quem pensa diferente deveria sair daqui,É discriminação,Sim\n", encoding="utf-8-sig")
    assert participacao.importar(conn, arq)["resumo"] == {"frases_novas": 1}
    assert store.listar(conn)[0]["tipo"] == "exclusao"


# ------------------------------------------------------------------ revisão humana obrigatória
def _pendente(conn, tmp_path, frase="Essa gente de fora só atrapalha, melhor que saiam daqui"):
    participacao.importar(conn, _csv(tmp_path, [f'frase,"{frase}",discriminacao,,sim,']))
    return store.listar(conn)[0]["id"]


def test_nao_aprova_frase_de_visitante_sem_anonimizar(conn, tmp_path):
    fid = _pendente(conn, tmp_path)
    for acao in (lambda: store.aprovar(conn, fid, "Rev"), lambda: store.marcar_ambiguo(conn, fid, "Rev"),
                 lambda: store.corrigir(conn, fid, "Rev", ["exclusao_social_territorial"])):
        with pytest.raises(store.RevisaoInvalida, match="anonimize"):
            acao()
    assert publicacao.exportar_frases(conn)["frases"] == []


def test_anonimizar_exige_revisor_texto_limpo_e_nao_aprova(conn, tmp_path):
    fid = _pendente(conn, tmp_path)
    with pytest.raises(store.RevisaoInvalida):
        store.anonimizar(conn, fid, "  ", "Essa gente atrapalha e deveria sair daqui")
    with pytest.raises(store.RevisaoInvalida, match="identificável"):
        store.anonimizar(conn, fid, "Rev", "Fale com @alguem sobre essa gente que deveria sair")
    with pytest.raises(store.RevisaoInvalida):
        store.anonimizar(conn, fid, "Rev", "curta")
    store.anonimizar(conn, fid, "Rev", "Essa gente atrapalha e deveria sair daqui", tipo="exclusao", rotulos=["exclusao_social_territorial"])
    item = store.listar(conn)[0]
    assert item["estado"] == "Pendente" and item["origem"] == store.ORIGEM_VISITANTE_ANONIMIZADA
    assert publicacao.exportar_frases(conn)["frases"] == []  # anonimizar não aprova
    store.aprovar(conn, fid, "Rev")
    publicadas = publicacao.exportar_frases(conn)["frases"]
    assert [f["id"] for f in publicadas] == [fid] and publicadas[0]["texto"] == "Essa gente atrapalha e deveria sair daqui"
    assert "Rev" not in json.dumps(publicadas)
    assert [h["nota"] for h in store.historico(conn, fid)][0] == "texto anonimizado manualmente"


def test_anonimizar_so_vale_para_frase_de_visitante(conn):
    store.adicionar(conn, {"id": "T-1", "origem": "sintetica_ilustrativa", "tipo": "exclusao", "texto": "Frase sintética de teste número um."})
    with pytest.raises(store.RevisaoInvalida):
        store.anonimizar(conn, "T-1", "Rev", "Outra frase sintética de teste qualquer")


def test_construir_site_aborta_se_frase_publicada_tem_dado_pessoal(conn, tmp_path):
    store.adicionar(conn, {"id": "T-2", "origem": "fornecida_pelo_operador", "tipo": "exclusao",
                           "texto": "Mandem mensagem para @alguem_real agora mesmo, por favor"})
    store.aprovar(conn, "T-2", "Rev")
    with pytest.raises(publicacao.VazamentoDetectado, match="identificável"):
        publicacao.construir_site(conn, destino=tmp_path / "data", verificar_corpora=False)
    assert not (tmp_path / "data" / "frases.json").exists()


# ------------------------------------------------------------------ agregados públicos
def test_resultados_so_de_frase_publicada_e_com_minimo(conn, tmp_path):
    store.adicionar(conn, {"id": "FR-01", "origem": "sintetica_ilustrativa", "tipo": "exclusao", "texto": "Frase sintética de teste número um."})
    store.aprovar(conn, "FR-01", "Rev")
    store.adicionar(conn, {"id": "FR-02", "origem": "sintetica_ilustrativa", "tipo": "exclusao", "texto": "Frase sintética de teste número dois."})
    linhas = [f"voto,,{'opiniao' if i < 4 else 'discriminacao'},FR-01,sim," for i in range(participacao.MINIMO_PARA_EXIBIR)]
    linhas += ["voto,,opiniao,FR-02,sim,"] * 12 + ["voto,,opiniao,FR-03,sim,"] * 12 + ["voto,,contexto,FR-01,sim,"]
    participacao.importar(conn, _csv(tmp_path, linhas))
    pub = publicacao.construir_site(conn, destino=tmp_path / "data", verificar_corpora=False)
    dados = json.loads((tmp_path / "data" / "participacao.json").read_text(encoding="utf-8"))
    assert pub["frases_publicadas"] == 1
    assert set(dados["resultados"]) == {"FR-01"}  # FR-02 não aprovada, FR-03 inexistente
    r = dados["resultados"]["FR-01"]
    assert r["n"] == 11 and r["opiniao"] == 4 and r["discriminacao"] == 6 and r["contexto"] == 1
    assert "não representa" in dados["aviso"]


def test_poucos_votos_nao_aparecem(conn, tmp_path):
    store.adicionar(conn, {"id": "FR-01", "origem": "sintetica_ilustrativa", "tipo": "exclusao", "texto": "Frase sintética de teste número um."})
    store.aprovar(conn, "FR-01", "Rev")
    participacao.importar(conn, _csv(tmp_path, ["voto,,opiniao,FR-01,sim,"] * (participacao.MINIMO_PARA_EXIBIR - 1)))
    assert participacao.resultados_publicos(conn, {"FR-01"})["resultados"] == {}


# ------------------------------------------------------------------ site
def test_site_tem_formulario_com_consentimento_e_armadilha_e_nao_guarda_no_navegador():
    html = (paths.SITE / "index.html").read_text(encoding="utf-8")
    js = "\n".join(p.read_text(encoding="utf-8") for p in sorted((paths.SITE / "js").rglob("*.js")))
    assert 'data-vista="participar"' in html and 'href="#/participar"' in html
    for trecho in ('id="campo-frase"', 'maxlength="400"', 'id="campo-consentimento"', 'id="campo-armadilha"', 'name="avaliacao"',
                   'id="contador-frase"', 'id="erro-frase"', 'id="mensagem-envio"'):
        assert trecho in html, trecho
    assert "anonimizada e aprovada" in html and "Nada é publicado automaticamente" in html
    assert 'credentials: "omit"' in js and 'referrerPolicy: "no-referrer"' in js
    assert "sessionStorage" not in js and "indexedDB" not in js and "document.cookie" not in js and "localStorage" not in js
    assert "Sem coleta de dados de visitantes" not in html  # a afirmação deixou de ser verdadeira
    # o sucesso só é mostrado após confirmação do serviço; sem confirmação possível, o site diz isso
    assert "não permite confirmar o recebimento" in js and "!r.ok" in js


def test_config_do_site_so_ativa_com_endpoint_https_e_campos_completos():
    cfg = json.loads((paths.SITE / "config_participacao.json").read_text(encoding="utf-8"))
    assert {"tipo", "frase", "avaliacao", "frase_id", "consentimento", "armadilha"} <= set(cfg["campos"])
    if cfg["ativo"]:
        assert re.match(r"^https://\S+$", cfg["endpoint"])
    assert cfg["turnstile_sitekey"].startswith("0x4")
    assert "turnstile_secret" not in {k.lower() for k in cfg}
    html = (paths.SITE / "index.html").read_text(encoding="utf-8")
    assert f'data-sitekey="{cfg["turnstile_sitekey"]}"' in html
    if cfg.get("provedor") == "cloudflare":
        assert cfg["endpoint"].startswith("https://eh-so-opiniao-api.") and cfg["endpoint"].endswith("/api/v1/participacoes")
        assert cfg["endpoint"].endswith("workers.dev/api/v1/participacoes")
        assert "formspree.io" not in cfg["endpoint"]
        assert str(cfg.get("_rollback_formspree") or "").startswith("https://formspree.io/")


def test_dados_publicados_nao_trazem_texto_de_visitante_nao_anonimizado():
    pasta = paths.SITE / "data"
    if not (pasta / "frases.json").exists():
        pytest.skip("site ainda não construído")
    frases = json.loads((pasta / "frases.json").read_text(encoding="utf-8"))["frases"]
    assert all(f["origem"] != store.ORIGEM_VISITANTE for f in frases)
    assert all(not anonimizacao.identificaveis(f["texto"]) for f in frases)
