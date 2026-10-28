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


def tabela_catalogo() -> str:
    linhas = ["| Dataset | Licença | Acesso | Status | Registros confirmados | Plataforma |", "|---|---|---|---|---|---|"]
    for ds_id in registry.listar_datasets():
        i = registry.dataset(ds_id)
        licenca = i["licenca"] if len(i["licenca"]) < 30 else "não declarada (contato exigido)"
        linhas.append(f"| {i['nome']} | {licenca} | {i['acesso']} | {i['status_acesso']} | {i['registros_confirmados']} | {i['plataforma']} |")
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


def datasets_md() -> str:
    partes = [CABECALHO, "# Catálogo de datasets\n\nFonte: `datasets/registry.yaml`.\n\n", tabela_catalogo(), "\n\n"]
    for ds_id in registry.listar_datasets():
        i = registry.dataset(ds_id)
        partes.append(f"## {i['nome']} (`{ds_id}`)\n\n")
        partes.append(f"- Versão/revisão: `{i['versao']}` · data: {i['data_versao']}\n- Licença: {i['licenca']}\n- Redistribuição: {i['redistribuicao']}\n"
                      f"- Acesso: `{i['acesso']}` · status: **{i['status_acesso']}**\n- Formatos: {', '.join(i['formatos'])} · plataforma: {i['plataforma']} · idioma: {i['idioma']}\n"
                      f"- Registros confirmados: {i['registros_confirmados']}" + (f" ({i['nota_contagem']})" if i.get("nota_contagem") else "") + "\n"
                      f"- Esquema de anotação: {i['esquema_anotacao']}\n- Contexto: {i['contexto']}\n- Integridade: {i['hash_ou_revisao']}\n- Referência: {i['referencia']}\n- Fonte: {i['url_origem']}\n- Limitações e vieses:\n")
        partes += [f"  - {x}\n" for x in i["limitacoes_vieses"]]
        partes.append("\n")
    return "".join(partes)


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
    return "".join(s)


GERADOS = {"MAPEAMENTO_ROTULOS.md": mapeamento_md, "TAXONOMIA.md": taxonomia_md, "DATASETS.md": datasets_md, "RESULTADOS.md": resultados_md}


def gerar_documentos() -> list[str]:
    paths.DOCS.mkdir(parents=True, exist_ok=True)
    escritos = []
    for nome, fn in GERADOS.items():
        (paths.DOCS / nome).write_text(fn(), encoding="utf-8")
        escritos.append(str(paths.DOCS / nome))
    return escritos
