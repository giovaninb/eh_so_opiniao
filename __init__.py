"""É Só Opinião? — observatório de pesquisa e site educativo.

Subtítulo: "Onde termina a opinião e começa a discriminação?"
Exposição: "Quem Pode Pertencer?"

Este pacote integra corpora públicos brasileiros de linguagem ofensiva a um
pipeline reproduzível (Dataset → Adaptador → Validação → Normalização →
Mapeamento → Experimento → Avaliação → Revisão humana).

Princípios (ver docs/):
- não identifica pessoas nem infere preferência eleitoral;
- não trata probabilidade de modelo como evidência de crime;
- não publica resultados de IA sem aprovação humana;
- corpora brutos ficam fora do Git e do site.
"""

__version__ = "0.1.0"
SCHEMA_VERSION = "1.0.0"
