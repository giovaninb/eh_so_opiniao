"""Geração de documentação a partir dos catálogos (fonte única de verdade)."""

from __future__ import annotations

from . import registry


def tabela_mapeamento() -> str:
    linhas = ["| Dataset | Rótulo original | Rótulo da taxonomia | Relação | Observação |", "|---|---|---|---|---|"]
    for c in registry.correspondencias():
        alvo = c.alvo or "— (fora da taxonomia v1)"
        linhas.append(f"| {c.dataset_id} | `{c.original}` | {alvo} | {c.relacao} | {c.nota} |")
    return "\n".join(linhas)


def tabela_taxonomia() -> str:
    linhas = ["| Classe | Tipo | Definição | Não é |", "|---|---|---|---|"]
    for rid, r in registry.rotulos_taxonomia().items():
        linhas.append(f"| `{rid}` | {r['tipo']} | {r['definicao']} | {r.get('nao_e', '')} |")
    return "\n".join(linhas)


def _licenca_curta(info: dict) -> str:
    cond = info["condicoes_licenca"]
    return info["licenca"] if cond["declarada"] and len(info["licenca"]) < 40 else "não declarada (condições registradas)"


def tabela_catalogo() -> str:
    linhas = ["| Dataset | Licença | Acesso | Status | Integração | Registros confirmados | Plataforma |", "|---|---|---|---|---|---|---|"]
    for ds_id in registry.listar_datasets():
        i = registry.dataset(ds_id)
        n = i["registros_confirmados"]
        registros = "não confirmado (sem arquivo lido)" if n is None else f"{n:,}".replace(",", ".")
        linhas.append(f"| {i['nome']} | {_licenca_curta(i)} | {i['acesso']} | {i['status_acesso']} | {i['integracao']} | {registros} | {i['plataforma']} |")
    return "\n".join(linhas)


# ------------------------------------------------------------------ documentos gerados
import json  # noqa: E402

from . import paths  # noqa: E402

CABECALHO = "<!-- GERADO AUTOMATICAMENTE por `python -m eh_so_opiniao docs`. Não edite à mão. -->\n\n"


def _mv(m: dict | None) -> str:
    if not m or m.get("media") is None:
        return "—"
    return f"{m['media']:.3f} ± {m['desvio']:.3f}"


def _rel(nome: str) -> dict | None:
    caminho = paths.RELATORIOS / f"experimento_{nome}.json"
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else None


def mapeamento_md() -> str:
    return (CABECALHO + f"# Mapeamento de rótulos (versão {registry.versao_mapeamento()})\n\n"
            "Cada linha liga um rótulo ORIGINAL de um dataset a uma classe da taxonomia "
            f"(v{registry.versao_taxonomia()}). Fonte única: `datasets/label_mapping.yaml`.\n\n"
            "- **equivalente**: definição e escopo coincidem.\n- **aproximado**: há sobreposição, mas escopo, definição ou domínio diferem; "
            "nunca é tratado como equivalente em experimentos.\n- **incompativel**: sem classe correspondente na taxonomia v1; o rótulo fica só em `original_labels`.\n\n"
            "Datasets NÃO são fundidos: cada amostra carrega apenas rótulos do próprio dataset; valores ausentes são permitidos.\n\n"
            + tabela_mapeamento() + "\n")


def taxonomia_md() -> str:
    return (CABECALHO + f"# Taxonomia (versão {registry.versao_taxonomia()})\n\n"
            "- **supervisionado**: há rótulo anotado por humanos em dataset catalogado que se relaciona com a classe.\n"
            "- **exploratorio**: não há rótulo anotado; só regras e revisão humana. Resultado é hipótese, não medição.\n"
            "- **salvaguarda**: evita confundir crítica política legítima, ironia ou ambiguidade com discriminação.\n\n"
            "Nenhuma classe afirma crime, intenção ou identidade de autor. `possivel_assedio_eleitoral_contextual` só faz sentido com contexto laboral.\n\n"
            + tabela_taxonomia() + "\n")


