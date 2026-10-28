<!-- GERADO AUTOMATICAMENTE por `python -m eh_so_opiniao docs`. Não edite à mão. -->

# Mapeamento de rótulos (versão 1.0.0)

Cada linha liga um rótulo ORIGINAL de um dataset a uma classe da taxonomia (v1.0.0). Fonte única: `datasets/label_mapping.yaml`.

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
| olid_br | `is_offensive` | linguagem_ofensiva | aproximado | Rótulo com apoio da Perspective API e checagem por anotadores. |
| olid_br | `insult` | insulto_hostilidade | aproximado | Categoria de ofensa; não implica alvo. |
| olid_br | `profanity_obscene` | — (fora da taxonomia v1) | incompativel | Xingamento/obscenidade sem classe própria na taxonomia v1; já está coberto por is_offensive. Preservado em original_labels. |
| olid_br | `racism` | racismo | equivalente | Mesma definição. |
| olid_br | `sexism` | misoginia | aproximado | Sexismo é mais amplo que misoginia. |
| olid_br | `lgbtqphobia` | lgbtfobia | aproximado |  |
| olid_br | `xenophobia` | xenofobia | aproximado |  |
| olid_br | `ideology` | hostilidade_politica | aproximado | Ofensa por ideologia; não é detector de preferência política nem de assédio eleitoral. |
| olid_br | `religious_intolerance` | — (fora da taxonomia v1) | incompativel | Sem classe correspondente na taxonomia v1. |
| olid_br | `health` | — (fora da taxonomia v1) | incompativel | Sem classe correspondente na taxonomia v1. |
| olid_br | `physical_aspects` | — (fora da taxonomia v1) | incompativel | Sem classe correspondente na taxonomia v1. |
| olid_br | `other_lifestyle` | — (fora da taxonomia v1) | incompativel | Sem classe correspondente na taxonomia v1. |
| olid_br | `is_targeted` | — (fora da taxonomia v1) | incompativel | Metadado de alvo (TIN/UNT) preservado em annotation_metadata. |
| olid_br | `targeted_type` | — (fora da taxonomia v1) | incompativel | IND/GRP/OTH preservado em annotation_metadata. |
