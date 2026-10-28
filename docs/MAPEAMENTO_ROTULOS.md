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