def _render(valor, nivel: int = 0) -> str:
    """Renderiza estruturas livres do registry (ficha científica) como lista aninhada de Markdown."""
    pad = "  " * nivel
    saida = []
    if isinstance(valor, dict):
        for k, v in valor.items():
            nome = k.replace("_", " ")
            saida.append(f"{pad}- **{nome}**:\n{_render(v, nivel + 1)}" if isinstance(v, (dict, list)) else f"{pad}- **{nome}**: {v}\n")
    elif isinstance(valor, list):
        for v in valor:
            saida.append(f"{pad}-\n{_render(v, nivel + 1)}" if isinstance(v, (dict, list)) else f"{pad}- {v}\n")
    else:
        saida.append(f"{pad}{valor}\n")
    return "".join(saida)


def _bloco_licenca(i: dict) -> str:
    c = i["condicoes_licenca"]
    linhas = [f"- Condições de licença (verificadas em {c['verificado_em']}):\n",
              f"  - declarada: {'sim' if c['declarada'] else 'NÃO'} · identificador: {c['identificador']}\n",
              f"  - fonte da verificação: {c['fonte_da_verificacao']}\n",
              f"  - uso neste projeto: {c['uso_pelo_projeto']}\n",
              f"  - exige reconhecimento explícito do operador antes do download: {'sim (`--aceito-licenca`)' if c['exige_reconhecimento_do_operador'] else 'não'}\n",
              "  - restrições:\n"]
    linhas += [f"    - {r}\n" for r in c["restricoes"]]
    return "".join(linhas)


def datasets_md() -> str:
    partes = [CABECALHO, "# Catálogo de datasets\n\nFonte: `datasets/registry.yaml`. Estados de acesso: `acessado` (arquivo no cache local, hash conferido), "
              "`pendente_autorizacao` (restrito; nada é contornado) e `pendente_fonte` (sem fonte pública verificável; nenhum dado é lido nem inventado). "
              "Integração: `integrado` (entra no pipeline e nos experimentos), `somente_sobreposicao` (só para medir sobreposição de textos) e `pendente_fonte`.\n\n",
              tabela_catalogo(), "\n\n"]
    for ds_id in registry.listar_datasets():
        i = registry.dataset(ds_id)
        n = i["registros_confirmados"]
        partes.append(f"## {i['nome']} (`{ds_id}`)\n\n")
        partes.append(f"- Versão/revisão: `{i['versao']}` · data: {i['data_versao']}\n- Licença: {i['licenca']}\n- Redistribuição: {i['redistribuicao']}\n"
                      f"- Acesso: `{i['acesso']}` · status: **{i['status_acesso']}** · integração: `{i['integracao']}`\n- Formatos: {', '.join(i['formatos']) or '—'} · plataforma: {i['plataforma']} · idioma: {i['idioma']}\n"
                      f"- Registros confirmados: {'não confirmado (nenhum arquivo foi lido)' if n is None else n}" + (f" ({i['nota_contagem']})" if i.get("nota_contagem") else "")
                      + (f" · declarados no artigo: {i['registros_declarados_no_artigo']}" if i.get("registros_declarados_no_artigo") else "") + "\n"
                      f"- Esquema de anotação: {i['esquema_anotacao']}\n- Contexto: {i['contexto']}\n- Integridade: {i['hash_ou_revisao']}\n- Referência: {i['referencia']}\n- Fonte: {i['url_origem']}\n")
        if i.get("url_artigo"):
            partes.append(f"- Artigo: {i['url_artigo']}\n")
        partes.append(_bloco_licenca(i))
        if i.get("pendencia"):
            partes.append(f"- **Pendência**: {i['pendencia']}\n")
        if i.get("fontes_verificadas"):
            partes.append("- Fontes verificadas:\n" + "".join(f"  - {f['fonte']}: {f['resultado']} ({f['verificado_em']})\n" for f in i["fontes_verificadas"]))
        if i.get("verificacao_cruzada_hatebrxplain"):
            partes.append("- Verificação cruzada com o HateBRXplain:\n" + _render(i["verificacao_cruzada_hatebrxplain"], 1))
        if i.get("ficha_cientifica"):
            partes.append("- Ficha científica:\n" + _render(i["ficha_cientifica"], 1))
        partes.append("- Limitações e vieses:\n")
        partes += [f"  - {x}\n" for x in i["limitacoes_vieses"]]
        partes.append("\n")
    return "".join(partes)


