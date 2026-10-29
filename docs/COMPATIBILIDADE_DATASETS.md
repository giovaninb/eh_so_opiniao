<!-- GERADO AUTOMATICAMENTE por `python -m eh_so_opiniao docs`. Não edite à mão. -->

# Compatibilidade entre datasets

Como os datasets se comparam e por que NÃO são fundidos. Fontes: `datasets/registry.yaml`, `datasets/label_mapping.yaml`, `relatorios/sobreposicao_corpora.json`.

## Plataforma, domínio, anotação e licença

| Dataset | Plataforma | Idioma | Licença | Redistribuição | Integração |
|---|---|---|---|---|---|
| ToLD-Br — Toxic Language Detection for Brazilian Portuguese | twitter | pt-BR | CC-BY-SA-4.0 | Permitida com atribuição e mesma licença | integrado |
| HateBR 2.0 e HateBRXplain | instagram | pt-BR | CC-BY-NC-4.0 | Somente uso não comercial, com atribuição | integrado |
| MultiDomainYT-ToxBR — corpus multidomínio de comentários tóxicos do YouTube (PUCRS, 2026) | youtube | pt-BR | não declarada (condições registradas) | Não | integrado |
| RacismoBR — discurso racista em português do Brasil (UFMG, 2026) | twitter | pt-BR | não declarada (condições registradas) | Não | pendente_fonte |
| TuPyE — Expanded Brazilian Hate Speech Dataset (somente análise de sobreposição) | twitter e instagram | pt-BR | não declarada (condições registradas) | Não | somente_sobreposicao |

- **told_br** · domínio/contexto: Tweets gerais; não é corpus político. · anotação e consenso: 3 anotadores por tweet; 6 categorias com contagem de votos 0-3 (float no CSV).
- **hatebr** · domínio/contexto: Comentários em publicações de políticos brasileiros (78 publicações no arquivo). O nome da conta do político NÃO é carregado para as amostras normalizadas. · anotação e consenso: Binário (ofensivo/não) com 3 anotadores especialistas; HateBRXplain acrescenta justificativas (rationales) de 2 anotadores como trechos de texto. Níveis de ofensa e alvos de ódio existem só na versão 1.0, sob pedido, NÃO integrados.
- **multidomain_yt_toxbr** · domínio/contexto: Comentários de 50 vídeos (2 por termo de busca, 25 termos) em cinco domínios temáticos: política polarizada, futebol, conflitos internacionais, feminismo e direitos das mulheres, conteúdo LGBTQIA+. O domínio e o vídeo de cada comentário NÃO constam nos arquivos publicados (as planilhas foram embaralhadas e só a coluna do comentário foi mantida). · anotação e consenso: Cada comentário tem 3 anotadores (dois grupos independentes de três: grupo 1 anotou os 2.500 primeiros, grupo 2 os 2.500 restantes). Nove categorias binárias por anotador, mais a coluna 'inválido'. O vetor do CSV é o consenso por maioria (>=2 de 3) em cada categoria; o rótulo binário é 1 se qualquer categoria tem consenso.
- **racismobr** · domínio/contexto: Posts do X (antigo Twitter): 405 coletados entre setembro/2024 e janeiro/2025 por palavras-chave, mais 629 posts de trabalhos anteriores (2017-2021) reanotados. · anotação e consenso: Binário: 1 = racista, 0 = não racista (racismo contra pessoas negras). Pares independentes de pesquisadores negros; terceiro avaliador nos casos de divergência.
- **tupye** · domínio/contexto: Composição por pesquisador: Leite et al. (ToLD-Br) 21.000, TuPy 10.000, Vargas et al. (HateBR) 7.000, Fortuna et al. 5.668. Por construção, 28.000 dos 43.668 documentos (64%) vêm do ToLD-Br e do HateBR. · anotação e consenso: Binário agressivo/ódio (colunas aggressive e hate) agregando três fontes por voto de maioria. 'hate' EXCLUI textos que só são ofensivos ou obscenos: definição de ódio diferente da do ToLD-Br e da do HateBR. A versão multirrótulo (13 colunas) não foi usada.

