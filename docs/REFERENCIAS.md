<!-- GERADO AUTOMATICAMENTE por `python -m eh_so_opiniao docs`. Não edite à mão. -->

# Referências científicas

Fonte: `datasets/registry.yaml` e `datasets/referencias.yaml`. A lista é a mesma que o site mostra na seção científica (`site/data/referencias.json`). Nenhum texto de corpus aparece aqui.

## Datasets catalogados

- **ToLD-Br — Toxic Language Detection for Brazilian Portuguese** — Leite et al. (2020). Toxic Language Detection in Social Media for Brazilian Portuguese: New Dataset and Multilingual Analysis. arXiv:2010.04543 (AACL-IJCNLP 2020). Fonte: https://github.com/JAugusto97/ToLD-Br · status: acessado
- **HateBR 2.0 e HateBRXplain** — Vargas et al. (2022) HateBR, LREC 2022, aclanthology 2022.lrec-1.777; Salles, Vargas & Benevenuto (2025) HateBRXplain, COLING 2025, aclanthology 2025.coling-main.446. Fonte: https://github.com/franciellevargas/HateBR · status: acessado
- **MultiDomainYT-ToxBR — corpus multidomínio de comentários tóxicos do YouTube (PUCRS, 2026)** — de Souza, G. Z., Manssour, I. H. (2026). MultiDomainYT-ToxBR: Um Corpus Multidomínio de Comentários Tóxicos do YouTube em Português Brasileiro. STIL 2026, aclanthology 2026.stil-1.36. Fonte: https://github.com/DAVINTLAB/MultiDomainYT-ToxBR · Artigo: https://aclanthology.org/2026.stil-1.36/ · status: acessado
- **RacismoBR — discurso racista em português do Brasil (UFMG, 2026)** — Vaz, J. V., Benevenuto, F., Gonçalves, M. A. (2026). RacismoBR: A Manually Annotated Dataset for Racist Discourse Detection in Brazilian Portuguese. PROPOR 2026, vol. 1, pp. 770-779. aclanthology 2026.propor-1.76. Fonte: https://github.com/joaovitorvaz/RacismoBR-Dataset · Artigo: https://aclanthology.org/2026.propor-1.76/ · status: pendente_fonte
- **TuPyE — Expanded Brazilian Hate Speech Dataset (somente análise de sobreposição)** — Oliveira et al. (2023). TuPy-E: detecting hate speech in Brazilian Portuguese social media with a novel dataset and comprehensive analysis of models. arXiv:2312.17704. Fonte: https://github.com/Silly-Machine/TuPyE-Expanded-Brazilian-Hate-Speech-Dataset · status: acessado

## Artigos dos datasets

### RacismoBR: A Manually Annotated Dataset for Racist Discourse Detection in Brazilian Portuguese

- Citação: Vaz, J. V., Benevenuto, F., Gonçalves, M. A. (2026). RacismoBR: A Manually Annotated Dataset for Racist Discourse Detection in Brazilian Portuguese. PROPOR 2026, 770-779.
- Veículo: PROPOR 2026, vol. 1, pp. 770-779 (ACL Anthology) · ano: 2026
- Endereço: https://aclanthology.org/2026.propor-1.76/
- Papel no projeto: Fonte da definição operacional, da composição e do método de anotação do RacismoBR. O dataset está pendente de fonte pública (ver registry.yaml); nenhum dado dele é usado.
- Direitos de uso: Artigo em acesso aberto na ACL Anthology (ver a licença indicada na página).
- O que NÃO é: Não é prova de que o dataset esteja acessível.

### MultiDomainYT-ToxBR: Um Corpus Multidomínio de Comentários Tóxicos do YouTube em Português Brasileiro

