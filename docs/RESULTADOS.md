<!-- GERADO AUTOMATICAMENTE por `python -m eh_so_opiniao docs`. Não edite à mão. -->

# Resultados dos experimentos

Todos os números abaixo foram calculados pelos scripts em `evaluation/experiments.py` a partir dos corpora baixados e verificados por SHA-256 (hashes nos JSON de `relatorios/`). Média ± desvio entre sementes de split (13, 42, 2026). Sem ajuste fino no teste: limiares são escolhidos na validação. Não são resultados de produção.

## B — HateBR (teste, split por publicação)

| Método | Precision | Recall | F1 (positiva) | Macro-F1 (2 classes) |
|---|---|---|---|---|
| Chute: sempre ofensivo | 0.539 ± 0.069 | 1.000 ± 0.000 | 0.698 ± 0.060 | 0.349 ± 0.030 |
| A — léxico de insultos | 0.987 ± 0.008 | 0.224 ± 0.018 | 0.364 ± 0.022 | 0.523 ± 0.042 |
| B — TF-IDF+LR (limiar 0,5) | 0.899 ± 0.044 | 0.841 ± 0.008 | 0.868 ± 0.017 | 0.863 ± 0.002 |
| B — TF-IDF+LR (limiar F1 na validação) | 0.870 ± 0.050 | 0.883 ± 0.019 | 0.875 ± 0.019 | 0.864 ± 0.007 |
| B — TF-IDF+LR (precisão>=0,85 na validação) | 0.883 ± 0.056 | 0.858 ± 0.031 | 0.868 ± 0.014 | 0.860 ± 0.002 |
| B — TF-IDF+SVM (limiar F1 na validação) | 0.870 ± 0.057 | 0.867 ± 0.029 | 0.866 ± 0.016 | 0.856 ± 0.004 |

### B — transferência HateBR → OLID-BR (sem textos em comum)

| Método | Precision | Recall | F1 (positiva) | Macro-F1 (2 classes) |
|---|---|---|---|---|
| Chute: sempre ofensivo | 0.854 ± 0.000 | 1.000 ± 0.000 | 0.921 ± 0.000 | 0.461 ± 0.000 |
| A — léxico | 0.974 ± 0.000 | 0.384 ± 0.000 | 0.551 ± 0.000 | 0.445 ± 0.000 |
| B — TF-IDF+LR | 0.880 ± 0.002 | 0.863 ± 0.012 | 0.871 ± 0.005 | 0.583 ± 0.004 |

Prevalência de ofensivos no OLID-BR: 0.854. **Atenção:** com prevalência tão alta, o F1 da classe positiva favorece o chute 'sempre ofensivo'; o macro-F1 (média das duas classes) é a leitura mais honesta. Calibração (HateBR, semente 42): Brier 0.1144, ECE 0.1378.

## A — ToLD-Br → OLID-BR, classes de grupo

F1 (média ± desvio). Suporte = positivos no teste/avaliação por semente. **Suporte baixo ⇒ não interpretar.**

| Classe | Relação (ToLD/OLID) | F1 em domínio (ToLD teste) | Positivos | F1 cruzado (OLID) | Positivos |
|---|---|---|---|---|---|
| insulto_hostilidade | aproximado/aproximado | 0.520 ± 0.018 | [296, 279, 289] | 0.409 ± 0.006 | 5411 |
| lgbtfobia | aproximado/aproximado | 0.542 ± 0.019 | [18, 24, 22] | 0.431 ± 0.042 | 369 |
| misoginia | equivalente/aproximado | 0.321 ± 0.177 | [20, 19, 26] | 0.107 ± 0.057 | 450 |
| racismo | equivalente/equivalente | 0.086 ± 0.057 | [7, 7, 6] | 0.091 ± 0.035 | 89 |
| xenofobia | aproximado/aproximado | 0.158 ± 0.123 | [7, 10, 8] | 0.045 ± 0.019 | 127 |

## C — Combinar bases (F1, limiar da validação)

Linhas: treino. Colunas: teste.

