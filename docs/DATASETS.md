<!-- GERADO AUTOMATICAMENTE por `python -m eh_so_opiniao docs`. Não edite à mão. -->

# Catálogo de datasets

Fonte: `datasets/registry.yaml`.

| Dataset | Licença | Acesso | Status | Registros confirmados | Plataforma |
|---|---|---|---|---|---|
| ToLD-Br — Toxic Language Detection for Brazilian Portuguese | CC-BY-SA-4.0 | aberto | acessado | 21000 | twitter |
| HateBR 2.0 e HateBRXplain | CC-BY-NC-4.0 | aberto | acessado | 7000 | instagram |

## ToLD-Br — Toxic Language Detection for Brazilian Portuguese (`told_br`)

- Versão/revisão: `main@6b325d26a9d25b321a3e9ba98ef98832b56729f5` · data: 2025-02-22
- Licença: CC-BY-SA-4.0
- Redistribuição: Permitida com atribuição e mesma licença. Mesmo assim, este projeto NÃO redistribui o corpus (nem no Git nem no site).
- Acesso: `aberto` · status: **acessado**
- Formatos: csv · plataforma: twitter · idioma: pt-BR
- Registros confirmados: 21000
- Esquema de anotação: 3 anotadores por tweet; 6 categorias com contagem de votos 0-3 (float no CSV).
- Contexto: Tweets gerais; não é corpus político.
- Integridade: sha256 do arquivo (acima) e commit git 6b325d26
- Referência: Leite et al. (2020). Toxic Language Detection in Social Media for Brazilian Portuguese: New Dataset and Multilingual Analysis. arXiv:2010.04543 (AACL-IJCNLP 2020).
- Fonte: https://github.com/JAugusto97/ToLD-Br
- Limitações e vieses:
  - Sem identificadores nem metadados de conversa; deduplicação só por texto.
  - Categorias raras (xenofobia, racismo) com poucos positivos por consenso.
  - Amostra por palavras-chave e perfis; viés de coleta e de anotadores (42 voluntários).
  - A distribuição e a duplicata de retweets podem inflar métricas se o split ignorar quase-duplicatas.

## HateBR 2.0 e HateBRXplain (`hatebr`)

- Versão/revisão: `main@a1301437a7b21620fbf0110a300c4c927a247daf` · data: 2026-01-05
- Licença: CC-BY-NC-4.0
- Redistribuição: Somente uso não comercial, com atribuição. O corpus NÃO é redistribuído por este projeto.
- Acesso: `aberto` · status: **acessado**
- Formatos: csv · plataforma: instagram · idioma: pt-BR
- Registros confirmados: 7000
- Esquema de anotação: Binário (ofensivo/não) com 3 anotadores especialistas; HateBRXplain acrescenta justificativas (rationales) de 2 anotadores como trechos de texto. Níveis de ofensa e alvos de ódio existem só na versão 1.0, sob pedido, NÃO integrados.
- Contexto: Comentários em publicações de políticos brasileiros (78 publicações no arquivo). O nome da conta do político NÃO é carregado para as amostras normalizadas.
- Integridade: sha256 dos arquivos (acima) e commit git a1301437
- Referência: Vargas et al. (2022) HateBR, LREC 2022, aclanthology 2022.lrec-1.777; Salles, Vargas & Benevenuto (2025) HateBRXplain, COLING 2025, aclanthology 2025.coling-main.446.
- Fonte: https://github.com/franciellevargas/HateBR
- Limitações e vieses:
  - Domínio político em Instagram; ofensa binária mistura insulto, xingamento e discurso de ódio.
  - Só 78 publicações; split por publicação gera poucos grupos.
  - Rationales são trechos textuais, não offsets; offsets são derivados por busca e podem falhar.
  - Equilíbrio artificial 50/50 (3.500/3.500) não reflete prevalência real.