- Citação: de Souza, G. Z., Manssour, I. H. (2026). MultiDomainYT-ToxBR: Um Corpus Multidomínio de Comentários Tóxicos do YouTube em Português Brasileiro. STIL 2026.
- Veículo: STIL 2026 (ACL Anthology) · ano: 2026
- Endereço: https://aclanthology.org/2026.stil-1.36/
- Papel no projeto: Fonte da taxonomia de nove categorias, da concordância reportada e do desempenho de referência. O F1 binário de 0,78 NÃO mede a capacidade de identificar categorias; no multirrótulo o artigo reporta F1 médio de 0,11.
- Direitos de uso: Artigo em acesso aberto na ACL Anthology.
- O que NÃO é: Não declara licença do corpus; o artigo informa apenas uso acadêmico.


## Recursos de explicabilidade

### HateBRXplain: A Benchmark Dataset with Human-Annotated Rationales for Explainable Hate Speech Detection in Brazilian Portuguese

- Citação: Salles, I., Vargas, F., Benevenuto, F. (2025). HateBRXplain. In: Proceedings of COLING 2025. aclanthology 2025.coling-main.446.
- Veículo: COLING 2025 · ano: 2025
- Endereço: https://github.com/isadorasalles/HateBRXplain
- Papel no projeto: Justificativas humanas (trechos) para 3.500 comentários ofensivos do HateBR, já integradas pelo adaptador do HateBR. O repositório foi auditado: mesmos 7.000 comentários e mesmas justificativas do arquivo integrado (6.998 de 7.000 idênticas). Apoia o protocolo AMP-F (explicabilidade); pontuações de LIME/SHAP do repositório não são importadas.
- Direitos de uso: Repositório sem licença declarada; o projeto lê o arquivo do repositório HateBR (CC-BY-NC-4.0).
- O que NÃO é: Atenção, SHAP ou LIME não provam a causa da decisão de um modelo; trechos humanos são justificativas, não verdade absoluta.


## Datasets avaliados (só sobreposição)

### TuPy-E: detecting hate speech in Brazilian Portuguese social media with a novel dataset and comprehensive analysis of models

- Citação: Oliveira et al. (2023). TuPy-E. arXiv:2312.17704.
- Veículo: arXiv:2312.17704 · ano: 2023
- Endereço: https://github.com/Silly-Machine/TuPyE-Expanded-Brazilian-Hate-Speech-Dataset
- Papel no projeto: Avaliado só para sobreposição: reúne ToLD-Br, HateBR e Fortuna et al., por isso 64% dos documentos são do ToLD-Br e do HateBR. Seus rótulos não entram nos experimentos; evita-se treinar nele e testar nos corpora que ele contém.
- Direitos de uso: CC-BY-4.0 no cartão do Hugging Face, inconsistente com as licenças dos componentes (CC-BY-SA-4.0 e CC-BY-NC-4.0).
- O que NÃO é: Não é corpus independente dos outros.


## Referências teóricas (não são datasets)

### Escala de Preconceito contra Nordestinos: desenvolvimento e evidências de validade e confiabilidade

- Citação: de Souza, L. E. C., de Lima, T. J. S., de Paula, A. S., Pereira, C. R. (2025). Escala de Preconceito contra Nordestinos. Psico, 56(1), e47118. doi:10.15448/1980-8623.2025.1.47118.
- Veículo: Psico, v. 56, n. 1, e47118 (PUCRS) · ano: 2025
- Endereço: https://revistaseletronicas.pucrs.br/revistapsico/article/view/47118
- DOI: 10.15448/1980-8623.2025.1.47118
- Papel no projeto: Referência TEÓRICA para uma taxonomia de estereótipos regionais (três fatores: incompetência, inferioridade, sociabilidade; Modelo de Conteúdo de Estereótipos). Apoia a leitura da classe exploratória 'discriminação regional'.
- Direitos de uso: CC BY-NC-ND 4.0: os itens da escala não são reproduzidos nem adaptados aqui.
- O que NÃO é: NÃO é dataset de comentários nem fornece rótulos supervisionados; não gera métrica de classificador.

