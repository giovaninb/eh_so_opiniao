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

# Catálogo ampliado: MultiDomainYT-ToxBR, RacismoBR e recursos complementares

Protocolos `AMP-A` a `AMP-G` de `evaluation/experiments_ampliados.py`. Resultados separados por dataset e por classe; nenhum dataset é fundido; cada classe é um classificador binário independente; limiar escolhido na validação; média ± desvio entre as sementes 13, 42 e 2026. Suporte < 30 positivos no teste ⇒ não interpretar P/R/F1.

> O F1 binário do MultiDomainYT-ToxBR (0,78 no artigo) mede “tóxico ou não” e **não** indica capacidade de identificar categorias específicas.

## Concordância entre anotadores (MultiDomainYT-ToxBR, recalculada das planilhas)

| Classe | κ grupo 1 | κ grupo 2 | κ artigo g1 | κ artigo g2 | Positivos por maioria (g1 + g2) |
|---|---|---|---|---|---|
| `insulto_de_baixo_calao` | 0.481 | 0.262 | 0.481 | 0.262 | 926 |
| `homofobia` | 0.734 | 0.442 | 0.734 | 0.442 | 153 |
| `racismo` | 0.422 | 0.332 | 0.422 | 0.332 | 17 |
| `misoginia_machismo` | 0.532 | 0.407 | 0.532 | 0.407 | 95 |
| `xenofobia` | 0.329 | 0.420 | 0.329 | 0.420 | 59 |
| `violencia_extremismo` | 0.364 | 0.215 | 0.364 | 0.215 | 57 |
| `intolerancia_religiosa` | 0.549 | 0.555 | 0.549 | 0.555 | 76 |
| `intolerancia_politica` | 0.584 | 0.499 | 0.584 | 0.499 | 253 |
| `anticapacitismo` | 0.443 | 0.218 | 0.443 | 0.218 | 32 |

Classes com kappa baixo (racismo, xenofobia, violência, anticapacitismo no grupo 2) têm rótulo de consenso ruidoso: métricas de modelo nelas medem também o desacordo humano. A coluna 'inválido' não é usada como rótulo.

## Sobreposição entre corpora

Método: chave de quase-duplicata (textnorm.hash_chave: sem caixa, pontuação, URL, menção, 'RT'); só contagens. Tabela completa em `docs/COMPATIBILIDADE_DATASETS.md`. TuPyE contém ToLD-Br e HateBR por construção; não treinar nele para avaliar nesses corpora. Entre ToLD-Br, HateBR e MultiDomainYT-ToxBR a sobreposição de textos é a que consta em `pares`; textos em comum são removidos da avaliação cruzada.

## AMP-A — RacismoBR (classificadores binários de racismo)

Status: **pendente_fonte**. Não há URL oficial nova verificada. Próximos passos legítimos: pedir aos autores (contato publicado no artigo, UFMG/DCC) o acesso pelo protocolo de divulgação responsável, ou aguardar o repositório voltar. Enquanto isso o dataset fica pendente_fonte e nenhum resultado real é reportado. Protocolo implementado e testado só com fixtures sintéticas. Nenhum número real existe até o dataset ter fonte verificável.

## AMP-B — Generalização entre datasets

Linhas: treino. Cada célula é UM par treino → teste para UM rótulo, F1 da classe positiva (limiar da validação do treino). Em domínio = split de teste; fora de domínio = dataset inteiro sem textos vistos no treino. Positivos entre colchetes (por semente).

### Rótulo `racismo`

Indisponíveis: racismobr (pendente_fonte). Definições: racismobr: `racist` (aproximado); told_br: `racism` (equivalente); multidomain_yt_toxbr: `racismo` (aproximado)

| Treino → Teste | Domínio | F1 | Revocação | Precisão | AP | Prevalência | Positivos | Aviso |
|---|---|---|---|---|---|---|---|---|
| told_br->told_br | em | 0.086 ± 0.057 | 0.413 ± 0.214 | 0.083 ± 0.083 | 0.128 ± 0.072 | 0.002 ± 0.000 | [7, 7, 6] | suporte insuficiente |
| told_br->multidomain_yt_toxbr | fora | 0.087 ± 0.013 | 0.392 ± 0.246 | 0.087 ± 0.057 | 0.103 ± 0.003 | 0.003 ± 0.000 | [17, 17, 17] | suporte insuficiente |
| multidomain_yt_toxbr->told_br | fora | 0.019 ± 0.013 | 0.414 ± 0.225 | 0.010 ± 0.007 | 0.017 ± 0.005 | 0.002 ± 0.000 | [33, 33, 33] |  |
| multidomain_yt_toxbr->multidomain_yt_toxbr | em | 0.047 ± 0.056 | 0.667 ± 0.471 | 0.025 ± 0.030 | 0.264 ± 0.069 | 0.002 ± 0.002 | [3, 1, 0] | suporte insuficiente |