| Treino \ Teste | hatebr | olid_br | told_br |
|---|---|---|---|
| hatebr | 0.875 ± 0.019 * | 0.872 ± 0.007 | 0.383 ± 0.006 |
| olid_br | 0.696 ± 0.059 | 0.920 ± 0.003 * | 0.329 ± 0.005 |
| told_br | 0.424 ± 0.066 | 0.477 ± 0.073 | 0.552 ± 0.007 * |
| hatebr+olid_br | 0.865 ± 0.026 * | 0.923 ± 0.001 * | 0.354 ± 0.005 |
| hatebr+olid_br+told_br | 0.847 ± 0.023 * | 0.888 ± 0.004 * | 0.539 ± 0.008 * |

`*` = base de teste presente no treino (em domínio).

| Teste | Referência | Combinado | F1 ref. | F1 comb. | Δ |
|---|---|---|---|---|---|
| hatebr | hatebr | hatebr+olid_br | 0.875 | 0.865 | -0.010 |
| hatebr | hatebr | hatebr+olid_br+told_br | 0.875 | 0.847 | -0.028 |
| olid_br | olid_br | hatebr+olid_br | 0.920 | 0.923 | +0.003 |
| olid_br | olid_br | hatebr+olid_br+told_br | 0.920 | 0.888 | -0.031 |
| told_br | told_br | hatebr+olid_br+told_br | 0.552 | 0.539 | -0.013 |

## D — Neutralidade partidária (contrafactual) e falsos positivos

Troca espelhada de termos (Lula↔Bolsonaro, petista↔bolsonarista, esquerda↔direita, PT↔PL) nos mesmos textos. Δ = pontuação após troca − antes. IC95% por bootstrap.

| Modelo | Grupo | Direção | n | Δ médio | IC95% | Decisões que mudam |
|---|---|---|---|---|---|---|
| hatebr | nao_ofensivos | esquerda_para_direita | 39 | -0.082 | [-0.126, -0.046] | 25.6% |
| hatebr | nao_ofensivos | direita_para_esquerda | 32 | +0.011 | [+0.004, +0.022] | 0.0% |
| hatebr | ofensivos | esquerda_para_direita | 99 | -0.114 | [-0.130, -0.099] | 20.2% |
| hatebr | ofensivos | direita_para_esquerda | 36 | +0.045 | [+0.022, +0.074] | 5.6% |
| hatebr+olid_br | nao_ofensivos | esquerda_para_direita | 39 | -0.059 | [-0.103, -0.023] | 20.5% |
| hatebr+olid_br | nao_ofensivos | direita_para_esquerda | 42 | -0.005 | [-0.012, +0.002] | 0.0% |
| hatebr+olid_br | ofensivos | esquerda_para_direita | 136 | -0.098 | [-0.114, -0.084] | 8.1% |
| hatebr+olid_br | ofensivos | direita_para_esquerda | 76 | +0.009 | [-0.002, +0.023] | 4.0% |

Falsos positivos em comentários NÃO ofensivos do HateBR (teste, n=429): taxa geral 0.121. Com termo político: 0.1222 (n=90); sem: 0.1209 (n=339).

As 27 fixtures do monitor foram pontuadas apenas de forma qualitativa (QUALITATIVO: 27 casos não são amostra estatística e não geram métrica.).

## E — Destaque de trechos (F1 por token)

| Método | OLID-BR teste (P / R / F1) | HateBRXplain (P / R / F1) |
|---|---|---|
| B_coeficientes_tfidf | 0.263 / 0.513 / 0.348 | 0.579 / 0.373 / 0.454 |
| A_lexico | 0.956 / 0.135 / 0.236 | 0.995 / 0.032 / 0.062 |
| tudo | 0.168 / 1.000 / 0.288 | 0.534 / 1.000 / 0.696 |
| aleatorio_prob_0.3 | 0.172 / 0.305 / 0.220 | 0.531 / 0.298 / 0.382 |

Exclusões: 350 amostras do OLID-BR com offsets fora do texto; 483 ofensivas sem span.

## Baseline C (transformer)

**Não executado.** `torch`/`transformers` não fazem parte do ambiente reprodutível; plano em `classifiers/transformer.py`.
