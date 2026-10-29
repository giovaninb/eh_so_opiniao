<!-- GERADO AUTOMATICAMENTE por `python -m eh_so_opiniao docs`. Não edite à mão. -->

# Mapeamento de rótulos (versão 1.2.0)

Cada linha liga um rótulo ORIGINAL de um dataset a uma classe da taxonomia (v1.2.0). Fonte única: `datasets/label_mapping.yaml`.

- **equivalente**: definição e escopo coincidem.
- **aproximado**: há sobreposição, mas escopo, definição ou domínio diferem; nunca é tratado como equivalente em experimentos.
- **incompativel**: sem classe correspondente na taxonomia v1; o rótulo fica só em `original_labels`.

Datasets NÃO são fundidos: cada amostra carrega apenas rótulos do próprio dataset; valores ausentes são permitidos.

| Dataset | Rótulo original | Rótulo da taxonomia | Relação | Observação |
|---|---|---|---|---|
| told_br | `homophobia` | lgbtfobia | aproximado | Votos 0-3 por categoria; a fonte descreve LGBTQ+fobia, sem distinguir orientação de identidade de gênero. |
| told_br | `obscene` | — (fora da taxonomia v1) | incompativel | Obscenidade não é ofensa dirigida; sem classe própria na taxonomia v1. Contribui apenas ao rótulo derivado toxico_qualquer_categoria. |
| told_br | `insult` | insulto_hostilidade | aproximado | Insulto em tweets; sem distinção entre alvo individual e coletivo. |
| told_br | `racism` | racismo | equivalente | Mesma definição de preconceito racial/étnico. |
| told_br | `misogyny` | misoginia | equivalente | Anotação específica de misoginia. |
| told_br | `xenophobia` | xenofobia | aproximado | Classe rara; não distingue origem nacional de regional. |
| told_br | `toxico_qualquer_categoria` | linguagem_ofensiva | aproximado | Derivado por política de consenso (ver adaptador); ToLD-Br não tem rótulo binário próprio na versão multirrótulo. |
| hatebr | `offensive_label` | linguagem_ofensiva | aproximado | HateBR 2.0/HateBRXplain é binário (ofensivo/não); comentários do Instagram dirigidos a políticos. |
| hatebr | `hate_speech` | — (fora da taxonomia v1) | incompativel | Camadas de discurso de ódio, nível de ofensa e alvos existem só na versão 1.0, sob pedido; indisponíveis aqui. |
| multidomain_yt_toxbr | `insulto_de_baixo_calao` | insulto_hostilidade | aproximado | Agressão verbal sem conotação discriminatória nem identidade social específica (palavrões, xingamentos); inclui ataque à aparência, inteligência ou caráter. |
| multidomain_yt_toxbr | `homofobia` | lgbtfobia | aproximado | Orientação sexual ou identidade de gênero; inclui estereótipos e piadas ofensivas. |
| multidomain_yt_toxbr | `racismo` | racismo | aproximado | Guia inclui "pejorativos ou estereotipados" e exemplos de escopo largo; apenas 17 positivos por consenso e concordância baixa (kappa 0,33-0,42). Não tratar como equivalente ao racismo do ToLD-Br. |
| multidomain_yt_toxbr | `misoginia_machismo` | misoginia | aproximado | Ódio, desprezo ou inferiorização da mulher por ser mulher; inclui "machismo", mais amplo que misoginia estrita. |
| multidomain_yt_toxbr | `xenofobia` | xenofobia | aproximado | Inclui origem geográfica, nacionalidade, etnia e REGIÃO (migrantes internos, como nordestinos e sulistas). Não distingue xenofobia nacional de preconceito regional por comentário. |
| multidomain_yt_toxbr | `violencia_extremismo` | incitacao_violencia | aproximado | Mais amplo que incitação: inclui defender, minimizar ou justificar violência e discursos autoritários de eliminação do "inimigo". 57 positivos; instável. |
| multidomain_yt_toxbr | `intolerancia_religiosa` | intolerancia_religiosa | aproximado | Ataque, zombaria ou desvalorização com base em crença ou religião; classe criada na taxonomia 1.1.0 a partir desta fonte (sem segundo dataset para validar equivalência). |
| multidomain_yt_toxbr | `intolerancia_politica` | hostilidade_politica | aproximado | Ataque, deslegitimação ou desumanização por orientação política ou filiação partidária, em comentários do YouTube; não é detector de preferência política. |
| multidomain_yt_toxbr | `anticapacitismo` | capacitismo | aproximado | Apesar do nome, mede a PRESENÇA de conteúdo capacitista (zombaria ou desumanização de pessoas com deficiência), conforme o guia de anotação. |
| multidomain_yt_toxbr | `invalido` | — (fora da taxonomia v1) | incompativel | Marca de comentário inválido por anotador (ignorada pelos autores na consolidação); preservada só como metadado de anotação. |
| multidomain_yt_toxbr | `toxico_qualquer_categoria` | linguagem_ofensiva | aproximado | Rótulo binário do corpus = 1 se qualquer das nove categorias tem consenso (>=2 de 3). Inclui insulto de baixo calão; "tóxico" aqui não é sinônimo de discurso de ódio. O F1 binário não indica capacidade de identificar categorias. |
| racismobr | `racist` | racismo | aproximado | Racismo contra pessoas negras, conforme a definição operacional dos autores (adaptada de Almeida, 2019), anotado por pesquisadores negros. Escopo mais estreito que a classe "racismo" da taxonomia (raça, cor ou etnia). Sem dados: mapeamento validado só com fixtures sintéticas. |
| tupye | `aggressive` | linguagem_ofensiva | aproximado | Agressividade agregada de três fontes por voto de maioria; definições herdadas de ToLD-Br, HateBR e Fortuna et al. |
| tupye | `hate` | — (fora da taxonomia v1) | incompativel | Ódio definido pelos autores EXCLUINDO textos só ofensivos ou obscenos; não coincide com nenhuma classe da taxonomia nem com o rótulo de ofensa do HateBR e do ToLD-Br. Rótulos específicos (multirrótulo) não foram baixados. |