### Rótulo `linguagem_ofensiva`

Indisponíveis: nenhum. Definições: told_br: `toxico_qualquer_categoria` (aproximado); hatebr: `offensive_label` (aproximado); multidomain_yt_toxbr: `toxico_qualquer_categoria` (aproximado)

| Treino → Teste | Domínio | F1 | Revocação | Precisão | AP | Prevalência | Positivos | Aviso |
|---|---|---|---|---|---|---|---|---|
| told_br->told_br | em | 0.552 ± 0.007 | 0.582 ± 0.057 | 0.531 ± 0.033 | 0.567 ± 0.005 | 0.195 ± 0.003 | [628, 604, 614] |  |
| told_br->hatebr | fora | 0.414 ± 0.067 | 0.269 ± 0.059 | 0.944 ± 0.017 | 0.825 ± 0.005 | 0.500 ± 0.000 | [3498, 3498, 3498] |  |
| told_br->multidomain_yt_toxbr | fora | 0.430 ± 0.044 | 0.333 ± 0.068 | 0.632 ± 0.040 | 0.570 ± 0.003 | 0.291 ± 0.000 | [1454, 1454, 1454] |  |
| hatebr->told_br | fora | 0.380 ± 0.003 | 0.836 ± 0.018 | 0.246 ± 0.003 | 0.362 ± 0.001 | 0.194 ± 0.000 | [4063, 4063, 4063] |  |
| hatebr->hatebr | em | 0.875 ± 0.019 | 0.883 ± 0.019 | 0.870 ± 0.050 | 0.952 ± 0.017 | 0.539 ± 0.069 | [467, 627, 614] |  |
| hatebr->multidomain_yt_toxbr | fora | 0.526 ± 0.002 | 0.894 ± 0.011 | 0.373 ± 0.004 | 0.520 ± 0.001 | 0.291 ± 0.000 | [1453, 1453, 1453] |  |
| multidomain_yt_toxbr->told_br | fora | 0.391 ± 0.014 | 0.473 ± 0.050 | 0.336 ± 0.006 | 0.335 ± 0.004 | 0.194 ± 0.000 | [4061, 4061, 4061] |  |
| multidomain_yt_toxbr->hatebr | fora | 0.528 ± 0.040 | 0.376 ± 0.044 | 0.893 ± 0.015 | 0.810 ± 0.004 | 0.500 ± 0.000 | [3500, 3499, 3499] |  |
| multidomain_yt_toxbr->multidomain_yt_toxbr | em | 0.635 ± 0.014 | 0.644 ± 0.034 | 0.632 ± 0.058 | 0.679 ± 0.038 | 0.285 ± 0.013 | [215, 225, 201] |  |

## AMP-C — Racismo explícito × implícito

Status: **aguardando_anotacao_humana**. são necessários >= 20 itens 'explicito' e >= 20 'implicito' anotados por pessoas; há {'explicito': 0, 'implicito': 0, 'indeterminado': 0} Nenhum dataset integrado traz essa distinção e ela não é inferida por regra.

## AMP-D — Xenofobia e discriminação regional

| Treino → Teste | F1 | Revocação | Precisão | AP | Prevalência | Positivos | Aviso |
|---|---|---|---|---|---|---|---|
| told_br->told_br | 0.158 ± 0.123 | 0.209 ± 0.175 | 0.128 ± 0.096 | 0.140 ± 0.040 | 0.003 ± 0.000 | [7, 10, 8] | suporte insuficiente |
| told_br->multidomain_yt_toxbr | 0.021 ± 0.015 | 0.011 ± 0.008 | 0.148 ± 0.139 | 0.019 ± 0.003 | 0.012 ± 0.000 | [59, 59, 59] |  |
| multidomain_yt_toxbr->told_br | 0.024 ± 0.017 | 0.016 ± 0.011 | 0.054 ± 0.045 | 0.008 ± 0.005 | 0.002 ± 0.000 | [42, 42, 42] |  |
| multidomain_yt_toxbr->multidomain_yt_toxbr | 0.322 ± 0.109 | 0.386 ± 0.096 | 0.281 ± 0.116 | 0.363 ± 0.102 | 0.013 ± 0.002 | [11, 11, 8] | suporte insuficiente |

Composição dos positivos de xenofobia (marcadores lexicais simples; diagnóstico, não rótulo):