def referencias_md() -> str:
    partes = [CABECALHO, "# Referências científicas\n\nFonte: `datasets/registry.yaml` e `datasets/referencias.yaml`. "
              "A lista é a mesma que o site mostra na seção científica (`site/data/referencias.json`). Nenhum texto de corpus aparece aqui.\n\n"
              "## Datasets catalogados\n\n"]
    for ds_id in registry.listar_datasets():
        i = registry.dataset(ds_id)
        partes.append(f"- **{i['nome']}** — {i['referencia']} Fonte: {i['url_origem']}" + (f" · Artigo: {i['url_artigo']}" if i.get("url_artigo") else "") + f" · status: {i['status_acesso']}\n")
    ordem = {"artigo": "Artigos dos datasets", "recurso_explicabilidade": "Recursos de explicabilidade", "dataset_avaliado": "Datasets avaliados (só sobreposição)",
             "referencia_teorica": "Referências teóricas (não são datasets)"}
    refs = registry.carregar_referencias()
    for tipo, titulo in ordem.items():
        itens = [r for r in refs if r["tipo"] == tipo]
        if not itens:
            continue
        partes.append(f"\n## {titulo}\n\n")
        for r in itens:
            partes.append(f"### {r['titulo']}\n\n- Citação: {r['citacao']}\n- Veículo: {r['veiculo']} · ano: {r['ano']}\n- Endereço: {r['url']}\n"
                          + (f"- DOI: {r['doi']}\n" if r.get("doi") else "") + f"- Papel no projeto: {r['papel_no_projeto']}\n- Direitos de uso: {r['licenca_ou_direitos']}\n- O que NÃO é: {r['o_que_nao_e']}\n\n")
    return "".join(partes)


def _json_rel(nome: str) -> dict | None:
    caminho = paths.RELATORIOS / nome
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else None


def compatibilidade_md() -> str:
    partes = [CABECALHO, "# Compatibilidade entre datasets\n\nComo os datasets se comparam e por que NÃO são fundidos. Fontes: `datasets/registry.yaml`, "
              "`datasets/label_mapping.yaml`, `relatorios/sobreposicao_corpora.json`.\n\n## Plataforma, domínio, anotação e licença\n\n"]
    partes.append("| Dataset | Plataforma | Idioma | Licença | Redistribuição | Integração |\n|---|---|---|---|---|---|\n")
    for ds_id in registry.listar_datasets():
        i = registry.dataset(ds_id)
        partes.append(f"| {i['nome']} | {i['plataforma']} | {i['idioma']} | {_licenca_curta(i)} | {i['redistribuicao'].split('.')[0]} | {i['integracao']} |\n")
    partes.append("\n")
    for ds_id in registry.listar_datasets():
        i = registry.dataset(ds_id)
        partes.append(f"- **{ds_id}** · domínio/contexto: {i['contexto']} · anotação e consenso: {i['esquema_anotacao']}\n")
    partes.append("\n## Classes da taxonomia por dataset (relação declarada, rótulo original)\n\n"
                  "`equivalente`: mesma definição e escopo. `aproximado`: sobreposição, mas definição, escopo ou domínio diferem; nunca é tratado como equivalente. "
                  "`—`: o dataset não tem rótulo para a classe. A coluna de cada dataset mostra `relação (rótulo original)`.\n\n")
    datasets = registry.listar_datasets()
    partes.append("| Classe | " + " | ".join(datasets) + " |\n|---|" + "---|" * len(datasets) + "\n")
    mapa: dict[tuple[str, str], list[str]] = {}
    for c in registry.correspondencias():
        if c.alvo:
            mapa.setdefault((c.alvo, c.dataset_id), []).append(f"{c.relacao} (`{c.original}`)")
    for classe, r in registry.rotulos_taxonomia().items():
        celulas = [" / ".join(mapa.get((classe, ds), [])) or "—" for ds in datasets]
        if any(c != "—" for c in celulas):
            partes.append(f"| `{classe}` ({r['tipo']}) | " + " | ".join(celulas) + " |\n")
    sem = [rid for rid, r in registry.rotulos_taxonomia().items() if all((rid, ds) not in mapa for ds in datasets)]
    partes.append("\nClasses sem rótulo anotado em nenhum dataset (exploratórias ou salvaguardas): " + ", ".join(f"`{x}`" for x in sem) + ".\n")
    partes.append("\n## Sobreposição de textos\n\n")
    sob = _json_rel("sobreposicao_corpora.json")
    if not sob:
        partes.append("Ainda não medida (`python -m eh_so_opiniao sobreposicao`).\n")
    else:
        partes.append(f"Método: {sob['metodo']}.\n\n| Par | Textos em comum | % do primeiro | % do segundo |\n|---|---|---|---|\n")
        for par, v in sob["pares"].items():
            a, b = par.split("__")
            partes.append(f"| {a} × {b} | {v['em_comum']} | {v['fracao_de_a']:.1%} | {v['fracao_de_b']:.1%} |\n")
        partes.append(f"\n{sob['leitura']}\n\n**RacismoBR**: {sob['racismobr']['sobreposicao_esperada']}\n")
    partes.append("\n## Consequências para os experimentos\n\n"
                  "- Nenhum dataset é fundido; cada rótulo vem do próprio dataset e carrega a relação declarada.\n"
                  "- Avaliação entre datasets remove textos vistos no treino e sempre separa os resultados por par treino × teste.\n"
                  "- Diferenças de desempenho fora de domínio misturam definição de classe, plataforma, época e anotadores; não são só erro de modelo.\n"
                  "- A TuPyE reúne ToLD-Br e HateBR, então não serve para avaliar generalização entre eles.\n")
    return "".join(partes)



