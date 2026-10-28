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

### B — transferência HateBR → ToLD-Br (sem textos em comum)

| Método | Precision | Recall | F1 (positiva) | Macro-F1 (2 classes) |
|---|---|---|---|---|
| Chute: sempre ofensivo | 0.194 ± 0.000 | 1.000 ± 0.000 | 0.324 ± 0.000 | 0.162 ± 0.000 |
| A — léxico | 0.292 ± 0.000 | 0.500 ± 0.000 | 0.369 ± 0.000 | 0.572 ± 0.000 |
| B — TF-IDF+LR | 0.246 ± 0.003 | 0.836 ± 0.018 | 0.380 ± 0.003 | 0.460 ± 0.012 |

Prevalência de ofensivos no ToLD-Br (rótulo derivado por votos, só aproximado ao do HateBR): 0.194. **Atenção:** o F1 da classe positiva pode favorecer o chute 'sempre ofensivo' quando a prevalência é alta; o macro-F1 (média das duas classes) é a leitura mais honesta. Calibração (HateBR, semente 42): Brier 0.1144, ECE 0.1378.

## A — ToLD-Br, classes de grupo (em domínio)

F1 (média ± desvio) no teste do ToLD-Br. Suporte = positivos no teste por semente. **Suporte baixo ⇒ não interpretar.** Não há segundo dataset aprovado com estas classes, então não existe avaliação fora de domínio.

| Classe | Relação (ToLD) | F1 em domínio | Positivos no teste |
|---|---|---|---|
| insulto_hostilidade | aproximado | 0.520 ± 0.018 | [296, 279, 289] |
| lgbtfobia | aproximado | 0.542 ± 0.019 | [18, 24, 22] |
| misoginia | equivalente | 0.321 ± 0.177 | [20, 19, 26] |
| racismo | equivalente | 0.086 ± 0.057 | [7, 7, 6] |
| xenofobia | aproximado | 0.158 ± 0.123 | [7, 10, 8] |

## C — Combinar bases (F1, limiar da validação)

Linhas: treino. Colunas: teste.

| Treino \ Teste | hatebr | told_br |
|---|---|---|
| hatebr | 0.875 ± 0.019 * | 0.383 ± 0.006 |
| told_br | 0.424 ± 0.066 | 0.552 ± 0.007 * |
| hatebr+told_br | 0.839 ± 0.014 * | 0.553 ± 0.003 * |

`*` = base de teste presente no treino (em domínio).

| Teste | Referência | Combinado | F1 ref. | F1 comb. | Δ |
|---|---|---|---|---|---|
| hatebr | hatebr | hatebr+told_br | 0.875 | 0.839 | -0.036 |
| told_br | told_br | hatebr+told_br | 0.552 | 0.553 | +0.001 |

## D — Neutralidade partidária (contrafactual) e falsos positivos

Troca espelhada de termos (Lula↔Bolsonaro, petista↔bolsonarista, esquerda↔direita, PT↔PL) nos mesmos textos. Δ = pontuação após troca − antes. IC95% por bootstrap.

| Modelo | Grupo | Direção | n | Δ médio | IC95% | Decisões que mudam |
|---|---|---|---|---|---|---|
| hatebr | nao_ofensivos | esquerda_para_direita | 39 | -0.082 | [-0.126, -0.046] | 25.6% |
| hatebr | nao_ofensivos | direita_para_esquerda | 32 | +0.011 | [+0.004, +0.022] | 0.0% |
| hatebr | ofensivos | esquerda_para_direita | 99 | -0.114 | [-0.130, -0.099] | 20.2% |
| hatebr | ofensivos | direita_para_esquerda | 36 | +0.045 | [+0.022, +0.074] | 5.6% |
| hatebr+told_br | nao_ofensivos | esquerda_para_direita | 67 | -0.106 | [-0.138, -0.075] | 19.4% |
| hatebr+told_br | nao_ofensivos | direita_para_esquerda | 75 | +0.027 | [+0.016, +0.039] | 6.7% |
| hatebr+told_br | ofensivos | esquerda_para_direita | 126 | -0.136 | [-0.154, -0.117] | 20.6% |
| hatebr+told_br | ofensivos | direita_para_esquerda | 50 | +0.049 | [+0.027, +0.075] | 8.0% |

Falsos positivos em comentários NÃO ofensivos do HateBR (teste, n=429): taxa geral 0.121. Com termo político: 0.1222 (n=90); sem: 0.1209 (n=339).

As 27 fixtures do monitor foram pontuadas apenas de forma qualitativa (QUALITATIVO: 27 casos não são amostra estatística e não geram métrica.).

## E — Destaque de trechos (F1 por token)

Treino e teste no HateBR; trechos derivados das justificativas do HateBRXplain (aproximação por busca textual).

| Método | HateBR teste (P / R / F1) |
|---|---|
| B_coeficientes_tfidf | 0.672 / 0.838 / 0.746 |
| A_lexico | 0.994 / 0.034 / 0.065 |
| tudo | 0.634 / 1.000 / 0.776 |
| aleatorio_prob_0.3 | 0.632 / 0.294 / 0.401 |

Exclusões: 2 comentários ofensivos sem trecho justificado (de 3500).

## Baseline C (transformer)

**Não executado.** `torch`/`transformers` não fazem parte do ambiente reprodutível; plano em `classifiers/transformer.py`.