| Dataset | Positivos | Marcador regional | Marcador de nacionalidade | Sem marcador |
|---|---|---|---|---|
| told_br | 42 | 26 | 2 | 14 |
| multidomain_yt_toxbr | 59 | 3 | 29 | 27 |

Nenhum dataset integrado distingue xenofobia regional da nacional por comentário; nada aqui mede discriminação regional.

## AMP-E — Falsos positivos em comentários políticos não tóxicos

'Comentário político não tóxico' = contém termo político (lista de E/D) E foi rotulado como NÃO ofensivo pelos anotadores do próprio corpus. É um proxy: não é uma revisão humana específica de 'crítica legítima'.

| Modelo → Corpus | Domínio | Taxa de FP (político não tóxico) | Taxa de FP (demais negativos) | n político por semente | IC95% Wilson (semente 42) |
|---|---|---|---|---|---|
| told_br:linguagem_ofensiva → told_br | em | 0.110 ± 0.025 | 0.128 ± 0.030 | [84, 78, 90] | [0.0529, 0.1895] |
| told_br:linguagem_ofensiva → hatebr | fora | 0.032 ± 0.018 | 0.012 ± 0.007 | [861, 861, 861] | [0.0088, 0.0257] |
| told_br:linguagem_ofensiva → multidomain_yt_toxbr | fora | 0.149 ± 0.056 | 0.076 ± 0.030 | [373, 373, 373] | [0.0751, 0.1367] |
| hatebr:linguagem_ofensiva → told_br | fora | 0.667 ± 0.018 | 0.613 ± 0.024 | [560, 560, 560] | [0.6023, 0.6814] |
| hatebr:linguagem_ofensiva → hatebr | em | 0.128 ± 0.035 | 0.152 ± 0.025 | [144, 90, 102] | [0.0696, 0.2057] |
| hatebr:linguagem_ofensiva → multidomain_yt_toxbr | fora | 0.718 ± 0.013 | 0.605 ± 0.018 | [373, 373, 373] | [0.6514, 0.744] |
| multidomain_yt_toxbr:linguagem_ofensiva → told_br | fora | 0.232 ± 0.037 | 0.225 ± 0.029 | [560, 560, 560] | [0.2159, 0.2875] |
| multidomain_yt_toxbr:linguagem_ofensiva → hatebr | fora | 0.083 ± 0.018 | 0.034 ± 0.011 | [861, 861, 861] | [0.0555, 0.09] |
| multidomain_yt_toxbr:linguagem_ofensiva → multidomain_yt_toxbr | em | 0.308 ± 0.065 | 0.135 ± 0.035 | [50, 53, 60] | [0.1644, 0.3958] |
| multidomain_yt_toxbr:hostilidade_politica → told_br | fora | 0.114 ± 0.058 | 0.002 ± 0.002 | [560, 560, 560] | [0.0668, 0.1138] |
| multidomain_yt_toxbr:hostilidade_politica → hatebr | fora | 0.122 ± 0.069 | 0.002 ± 0.003 | [861, 861, 861] | [0.0607, 0.0964] |
| multidomain_yt_toxbr:hostilidade_politica → multidomain_yt_toxbr | em | 0.181 ± 0.056 | 0.004 ± 0.003 | [50, 53, 60] | [0.0785, 0.2705] |

## AMP-F — Trechos humanos × trechos destacados por modelos (HateBRXplain)

Teste: 626 comentários ofensivos com trecho (615 com os dois anotadores). Teto humano (anotador 1 × 2, por token): P 0.880 · R 0.690 · F1 0.774 · κ 0.5367.

| Método | F1 vs união | F1 vs anotador 1 | F1 vs anotador 2 | R-precisão (ranking) | AP por token |
|---|---|---|---|---|---|
| coeficientes_tfidf | 0.773 | 0.733 | 0.630 | 0.806 ± 0.258 | 0.729 |
| oclusao_do_modelo_completo | 0.755 | 0.718 | 0.613 | 0.823 ± 0.232 | 0.762 |
| tudo | 0.776 | 0.736 | 0.625 | — | — |
| aleatorio_prob_0.3 | 0.401 | 0.393 | 0.350 | 0.759 ± 0.305 | 0.636 |

Densidade de tokens humanos: 0.634 (o acaso acerta cerca disso). O acaso acerta cerca da densidade; o teto humano é o F1/kappa entre anotadores. Quando 'tudo' empata com os métodos, o F1 por limiar não discrimina e vale o ranking.