def _pct(x) -> str:
    return "—" if x is None else f"{x:.3f}"


def _linha_resumo(nome: str, c: dict) -> str:
    if "f1" not in c:
        return f"| {nome} | — | — | — | — | — | {c.get('status', 'sem resultado')} |\n"
    aviso = "suporte insuficiente (< 30 positivos)" if c.get("suporte_insuficiente") else ""
    return (f"| {nome} | {_mv(c['precision'])} | {_mv(c['recall'])} | {_mv(c['f1'])} | {_mv(c['average_precision'])} | "
            f"{c['positivos_por_semente']} | {aviso} |\n")


def resultados_ampliados_md() -> str:
    a, b, c, d, e, f, g = (_rel(f"amp_{x}") for x in "abcdefg")
    conc, sob = _json_rel("concordancia_multidomain_yt_toxbr.json"), _json_rel("sobreposicao_corpora.json")
    if not any((a, b, c, d, e, f, g, conc, sob)):
        return ""
    s = ["\n# Catálogo ampliado: MultiDomainYT-ToxBR, RacismoBR e recursos complementares\n\n"
         "Protocolos `AMP-A` a `AMP-G` de `evaluation/experiments_ampliados.py`. Resultados separados por dataset e por classe; nenhum dataset é fundido; "
         "cada classe é um classificador binário independente; limiar escolhido na validação; média ± desvio entre as sementes 13, 42 e 2026. "
         "Suporte < 30 positivos no teste ⇒ não interpretar P/R/F1.\n\n"
         "> O F1 binário do MultiDomainYT-ToxBR (0,78 no artigo) mede “tóxico ou não” e **não** indica capacidade de identificar categorias específicas.\n\n"]
    if conc:
        s.append("## Concordância entre anotadores (MultiDomainYT-ToxBR, recalculada das planilhas)\n\n"
                 "| Classe | κ grupo 1 | κ grupo 2 | κ artigo g1 | κ artigo g2 | Positivos por maioria (g1 + g2) |\n|---|---|---|---|---|---|\n")
        g1, g2 = conc["por_grupo"]["grupo_1"]["classes"], conc["por_grupo"]["grupo_2"]["classes"]
        for k in g1:
            s.append(f"| `{k}` | {_pct(g1[k]['kappa_fleiss'])} | {_pct(g2[k]['kappa_fleiss'])} | {_pct(g1[k]['kappa_reportado_no_artigo'])} | "
                     f"{_pct(g2[k]['kappa_reportado_no_artigo'])} | {g1[k]['positivos_por_maioria'] + g2[k]['positivos_por_maioria']} |\n")
        s.append(f"\n{conc['leitura']}\n\n")
    if sob:
        s.append(f"## Sobreposição entre corpora\n\nMétodo: {sob['metodo']}. Tabela completa em `docs/COMPATIBILIDADE_DATASETS.md`. {sob['leitura']}\n\n")
    if a:
        s.append(f"## AMP-A — RacismoBR (classificadores binários de racismo)\n\nStatus: **{a['status']}**. ")
        s.append(f"{a.get('motivo', '')} {a.get('nota', '')}\n\n")
    if b:
        s.append("## AMP-B — Generalização entre datasets\n\nLinhas: treino. Cada célula é UM par treino → teste para UM rótulo, F1 da classe positiva (limiar da validação do treino). "
                 "Em domínio = split de teste; fora de domínio = dataset inteiro sem textos vistos no treino. Positivos entre colchetes (por semente).\n\n")
        for alvo, v in b["alvos"].items():
            s.append(f"### Rótulo `{alvo}`\n\nIndisponíveis: {', '.join(f'{k} ({x['status']})' for k, x in v['datasets_indisponiveis'].items()) or 'nenhum'}. "
                     f"Definições: " + "; ".join(f"{ds}: `{d['rotulo_original']}` ({d['relacao']})" for ds, d in v["definicoes"].items()) + "\n\n"
                     "| Treino → Teste | Domínio | F1 | Revocação | Precisão | AP | Prevalência | Positivos | Aviso |\n|---|---|---|---|---|---|---|---|---|\n")
            for par, x in v["matriz"].items():
                if "f1" not in x:
                    continue
                s.append(f"| {par} | {'em' if x['em_dominio'] else 'fora'} | {_mv(x['f1'])} | {_mv(x['recall'])} | {_mv(x['precision'])} | {_mv(x['average_precision'])} | "
                         f"{_mv(x['prevalencia'])} | {x['positivos_por_semente']} | {'suporte insuficiente' if x['suporte_insuficiente'] else ''} |\n")
            s.append("\n")
    if c:
        s.append(f"## AMP-C — Racismo explícito × implícito\n\nStatus: **{c['status']}**. {c.get('motivo', '')} Nenhum dataset integrado traz essa distinção e ela não é inferida por regra.\n\n")
    if d:
        s.append("## AMP-D — Xenofobia e discriminação regional\n\n| Treino → Teste | F1 | Revocação | Precisão | AP | Prevalência | Positivos | Aviso |\n|---|---|---|---|---|---|---|---|\n")
        for par, x in d["matriz_xenofobia"].items():
            s.append(f"| {par} | {_mv(x['f1'])} | {_mv(x['recall'])} | {_mv(x['precision'])} | {_mv(x['average_precision'])} | {_mv(x['prevalencia'])} | {x['positivos_por_semente']} | "
                     f"{'suporte insuficiente' if x['suporte_insuficiente'] else ''} |\n")
        s.append("\nComposição dos positivos de xenofobia (marcadores lexicais simples; diagnóstico, não rótulo):\n\n| Dataset | Positivos | Marcador regional | Marcador de nacionalidade | Sem marcador |\n|---|---|---|---|---|\n")
        for ds, x in d["composicao_dos_positivos"].items():
            s.append(f"| {ds} | {x['positivos_xenofobia']} | {x['com_marcador_regional']} | {x['com_marcador_nacionalidade']} | {x['sem_marcador_da_lista']} |\n")
        s.append(f"\n{d['discriminacao_regional']['leitura']}\n\n")
    if e:
        s.append(f"## AMP-E — Falsos positivos em comentários políticos não tóxicos\n\n{e['definicao_de_alvo']}\n\n"
                 "| Modelo → Corpus | Domínio | Taxa de FP (político não tóxico) | Taxa de FP (demais negativos) | n político por semente | IC95% Wilson (semente 42) |\n|---|---|---|---|---|---|\n")
        for mod, por in e["resultado_por_modelo_e_corpus"].items():
            for ds, x in por.items():
                cont = next((k for k in x["contagens_por_semente"] if k["semente"] == 42), x["contagens_por_semente"][0])
                s.append(f"| {mod} → {ds} | {'em' if x['em_dominio'] else 'fora'} | {_mv(x['taxa_fp_politico_nao_toxico'])} | {_mv(x['taxa_fp_demais_negativos'])} | "
                         f"{[k['n_politico_nao_toxico'] for k in x['contagens_por_semente']]} | {cont['ic95_wilson_politico']} |\n")
        s.append("\n")
    if f and f.get("status") == "executado":
        h = f["teto_humano_anotador_1_vs_2"]
        s.append(f"## AMP-F — Trechos humanos × trechos destacados por modelos (HateBRXplain)\n\nTeste: {f['amostras']['teste']} comentários ofensivos com trecho "
                 f"({f['amostras']['teste_com_os_dois_anotadores']} com os dois anotadores). Teto humano (anotador 1 × 2, por token): P {h['precision']:.3f} · R {h['recall']:.3f} · "
                 f"F1 {h['f1']:.3f} · κ {h['kappa_de_cohen_por_token']}.\n\n| Método | F1 vs união | F1 vs anotador 1 | F1 vs anotador 2 | R-precisão (ranking) | AP por token |\n|---|---|---|---|---|---|\n")
        rk = f["ranking_independente_de_limiar"]
        for k, v in f["metodos"].items():
            r = rk.get(k) or rk.get("aleatorio" if k.startswith("aleatorio") else k)
            rp = _mv(r["r_precision_media_por_comentario"]) if r else "—"
            apt = _pct(r["average_precision_tokens_agrupados"]) if r else "—"
            s.append(f"| {k} | {v['contra_uniao_dos_dois_anotadores']['f1']:.3f} | {v['contra_anotador_1']['f1']:.3f} | {v['contra_anotador_2']['f1']:.3f} | {rp} | {apt} |\n")
        sv = f["sensibilidade_do_modelo_a_remocao"]
        s.append(f"\nDensidade de tokens humanos: {rk['densidade_de_tokens_humanos']:.3f} (o acaso acerta cerca disso). {rk['leitura']}\n\n"
                 f"Sensibilidade do modelo à remoção ({sv['base']}): remover trechos humanos derruba a pontuação em {sv['remover_trechos_humanos']['queda_media_da_pontuacao']['media']:.3f} "
                 f"(deixa de marcar {sv['remover_trechos_humanos']['fracao_que_deixou_de_ser_marcado']:.1%}); remover o mesmo número de tokens aleatórios, "
                 f"{sv['remover_aleatorios_mesmo_numero']['queda_media_da_pontuacao']['media']:.3f}. {sv['leitura']}\n\n")
    elif f:
        s.append(f"## AMP-F — Trechos humanos × modelos\n\nStatus: **{f['status']}**.\n\n")
    if g and g.get("status") == "executado":
        s.append("## AMP-G — MultiDomainYT-ToxBR por classe, concordância e poucos exemplos\n\n"
                 "Um classificador binário por classe (um contra todos), teste do próprio dataset. Portão `validada`: ≥ 30 positivos no teste em todas as sementes **e** AP ≥ 2× a prevalência.\n\n"
                 "| Classe | Precisão | Revocação | F1 | AP | Positivos no teste | Validada |\n|---|---|---|---|---|---|---|\n")
        for k, v in g["por_classe_em_dominio"].items():
            if "f1" not in v:
                continue
            s.append(f"| `{k}` | {_mv(v['precision'])} | {_mv(v['recall'])} | {_mv(v['f1'])} | {_mv(v['average_precision'])} | {v['positivos_por_semente']} | {'sim' if v['validada'] else 'não'} |\n")
        s.append(f"\nClasses validadas: {', '.join(f'`{x}`' for x in g['classes_validadas'])}. As demais **não devem ser usadas** como classificador.\n\n")
        cc = g["concordancia_e_desempenho"]
        if cc.get("disponivel"):
            s.append("Desempenho do classificador binário por nível de acordo e por grupo de anotadores:\n\n| Estrato | AUC-ROC | Revocação | Taxa de FP | Positivos por semente |\n|---|---|---|---|---|\n")
            for nome, v in {**cc["desempenho_binario_por_nivel_de_acordo"], **cc["desempenho_binario_por_grupo_de_anotadores"]}.items():
                if "f1" in v:
                    s.append(f"| {nome} | {_mv(v['roc_auc'])} | {_mv(v['recall'])} | {_mv(v['taxa_falso_positivo'])} | {v['positivos_por_semente']} |\n")
            s.append(f"\n{cc['nota_nivel_de_acordo']} Correlação de Spearman entre κ médio e F1 por classe: {cc['correlacao_de_spearman_kappa_medio_x_f1']} ({cc['leitura_da_correlacao']})\n\n")
        s.append("Curva de aprendizado (F1 no teste × positivos no treino):\n\n| Classe | " + " | ".join(str(x["positivos_no_treino"]) for x in next(iter(g["curva_de_aprendizado_por_positivos"].values()), [])) + " |\n")
        for cls, pts in g["curva_de_aprendizado_por_positivos"].items():
            if pts:
                s.append(f"| `{cls}` | " + " | ".join(_mv(x["f1"]) for x in pts) + " |\n")
        s.append("\n")
    return "".join(s)