## Classes da taxonomia por dataset (relação declarada, rótulo original)

`equivalente`: mesma definição e escopo. `aproximado`: sobreposição, mas definição, escopo ou domínio diferem; nunca é tratado como equivalente. `—`: o dataset não tem rótulo para a classe. A coluna de cada dataset mostra `relação (rótulo original)`.

| Classe | told_br | hatebr | multidomain_yt_toxbr | racismobr | tupye |
|---|---|---|---|---|---|
| `linguagem_ofensiva` (supervisionado) | aproximado (`toxico_qualquer_categoria`) | aproximado (`offensive_label`) | aproximado (`toxico_qualquer_categoria`) | — | aproximado (`aggressive`) |
| `insulto_hostilidade` (supervisionado) | aproximado (`insult`) | — | aproximado (`insulto_de_baixo_calao`) | — | — |
| `racismo` (supervisionado) | equivalente (`racism`) | — | aproximado (`racismo`) | aproximado (`racist`) | — |
| `xenofobia` (supervisionado) | aproximado (`xenophobia`) | — | aproximado (`xenofobia`) | — | — |
| `misoginia` (supervisionado) | equivalente (`misogyny`) | — | aproximado (`misoginia_machismo`) | — | — |
| `intolerancia_religiosa` (supervisionado) | — | — | aproximado (`intolerancia_religiosa`) | — | — |
| `capacitismo` (supervisionado) | — | — | aproximado (`anticapacitismo`) | — | — |
| `lgbtfobia` (supervisionado) | aproximado (`homophobia`) | — | aproximado (`homofobia`) | — | — |
| `hostilidade_politica` (supervisionado) | — | — | aproximado (`intolerancia_politica`) | — | — |
| `incitacao_violencia` (supervisionado) | — | — | aproximado (`violencia_extremismo`) | — | — |

Classes sem rótulo anotado em nenhum dataset (exploratórias ou salvaguardas): `transfobia`, `idadismo`, `estereotipos_masculinidade`, `estigma_nao_monogamia`, `discriminacao_regional`, `desumanizacao`, `exclusao_social_territorial`, `estigmatizacao_socioeconomica`, `possivel_assedio_eleitoral_contextual`, `critica_politica_legitima`, `ironia_humor`, `ambigua`.

## Sobreposição de textos

Método: chave de quase-duplicata (textnorm.hash_chave: sem caixa, pontuação, URL, menção, 'RT'); só contagens.

| Par | Textos em comum | % do primeiro | % do segundo |
|---|---|---|---|
| hatebr × multidomain_yt_toxbr | 5 | 0.1% | 0.1% |
| hatebr × told_br | 4 | 0.1% | 0.0% |
| hatebr × tupye | 5220 | 74.6% | 12.4% |
| multidomain_yt_toxbr × told_br | 9 | 0.2% | 0.0% |
| multidomain_yt_toxbr × tupye | 23 | 0.5% | 0.1% |
| told_br × tupye | 20561 | 100.0% | 48.7% |

TuPyE contém ToLD-Br e HateBR por construção; não treinar nele para avaliar nesses corpora. Entre ToLD-Br, HateBR e MultiDomainYT-ToxBR a sobreposição de textos é a que consta em `pares`; textos em comum são removidos da avaliação cruzada.

**RacismoBR**: Parte dos 629 posts da literatura vem de Fortuna et al. (2019) e de Leite et al. (2020, ToLD-Br), logo há sobreposição esperada com ToLD-Br e TuPyE. NÃO MEDIDA: sem arquivo. Medir antes de qualquer avaliação cruzada.

## Consequências para os experimentos

- Nenhum dataset é fundido; cada rótulo vem do próprio dataset e carrega a relação declarada.
- Avaliação entre datasets remove textos vistos no treino e sempre separa os resultados por par treino × teste.
- Diferenças de desempenho fora de domínio misturam definição de classe, plataforma, época e anotadores; não são só erro de modelo.
- A TuPyE reúne ToLD-Br e HateBR, então não serve para avaliar generalização entre eles.
