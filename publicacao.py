"""Geração dos dados do site estático.

Só sai daqui: (1) frases com decisão humana (Aprovado/Corrigido/Ambíguo permitido) de origens
publicáveis; (2) taxonomia; (3) catálogo e referências (metadados, nunca texto de corpus);
(4) achados agregados dos experimentos (números, nunca exemplos).
A classificação por IA NÃO roda no site: o site só lê JSON já revisado.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import SCHEMA_VERSION, anonimizacao, participacao, paths, registry
from .review import store
from .textnorm import hash_chave

AVISO = ("Conteúdo educativo e experimental. Uma classificação de IA é uma hipótese, não uma prova: "
         "não conclui crime, intenção nem identidade, e só é exibida depois de revisão humana.")


class VazamentoDetectado(RuntimeError):
    pass


def _nomes(rotulos: list[str]) -> list[dict[str, str]]:
    tax = registry.rotulos_taxonomia()
    return [{"id": r, "nome": tax[r]["nome"], "tipo": tax[r]["tipo"]} for r in rotulos if r in tax]


# Tema de exibição para itens antigos, sem metadados editoriais: o primeiro rótulo da lista que bater.
_TEMA_POR_ROTULO = (("racismo", "racismo"), ("misoginia", "misoginia"), ("lgbtfobia", "lgbtfobia"),
                    ("discriminacao_regional", "discriminacao_regional"), ("xenofobia", "xenofobia"),
                    ("estigmatizacao_socioeconomica", "estigmatizacao_socioeconomica"), ("hostilidade_politica", "hostilidade_politica"),
                    ("desumanizacao", "desumanizacao"), ("exclusao_social_territorial", "exclusao_territorial"),
                    ("critica_politica_legitima", "critica_legitima"), ("ironia_humor", "ironia"))
# Natureza do exemplo, derivada da origem (nunca declarada pelo texto): ver docs/CASOS_EDITORIAIS.md.
NATUREZA_POR_ORIGEM = {"sintetica_ilustrativa": "ficticio", "fornecida_pelo_operador": "adaptado", "visitante_anonimizada": "contribuicao"}


def _tema(editorial: dict[str, Any], rotulos: list[str], tipo: str | None) -> str:
    if editorial.get("tema"):
        return editorial["tema"]
    for rotulo, tema in _TEMA_POR_ROTULO:
        if rotulo in rotulos:
            return tema
    return "depende_contexto" if tipo == "ambigua" else "sem_discriminacao"


def exportar_frases(conn, incluir_rascunho: bool = False) -> dict[str, Any]:
    from . import expansao

    itens = []
    for linha in store.listar(conn):
        publicavel = store.publicavel(linha)
        rascunho_ok = incluir_rascunho and linha["origem"] in store.ORIGENS_PUBLICAVEIS and linha["estado"] != "Rejeitado"
        if not publicavel and not rascunho_ok:
            continue
        if linha["estado"] == "Ambíguo":
            finais = ["ambigua"]
        elif linha["rotulos_humanos"] is not None:
            finais = json.loads(linha["rotulos_humanos"])
        else:
            finais = json.loads(linha["rotulos_propostos"])
        ia = json.loads(linha["ia_rotulos"])
        editorial = json.loads(linha["editorial"]) if linha["editorial"] else {}
        itens.append({
            "id": linha["id"], "texto": linha["texto"], "tipo": linha["tipo"],
            "tema": _tema(editorial, finais, linha["tipo"]), "natureza": NATUREZA_POR_ORIGEM.get(linha["origem"], "ficticio"),
            "contexto": editorial.get("contexto"), "razoes": editorial.get("razoes", []), "muda_se": editorial.get("muda_se"),
            "rotulos": _nomes(finais), "mecanismo": linha["mecanismo"], "par_espelho": linha["par_espelho"],
            "ia": {"sinalizou": _nomes(ia), "metodo": linha["ia_metodo"], "concorda_com_revisao": sorted(ia) == sorted(finais)},
            "revisao": {"estado": linha["estado"] if publicavel else "RASCUNHO", "por_humano": publicavel},
            "origem": linha["origem"],
            # dimensões independentes e aviso de conteúdo (só itens da expansão têm; os demais ficam nulos/falsos)
            "subtema": editorial.get("subtema"), "aviso_conteudo": bool(editorial.get("aviso_conteudo")),
            "dimensoes": editorial.get("dimensoes"),
            "grupo": expansao.grupo_de(_tema(editorial, finais, linha["tipo"]), (editorial.get("dimensoes") or {}).get("grupo")),
        })
    usados = {i["tema"] for i in itens}
    grupos_usados = {i["grupo"] for i in itens if i["grupo"]}
    from . import casos

    return {"schema": f"eso-site-{SCHEMA_VERSION}", "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "taxonomia_versao": registry.versao_taxonomia(), "aviso": AVISO,
            "temas": [t for t in casos.temas() if t["id"] in usados],
            "grupos": [g for g in expansao.grupos() if g["id"] in grupos_usados], "frases": itens}


def taxonomia_publica() -> dict[str, Any]:
    return {"versao": registry.versao_taxonomia(), "rotulos": [
        {"id": rid, "nome": r["nome"], "tipo": r["tipo"], "definicao": r["definicao"], "nao_e": r.get("nao_e", ""),
         "observacao": r.get("observacao", "")} for rid, r in registry.rotulos_taxonomia().items()]}


def _uso_publico(i: dict[str, Any]) -> tuple[str, str]:
    """Rótulo e explicação em linguagem simples sobre COMO a base é usada (ou por que não é)."""
    if i["integracao"] == "pendente_fonte":
        return ("Aguardando fonte oficial", "O repositório citado pelos autores não está acessível. Nenhum dado dela foi usado nem inventado.")
    if i["integracao"] == "somente_sobreposicao":
        return ("Só para medir sobreposição", "Serve para checar textos repetidos entre bases. Não é usada para treinar nem para avaliar.")
    if not i["condicoes_licenca"]["declarada"]:
        return ("Em uso local, sob condições de licença", "Sem licença formal publicada: uso só acadêmico, no computador da equipe, sem redistribuição.")
    return ("Em uso nos experimentos", "Licença declarada e respeitada. Os textos não são publicados aqui.")


def catalogo_publico() -> list[dict[str, Any]]:
    saida = []
    for ds_id in registry.listar_datasets():
        i = registry.dataset(ds_id)
        rotulo, explicacao = _uso_publico(i)
        saida.append({"id": ds_id, "nome": i["nome"],
                      "licenca": i["licenca"] if i["condicoes_licenca"]["declarada"] and len(i["licenca"]) < 40 else "não declarada",
                      "plataforma": i["plataforma"], "acesso": i["acesso"], "status": i["status_acesso"], "integracao": i["integracao"],
                      "rotulo_uso": rotulo, "explicacao_uso": explicacao,
                      "registros": i["registros_confirmados"], "referencia": i["referencia"], "url": i["url_origem"],
                      "url_artigo": i.get("url_artigo"), "limitacoes": i["limitacoes_vieses"]})
    return saida


def contexto_publico() -> dict[str, Any]:
    """Dados de contexto por grupo (ex.: violência contra pessoas trans), com dado, fonte, ano, metodologia e limitações."""
    import yaml

    bruto = yaml.safe_load((paths.CATALOGO / "contexto_dados.yaml").read_text(encoding="utf-8"))
    chaves = ("id", "grupo", "titulo", "dado", "fonte", "ano", "metodologia", "limitacoes", "links", "conferencia")
    return {"conferido_em": bruto["conferido_em"], "itens": [{k: i[k] for k in chaves} for i in bruto["itens"]]}


def referencias_publicas() -> dict[str, Any]:
    """Recursos citados além das bases do catálogo (escala teórica, recursos de explicabilidade). Sem texto de corpus."""
    itens = [{"id": r["id"], "tipo": r["tipo"], "titulo": r["titulo"], "citacao": r["citacao"], "url": r["url"],
              "papel": r["papel_no_projeto"], "o_que_nao_e": r["o_que_nao_e"], "direitos": r["licenca_ou_direitos"],
              "eh_dataset_supervisionado": r.get("usar_como_dataset_supervisionado", None)} for r in registry.carregar_referencias()]
    return {"referencias": itens, "aviso": "Referência teórica não é base de dados e não gera classificador."}


def _ler(nome: str, pasta: Path) -> dict[str, Any] | None:
    caminho = pasta / f"experimento_{nome}.json"
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else None


def achados_dos_relatorios(pasta: Path | None = None) -> list[dict[str, Any]]:
    """Achados agregados (números dos relatórios reais). Sem texto de corpora."""
    pasta = pasta or paths.RELATORIOS
    achados: list[dict[str, Any]] = []
    b, c, d, e, a = (_ler(x, pasta) for x in "bcdea")
    pct = lambda v: f"{round(v * 100)}%"  # noqa: E731
    if b:
        t = b["teste_hatebr"]
        lr, lex = t["B_lr_val_f1"], t["A_lexico"]
        achados.append({"id": "fp_fn", "titulo": "Mesmo o melhor modelo simples erra",
                        "texto": f"No teste do HateBR, o modelo TF-IDF acerta a maior parte, mas deixa passar cerca de {pct(1 - lr['recall']['media'])} dos comentários ofensivos "
                                 f"e marca como ofensivos cerca de {pct(1 - lr['precision']['media'])} dos que sinalizou sem serem. "
                                 f"Já a lista de palavras ofensivas quase não erra ao apontar (precisão {pct(lex['precision']['media'])}), mas só encontra {pct(lex['recall']['media'])} dos casos.",
                        "experimento": "B"})
        tr = b["transferencia_para_told"]
        achados.append({"id": "fora_do_dominio", "titulo": "Fora do domínio, o resultado muda",
                        "texto": f"Treinado em comentários sobre políticos (HateBR) e testado no ToLD-Br, o modelo obteve macro-F1 {tr['B_lr_val_f1']['macro_f1']['media']:.2f} "
                                 f"(média das duas classes), contra {tr['trivial']['macro_f1']['media']:.2f} de simplesmente marcar tudo como ofensivo e {tr['A_lexico']['macro_f1']['media']:.2f} da lista de palavras. "
                                 f"No ToLD-Br, {pct(tr['prevalencia_told'])} dos textos contam como ofensivos pelo critério de votos usado aqui, que é só aproximado ao do HateBR. "
                                 "Comparar com o chute e com outro domínio é essencial para não se enganar.",
                        "experimento": "B"})
    if a:
        raras = [k for k, v in a["por_classe"].items() if v["suporte_insuficiente_dominio"]]
        achados.append({"id": "classes_raras", "titulo": "Classes raras quase não têm exemplos",
                        "texto": "Para as classes " + ", ".join(registry.rotulos_taxonomia()[k]["nome"].lower() for k in raras) +
                                 " há poucos exemplos positivos no teste. As métricas dessas classes oscilam muito e não permitem concluir que o modelo funciona.",
                        "experimento": "A"})
    if c:
        piores = [g for g in c["efeito_de_combinar_em_dominio"] if g["delta"] < 0]
        if piores:
            achados.append({"id": "combinar_dados", "titulo": "Juntar bases diferentes nem sempre ajuda",
                            "texto": f"Em {len(piores)} de {len(c['efeito_de_combinar_em_dominio'])} comparações, treinar com mais de uma base (cujas definições de 'ofensivo' são só aproximadas) "
                                     "piorou o F1 no teste da própria base. Misturar rótulos parecidos não é o mesmo que ter o mesmo rótulo.",
                            "experimento": "C"})
    if d:
        cf = d["contrafactual"]["hatebr"]["ofensivos"]["esquerda_para_direita"]
        achados.append({"id": "neutralidade", "titulo": "O modelo pode tratar lados políticos de modo diferente",
                        "texto": f"Ao trocar apenas termos de um lado político pelo equivalente do outro nos mesmos textos ofensivos (n={cf['n']}), "
                                 f"a pontuação média mudou {cf['delta_medio_assinado']:+.2f} (IC95% {cf['ic95_bootstrap'][0]:+.2f} a {cf['ic95_bootstrap'][1]:+.2f}). "
                                 "O mesmo ato deveria receber o mesmo tratamento. Por isso o modelo não pode ser usado para priorizar casos sem revisão e controle de neutralidade.",
                        "experimento": "D"})
    if e:
        m, tudo = e["hatebr_teste"]["B_coeficientes_tfidf"], e["hatebr_teste"]["tudo"]
        achados.append({"id": "destaque_trechos", "titulo": "Destacar o trecho ofensivo é difícil",
                        "texto": f"Ao tentar marcar quais palavras tornam um texto ofensivo, o baseline teve F1 {m['f1']:.2f}, {'abaixo' if m['f1'] < tudo['f1'] else 'acima'} dos {tudo['f1']:.2f} de simplesmente marcar tudo (a maior parte das palavras desses comentários já está dentro do trecho ofensivo). "
                                 "O destaque ajuda a revisão humana, mas não é uma explicação confiável.",
                        "experimento": "E"})
    achados += _achados_ampliados(pasta, pct)
    return achados


def _achados_ampliados(pasta: Path, pct) -> list[dict[str, Any]]:
    """Achados dos protocolos AMP-E e AMP-G (catálogo ampliado). Só números agregados."""
    saida: list[dict[str, Any]] = []
    e, g = _ler("amp_e", pasta), _ler("amp_g", pasta)
    if g and g.get("status") == "executado":
        classes = [k for k, v in g["por_classe_em_dominio"].items() if "f1" in v and k != "linguagem_ofensiva"]
        ok = [k for k in g["classes_validadas"] if k != "linguagem_ofensiva"]
        saida.append({"id": "poucas_classes_passam", "titulo": "Poucas categorias passam no teste de qualidade",
                      "texto": f"No corpus de comentários do YouTube, só {len(ok)} de {len(classes)} categorias tiveram exemplos suficientes e desempenho bem acima do acaso para serem avaliadas "
                               "separadamente. As demais não devem ser usadas, mesmo que o resultado geral de 'tóxico ou não' pareça bom.",
                      "experimento": "AMP-G"})
        niv = g["concordancia_e_desempenho"].get("desempenho_binario_por_nivel_de_acordo") or {}
        un, dv = niv.get("unanimes_em_todas_as_classes"), niv.get("com_voto_dividido_em_alguma_classe")
        if un and dv and "roc_auc" in un and "roc_auc" in dv:
            saida.append({"id": "onde_humanos_discordam", "titulo": "Onde as pessoas discordam, o modelo também tropeça",
                          "texto": f"Nos comentários em que os anotadores concordaram em tudo, o modelo separa bem o ofensivo do não ofensivo (AUC {un['roc_auc']['media']:.2f}). "
                                   f"Onde houve voto dividido em alguma categoria, cai para {dv['roc_auc']['media']:.2f}. Parte do erro do modelo é desacordo humano, não só falha da máquina.",
                          "experimento": "AMP-G"})
    if e:
        c = (e["resultado_por_modelo_e_corpus"].get("multidomain_yt_toxbr:linguagem_ofensiva") or {}).get("multidomain_yt_toxbr")
        if c and c["taxa_fp_politico_nao_toxico"]["media"] is not None and c["taxa_fp_demais_negativos"]["media"] is not None:
            saida.append({"id": "politica_nao_e_ofensa", "titulo": "Falar de política não é ofender, mas o modelo se confunde",
                          "texto": f"Entre comentários sobre política que as pessoas anotadoras consideraram NÃO tóxicos, o modelo marcou como ofensivos cerca de {pct(c['taxa_fp_politico_nao_toxico']['media'])}, "
                                   f"contra {pct(c['taxa_fp_demais_negativos']['media'])} nos demais comentários não tóxicos. Crítica política legítima não deve ser tratada como ofensa por automação.",
                          "experimento": "AMP-E"})
    return saida


def varrer_vazamento(conteudo: Any, textos_corpora: list[str], minimo: int = 25) -> list[str]:
    """Retorna textos de corpora que aparecem no conteúdo publicado (deve ser vazio)."""
    bruto = json.dumps(conteudo, ensure_ascii=False)
    chaves_publicadas = {hash_chave(f["texto"]) for f in conteudo.get("frases", [])} if isinstance(conteudo, dict) else set()
    achados = [t for t in textos_corpora if len(t) >= minimo and t in bruto]
    achados += [t for t in textos_corpora if hash_chave(t) in chaves_publicadas]
    return achados


def _textos_dos_corpora_locais() -> list[str]:
    textos: list[str] = []
    pasta = paths.normalizados()
    if not pasta.exists():
        return textos
    for arq in pasta.glob("*.jsonl"):
        with arq.open(encoding="utf-8") as f:
            textos += [json.loads(l)["text"] for l in f if l.strip()]
    return textos


def construir_site(conn, destino: Path | None = None, incluir_rascunho: bool = False, verificar_corpora: bool = True,
                   paginas_estaticas: bool | None = None, pares_revisados: set[str] | None = None) -> dict[str, Any]:
    """`paginas_estaticas` (None = só quando o destino é o `site/data` real) gera `casos/`, `comparar/`, sitemap e robots."""
    from . import assuntos as assuntos_editoriais, paginas, pares as mod_pares
    from .casos import carregar_todos

    destino_real = destino is None  # só o destino real grava o registro versionado de casos já publicados
    gerar_paginas = destino_real if paginas_estaticas is None else paginas_estaticas
    destino = destino or paths.SITE / "data"
    frases = exportar_frases(conn, incluir_rascunho=False)
    com_dado_pessoal = [f["id"] for f in frases["frases"] if anonimizacao.identificaveis(f["texto"])]
    if com_dado_pessoal:
        raise VazamentoDetectado(f"frase(s) com dado identificável (link, @, telefone, documento): {com_dado_pessoal}")
    if verificar_corpora:
        achados = varrer_vazamento(frases, _textos_dos_corpora_locais())
        if achados:
            raise VazamentoDetectado(f"{len(achados)} texto(s) de corpora científicos encontrados no conteúdo público")
    destino.mkdir(parents=True, exist_ok=True)
    ids_publicados = {f["id"] for f in frases["frases"]}
    todos_ids = {f["id"] for f in carregar_todos()["frases"]}
    comparacoes = mod_pares.exportar(ids_publicados, mod_pares.carregar(ids_validos=todos_ids), revisados=pares_revisados)
    camada_assuntos = assuntos_editoriais.exportar(frases["frases"], comparacoes.get("pares") or [])
    arquivos = {
        "pares.json": comparacoes,
        "assuntos.json": camada_assuntos,
        "frases.json": frases, "taxonomia.json": taxonomia_publica(), "catalogo.json": catalogo_publico(), "referencias.json": referencias_publicas(),
        "contexto.json": contexto_publico(), "achados.json": {"gerado_dos_relatorios": achados_dos_relatorios(), "aviso": AVISO},
        "participacao.json": participacao.resultados_publicos(conn, {f["id"] for f in frases["frases"]}),
    }
    for nome, conteudo in arquivos.items():
        (destino / nome).write_text(json.dumps(conteudo, indent=2, ensure_ascii=False), encoding="utf-8")
    rascunho = 0
    if incluir_rascunho:
        pasta = destino / "_rascunho"
        pasta.mkdir(exist_ok=True)
        r = exportar_frases(conn, incluir_rascunho=True)
        (pasta / "frases.json").write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
        rascunho = len(r["frases"])
    resumo_paginas: dict[str, int] = {}
    if gerar_paginas:
        resumo_paginas = paginas.gerar(frases["frases"], comparacoes["pares"], destino.parent,
                                      registro=paginas.REGISTRO if destino_real else None,
                                      assuntos=camada_assuntos.get("assuntos") or [])
    return {"frases_publicadas": len(frases["frases"]), "frases_rascunho_local": rascunho, "destino": str(destino),
            "pares_publicados": len(comparacoes["pares"]), "paginas": resumo_paginas}