Sensibilidade do modelo à remoção (538 comentários ofensivos do teste marcados pelo modelo): remover trechos humanos derruba a pontuação em 0.328 (deixa de marcar 74.9%); remover o mesmo número de tokens aleatórios, -0.005. Mede o quanto a pontuação do MODELO depende dos trechos; não prova que os trechos causam a decisão nem que o modelo 'entende' a ofensa.

## AMP-G — MultiDomainYT-ToxBR por classe, concordância e poucos exemplos

Um classificador binário por classe (um contra todos), teste do próprio dataset. Portão `validada`: ≥ 30 positivos no teste em todas as sementes **e** AP ≥ 2× a prevalência.

| Classe | Precisão | Revocação | F1 | AP | Positivos no teste | Validada |
|---|---|---|---|---|---|---|
| `linguagem_ofensiva` | 0.632 ± 0.058 | 0.644 ± 0.034 | 0.635 ± 0.014 | 0.679 ± 0.038 | [215, 225, 201] | sim |
| `insulto_hostilidade` | 0.516 ± 0.022 | 0.679 ± 0.032 | 0.586 ± 0.022 | 0.617 ± 0.050 | [136, 137, 130] | sim |
| `lgbtfobia` | 0.339 ± 0.075 | 0.509 ± 0.242 | 0.371 ± 0.123 | 0.442 ± 0.082 | [18, 24, 13] | não |
| `racismo` | 0.025 ± 0.030 | 0.667 ± 0.471 | 0.047 ± 0.056 | 0.264 ± 0.069 | [3, 1, 0] | não |
| `misoginia` | 0.266 ± 0.009 | 0.626 ± 0.226 | 0.358 ± 0.046 | 0.326 ± 0.077 | [12, 16, 15] | não |
| `xenofobia` | 0.281 ± 0.116 | 0.386 ± 0.096 | 0.322 ± 0.109 | 0.363 ± 0.102 | [11, 11, 8] | não |
| `incitacao_violencia` | 0.245 ± 0.204 | 0.169 ± 0.150 | 0.169 ± 0.122 | 0.227 ± 0.097 | [11, 7, 7] | não |
| `intolerancia_religiosa` | 0.236 ± 0.086 | 0.335 ± 0.157 | 0.254 ± 0.073 | 0.320 ± 0.156 | [10, 12, 9] | não |
| `hostilidade_politica` | 0.558 ± 0.023 | 0.566 ± 0.135 | 0.551 ± 0.058 | 0.542 ± 0.007 | [41, 37, 45] | sim |
| `capacitismo` | 1.000 ± 0.000 | 0.500 ± 0.245 | 0.630 ± 0.228 | 0.676 ± 0.163 | [5, 4, 5] | não |

Classes validadas: `linguagem_ofensiva`, `insulto_hostilidade`, `hostilidade_politica`. As demais **não devem ser usadas** como classificador.

Desempenho do classificador binário por nível de acordo e por grupo de anotadores:

| Estrato | AUC-ROC | Revocação | Taxa de FP | Positivos por semente |
|---|---|---|---|---|
| unanimes_em_todas_as_classes | 0.910 ± 0.008 | 0.732 ± 0.059 | 0.084 ± 0.029 | [43, 53, 43] |
| com_voto_dividido_em_alguma_classe | 0.700 ± 0.013 | 0.619 ± 0.028 | 0.314 ± 0.066 | [172, 172, 158] |
| grupo_1 | 0.821 ± 0.003 | 0.598 ± 0.049 | 0.145 ± 0.054 | [112, 123, 101] |
| grupo_2 | 0.848 ± 0.021 | 0.695 ± 0.018 | 0.158 ± 0.026 | [103, 102, 100] |

F1 e precisão dependem da prevalência de cada estrato (itens unânimes são quase todos negativos), então NÃO são comparáveis entre estratos; use a AUC-ROC, a revocação e a taxa de falso positivo, e leia o n de positivos de cada estrato. Os estratos não têm o mesmo tamanho nem a mesma composição. Correlação de Spearman entre κ médio e F1 por classe: -0.05 (n = 9 classes: descritiva, não inferencial; classes raras confundem raridade com desacordo.)

Curva de aprendizado (F1 no teste × positivos no treino):

| Classe | 10 | 25 | 50 | 100 | 200 | todos |
| `insulto_hostilidade` | 0.326 ± 0.032 | 0.372 ± 0.017 | 0.408 ± 0.033 | 0.481 ± 0.033 | 0.521 ± 0.035 | 0.586 ± 0.022 |
| `hostilidade_politica` | 0.251 ± 0.091 | 0.438 ± 0.033 | 0.499 ± 0.068 | 0.508 ± 0.097 | 0.551 ± 0.058 |