def resultados_md() -> str:
    a, b, c, d, e = (_rel(x) for x in "abcde")
    if not any((a, b, c, d, e)):
        return CABECALHO + "# Resultados\n\nExperimentos ainda não executados (`python -m eh_so_opiniao experimentos`).\n"
    s = [CABECALHO, "# Resultados dos experimentos\n\nTodos os números abaixo foram calculados pelos scripts em `evaluation/experiments.py` a partir dos corpora "
         "baixados e verificados por SHA-256 (hashes nos JSON de `relatorios/`). Média ± desvio entre sementes de split (13, 42, 2026). "
         "Sem ajuste fino no teste: limiares são escolhidos na validação. Não são resultados de produção.\n\n"]
    if b:
        s.append("## B — HateBR (teste, split por publicação)\n\n| Método | Precision | Recall | F1 (positiva) | Macro-F1 (2 classes) |\n|---|---|---|---|---|\n")
        nomes = {"trivial": "Chute: sempre ofensivo", "A_lexico": "A — léxico de insultos", "B_lr_0.5": "B — TF-IDF+LR (limiar 0,5)",
                 "B_lr_val_f1": "B — TF-IDF+LR (limiar F1 na validação)", "B_lr_precisao>=0.85": "B — TF-IDF+LR (precisão>=0,85 na validação)", "B_svm_val_f1": "B — TF-IDF+SVM (limiar F1 na validação)"}
        for k, n in nomes.items():
            v = b["teste_hatebr"][k]
            s.append(f"| {n} | {_mv(v['precision'])} | {_mv(v['recall'])} | {_mv(v['f1'])} | {_mv(v['macro_f1'])} |\n")
        s.append("\n### B — transferência HateBR → ToLD-Br (sem textos em comum)\n\n| Método | Precision | Recall | F1 (positiva) | Macro-F1 (2 classes) |\n|---|---|---|---|---|\n")
        t = b["transferencia_para_told"]
        for k, n in (("trivial", "Chute: sempre ofensivo"), ("A_lexico", "A — léxico"), ("B_lr_val_f1", "B — TF-IDF+LR")):
            s.append(f"| {n} | {_mv(t[k]['precision'])} | {_mv(t[k]['recall'])} | {_mv(t[k]['f1'])} | {_mv(t[k]['macro_f1'])} |\n")
        cal = b["detalhes_semente_principal"]["calibracao_lr"]
        s.append(f"\nPrevalência de ofensivos no ToLD-Br (rótulo derivado por votos, só aproximado ao do HateBR): {t['prevalencia_told']:.3f}. **Atenção:** o F1 da classe positiva pode favorecer o chute 'sempre ofensivo' quando a prevalência é alta; o macro-F1 (média das duas classes) é a leitura mais honesta. Calibração (HateBR, semente 42): Brier {cal['brier']}, ECE {cal['ece']}.\n\n")
    if a:
        s.append("## A — ToLD-Br, classes de grupo (em domínio)\n\nF1 (média ± desvio) no teste do ToLD-Br. Suporte = positivos no teste por semente. **Suporte baixo ⇒ não interpretar.** "
                 "Não há segundo dataset aprovado com estas classes, então não existe avaliação fora de domínio.\n\n"
                 "| Classe | Relação (ToLD) | F1 em domínio | Positivos no teste |\n|---|---|---|---|\n")
        for k, v in a["por_classe"].items():
            s.append(f"| {k} | {v['relacao_told']} | {_mv(v['dominio_told_teste']['f1'])} | {v['dominio_told_teste']['positivos_teste_por_semente']} |\n")
        s.append("\n")
    if c:
        s.append("## C — Combinar bases (F1, limiar da validação)\n\nLinhas: treino. Colunas: teste.\n\n| Treino \\ Teste | hatebr | told_br |\n|---|---|---|\n")
        for tr, linha in c["matriz_treino_x_teste"].items():
            s.append(f"| {tr} | " + " | ".join(_mv(linha[t]["limiar_val_f1"]["f1"]) + (" *" if linha[t]["em_dominio"] else "") for t in ("hatebr", "told_br")) + " |\n")
        s.append("\n`*` = base de teste presente no treino (em domínio).\n\n| Teste | Referência | Combinado | F1 ref. | F1 comb. | Δ |\n|---|---|---|---|---|---|\n")
        for g in c["efeito_de_combinar_em_dominio"]:
            s.append(f"| {g['teste']} | {g['treino_referencia']} | {g['treino_combinado']} | {g['f1_referencia']:.3f} | {g['f1_combinado']:.3f} | {g['delta']:+.3f} |\n")
        s.append("\n")
    if d:
        s.append("## D — Neutralidade partidária (contrafactual) e falsos positivos\n\nTroca espelhada de termos (Lula↔Bolsonaro, petista↔bolsonarista, esquerda↔direita, PT↔PL) nos mesmos textos. "
                 "Δ = pontuação após troca − antes. IC95% por bootstrap.\n\n| Modelo | Grupo | Direção | n | Δ médio | IC95% | Decisões que mudam |\n|---|---|---|---|---|---|---|\n")
        for mod, v in d["contrafactual"].items():
            for grupo in ("nao_ofensivos", "ofensivos"):
                for dr, x in v[grupo].items():
                    if x.get("n"):
                        s.append(f"| {mod} | {grupo} | {dr} | {x['n']} | {x['delta_medio_assinado']:+.3f} | [{x['ic95_bootstrap'][0]:+.3f}, {x['ic95_bootstrap'][1]:+.3f}] | {x['fracao_mudou_decisao']:.1%} |\n")
        fp = d["falsos_positivos_hatebr_nao_ofensivos"]
        s.append(f"\nFalsos positivos em comentários NÃO ofensivos do HateBR (teste, n={fp['n_nao_ofensivos_teste']}): taxa geral {fp['taxa_falso_positivo_geral']:.3f}. "
                 f"Com termo político: {fp['menciona_termo_politico']['com']['taxa_fp']} (n={fp['menciona_termo_politico']['com']['n']}); sem: {fp['menciona_termo_politico']['sem']['taxa_fp']} (n={fp['menciona_termo_politico']['sem']['n']}).\n\n")
        fx = d.get("fixtures_do_monitor", {})
        if fx.get("disponivel"):
            s.append(f"As 27 fixtures do monitor foram pontuadas apenas de forma qualitativa ({fx['carater']}).\n\n")
    if e:
        s.append("## E — Destaque de trechos (F1 por token)\n\nTreino e teste no HateBR; trechos derivados das justificativas do HateBRXplain (aproximação por busca textual).\n\n"
                 "| Método | HateBR teste (P / R / F1) |\n|---|---|\n")
        for k in ("B_coeficientes_tfidf", "A_lexico", "tudo", "aleatorio_prob_0.3"):
            h = e["hatebr_teste"][k]
            s.append(f"| {k} | {h['precision']:.3f} / {h['recall']:.3f} / {h['f1']:.3f} |\n")
        x = e["exclusoes"]
        s.append(f"\nExclusões: {x['hatebr_ofensivas_sem_trecho_ignoradas']} comentários ofensivos sem trecho justificado (de {x['hatebr_ofensivas']}).\n\n")
    s.append("## Baseline C (transformer)\n\n**Não executado.** `torch`/`transformers` não fazem parte do ambiente reprodutível; plano em `classifiers/transformer.py`.\n")
    s.append(resultados_ampliados_md())
    return "".join(s)


GERADOS = {"MAPEAMENTO_ROTULOS.md": mapeamento_md, "TAXONOMIA.md": taxonomia_md, "DATASETS.md": datasets_md, "REFERENCIAS.md": referencias_md,
           "COMPATIBILIDADE_DATASETS.md": compatibilidade_md, "RESULTADOS.md": resultados_md}


def gerar_documentos() -> list[str]:
    paths.DOCS.mkdir(parents=True, exist_ok=True)
    escritos = []
    for nome, fn in GERADOS.items():
        (paths.DOCS / nome).write_text(fn(), encoding="utf-8")
        escritos.append(str(paths.DOCS / nome))
    return escritos
