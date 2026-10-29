<!-- GERADO AUTOMATICAMENTE por `python -m eh_so_opiniao docs`. Não edite à mão. -->

# Catálogo de datasets

Fonte: `datasets/registry.yaml`. Estados de acesso: `acessado` (arquivo no cache local, hash conferido), `pendente_autorizacao` (restrito; nada é contornado) e `pendente_fonte` (sem fonte pública verificável; nenhum dado é lido nem inventado). Integração: `integrado` (entra no pipeline e nos experimentos), `somente_sobreposicao` (só para medir sobreposição de textos) e `pendente_fonte`.

| Dataset | Licença | Acesso | Status | Integração | Registros confirmados | Plataforma |
|---|---|---|---|---|---|---|
| ToLD-Br — Toxic Language Detection for Brazilian Portuguese | CC-BY-SA-4.0 | aberto | acessado | integrado | 21.000 | twitter |
| HateBR 2.0 e HateBRXplain | CC-BY-NC-4.0 | aberto | acessado | integrado | 7.000 | instagram |
| MultiDomainYT-ToxBR — corpus multidomínio de comentários tóxicos do YouTube (PUCRS, 2026) | não declarada (condições registradas) | aberto | acessado | integrado | 5.000 | youtube |
| RacismoBR — discurso racista em português do Brasil (UFMG, 2026) | não declarada (condições registradas) | sem_fonte_publica | pendente_fonte | pendente_fonte | não confirmado (sem arquivo lido) | twitter |
| TuPyE — Expanded Brazilian Hate Speech Dataset (somente análise de sobreposição) | não declarada (condições registradas) | aberto | acessado | somente_sobreposicao | 43.668 | twitter e instagram |

## ToLD-Br — Toxic Language Detection for Brazilian Portuguese (`told_br`)

- Versão/revisão: `main@6b325d26a9d25b321a3e9ba98ef98832b56729f5` · data: 2025-02-22
- Licença: CC-BY-SA-4.0
- Redistribuição: Permitida com atribuição e mesma licença. Mesmo assim, este projeto NÃO redistribui o corpus (nem no Git nem no site).
- Acesso: `aberto` · status: **acessado** · integração: `integrado`
- Formatos: csv · plataforma: twitter · idioma: pt-BR
- Registros confirmados: 21000
- Esquema de anotação: 3 anotadores por tweet; 6 categorias com contagem de votos 0-3 (float no CSV).
- Contexto: Tweets gerais; não é corpus político.
- Integridade: sha256 do arquivo (acima) e commit git 6b325d26
- Referência: Leite et al. (2020). Toxic Language Detection in Social Media for Brazilian Portuguese: New Dataset and Multilingual Analysis. arXiv:2010.04543 (AACL-IJCNLP 2020).
- Fonte: https://github.com/JAugusto97/ToLD-Br
- Condições de licença (verificadas em 2026-10-28):
  - declarada: sim · identificador: CC-BY-SA-4.0
  - fonte da verificação: Repositório oficial (arquivo de licença e README).
  - uso neste projeto: Pesquisa e educação sem fins comerciais; apenas métricas agregadas são publicadas.
  - exige reconhecimento explícito do operador antes do download: não
  - restrições:
    - atribuição
    - compartilhamento pela mesma licença em derivados que redistribuam dados
- Limitações e vieses:
  - Sem identificadores nem metadados de conversa; deduplicação só por texto.
  - Categorias raras (xenofobia, racismo) com poucos positivos por consenso.
  - Amostra por palavras-chave e perfis; viés de coleta e de anotadores (42 voluntários).
  - A distribuição e a duplicata de retweets podem inflar métricas se o split ignorar quase-duplicatas.

## HateBR 2.0 e HateBRXplain (`hatebr`)

- Versão/revisão: `main@a1301437a7b21620fbf0110a300c4c927a247daf` · data: 2026-01-05
- Licença: CC-BY-NC-4.0
- Redistribuição: Somente uso não comercial, com atribuição. O corpus NÃO é redistribuído por este projeto.
- Acesso: `aberto` · status: **acessado** · integração: `integrado`
- Formatos: csv · plataforma: instagram · idioma: pt-BR
- Registros confirmados: 7000
- Esquema de anotação: Binário (ofensivo/não) com 3 anotadores especialistas; HateBRXplain acrescenta justificativas (rationales) de 2 anotadores como trechos de texto. Níveis de ofensa e alvos de ódio existem só na versão 1.0, sob pedido, NÃO integrados.
- Contexto: Comentários em publicações de políticos brasileiros (78 publicações no arquivo). O nome da conta do político NÃO é carregado para as amostras normalizadas.
- Integridade: sha256 dos arquivos (acima) e commit git a1301437
- Referência: Vargas et al. (2022) HateBR, LREC 2022, aclanthology 2022.lrec-1.777; Salles, Vargas & Benevenuto (2025) HateBRXplain, COLING 2025, aclanthology 2025.coling-main.446.
- Fonte: https://github.com/franciellevargas/HateBR
- Condições de licença (verificadas em 2026-10-28):
  - declarada: sim · identificador: CC-BY-NC-4.0
  - fonte da verificação: Repositório oficial franciellevargas/HateBR (licença e README).
  - uso neste projeto: Pesquisa e educação sem fins comerciais; apenas métricas agregadas são publicadas.
  - exige reconhecimento explícito do operador antes do download: não
  - restrições:
    - atribuição
    - somente uso não comercial
- Verificação cruzada com o HateBRXplain:
  - **repositorio auditado**: https://github.com/isadorasalles/HateBRXplain
  - **revisao auditada**: main@e951f1755b (2025-02-04)
  - **verificado em**: 2026-10-29
  - **conteudo do repositorio**: data/HateBRXplain.json e data/hatebr_and_rationales.csv (7.000 comentários), notebooks de classificadores (mBERT, BERTimbau, DistilBERTimbau, PTT5), explicabilidade com LIME e SHAP, métricas de plausibilidade e fidelidade, concordância entre anotadores.
  - **comparacao com o arquivo integrado**: Os mesmos 7.000 comentários; os trechos de justificativa de 6.998 dos 7.000 são idênticos aos de HateBRXplain.csv (franciellevargas/HateBR), com mesma ordem de anotadores. Os trechos não localizáveis no texto (cerca de 1,2%) são os mesmos nas duas fontes. Nenhum dado novo foi integrado.
  - **licenca no repositorio auditado**: Não declarada (sem arquivo LICENSE; README não cita licença). O projeto continua lendo apenas o arquivo do repositório com licença CC-BY-NC-4.0.
  - **uso no projeto**: Apoia o experimento de explicabilidade (trechos relevantes, protocolo AMP-F). Pontuações de LIME/SHAP do repositório NÃO são importadas.
- Limitações e vieses:
  - Domínio político em Instagram; ofensa binária mistura insulto, xingamento e discurso de ódio.
  - Só 78 publicações; split por publicação gera poucos grupos.
  - Rationales são trechos textuais, não offsets; offsets são derivados por busca e podem falhar.
  - Equilíbrio artificial 50/50 (3.500/3.500) não reflete prevalência real.

## MultiDomainYT-ToxBR — corpus multidomínio de comentários tóxicos do YouTube (PUCRS, 2026) (`multidomain_yt_toxbr`)

- Versão/revisão: `main@3d6ca38c3b340e50f4a3cd141b9c0f2a1a41689f` · data: 2026-10-29
- Licença: Não declarada no repositório (sem arquivo LICENSE; GitHub: license=null). O artigo informa disponibilização exclusivamente para fins acadêmicos.
- Redistribuição: Não. Sem licença declarada, nenhuma redistribuição é presumida: o corpus não vai ao Git, ao site nem a terceiros.
- Acesso: `aberto` · status: **acessado** · integração: `integrado`
- Formatos: csv, xlsx · plataforma: youtube · idioma: pt-BR
- Registros confirmados: 5000 (5.000 linhas em cada CSV (1 texto vazio e 15 duplicatas exatas incluídos); 6 planilhas com 2.500 linhas cada (2 grupos de 3 anotadores).)
- Esquema de anotação: Cada comentário tem 3 anotadores (dois grupos independentes de três: grupo 1 anotou os 2.500 primeiros, grupo 2 os 2.500 restantes). Nove categorias binárias por anotador, mais a coluna 'inválido'. O vetor do CSV é o consenso por maioria (>=2 de 3) em cada categoria; o rótulo binário é 1 se qualquer categoria tem consenso.
- Contexto: Comentários de 50 vídeos (2 por termo de busca, 25 termos) em cinco domínios temáticos: política polarizada, futebol, conflitos internacionais, feminismo e direitos das mulheres, conteúdo LGBTQIA+. O domínio e o vídeo de cada comentário NÃO constam nos arquivos publicados (as planilhas foram embaralhadas e só a coluna do comentário foi mantida).
- Integridade: sha256 dos arquivos (acima) e commit git 3d6ca38c
- Referência: de Souza, G. Z., Manssour, I. H. (2026). MultiDomainYT-ToxBR: Um Corpus Multidomínio de Comentários Tóxicos do YouTube em Português Brasileiro. STIL 2026, aclanthology 2026.stil-1.36.
- Fonte: https://github.com/DAVINTLAB/MultiDomainYT-ToxBR
- Artigo: https://aclanthology.org/2026.stil-1.36/
- Condições de licença (verificadas em 2026-10-29):
  - declarada: NÃO · identificador: nenhuma (sem LICENSE no repositório; artigo: 'exclusivamente para fins acadêmicos')
  - fonte da verificação: API do GitHub (license=null), árvore do repositório no commit 3d6ca38c e seção 8 (Considerações Éticas) do artigo.
  - uso neste projeto: Pesquisa acadêmica sem fins comerciais, apenas em cache local; apenas métricas agregadas são publicadas.
  - exige reconhecimento explícito do operador antes do download: sim (`--aceito-licenca`)
  - restrições:
    - somente fins acadêmicos (declaração do artigo)
    - sem redistribuição dos comentários, dos vetores de rótulos nem das planilhas de anotadores
    - sem publicar comentários no site nem no Git
    - licença formal ausente: recomenda-se pedir confirmação por escrito aos autores antes de qualquer uso além da pesquisa local
- Ficha científica:
  - **verificacao do esquema**:
    - **verificado em**: 2026-10-29
    - **csv binario**: cabeçalho text,label; 5.000 linhas; label ∈ {0,1} (3.546 zeros e 1.454 uns).
    - **csv multirrotulo**: cabeçalho text,label; 5.000 linhas; label é uma string '[a, b, ..., i]' com 9 inteiros 0/1 (42 vetores distintos). Os nomes das classes NÃO estão no arquivo.
    - **planilhas**: cabeçalho comentario + 9 categorias + inválido; valores 0/1 por anotador.
  - **ordem do vetor multirrotulo**:
    - **ordem verificada**:
      - insulto_de_baixo_calao
      - homofobia
      - racismo
      - misoginia_machismo
      - xenofobia
      - violencia_extremismo
      - intolerancia_religiosa
      - intolerancia_politica
      - anticapacitismo
    - **como foi verificada**: O vetor de cada uma das 5.000 linhas foi reconstruído a partir das seis planilhas (maioria >=2 de 3 por grupo) e comparado posição a posição; as 9 posições coincidem 100% com as 9 colunas das planilhas na ordem acima, e o rótulo binário coincide 100% com 'qualquer categoria'. A ordem também é a de `classesFinais` no notebook 3_Tratamento (autores) e a do guia de anotação.
    - **divergencia do readme**: O README descreve o vetor como [insulto, obsceno, homofobia, racismo, misoginia, xenofobia, violência, intolerância_religiosa, intolerância_política]. Isso é inconsistente com os dados: não existe categoria 'obsceno', falta 'anticapacitismo', e todas as posições seguintes ao insulto ficariam deslocadas. NÃO foi usada a ordem do README.
    - **nota sobre o nome anticapacitismo**: A coluna se chama 'anticapacitismo', mas a definição do guia descreve comentários que zombam, menosprezam ou desumanizam pessoas com deficiência, isto é, conteúdo capacitista. O rótulo mede a PRESENÇA de capacitismo.
  - **concordancia reportada no artigo**:
    - **medida**: Kappa de Fleiss por categoria e por grupo (alfa de Krippendorff difere menos de 0,0001)
    - **grupo 1**:
      - **insulto de baixo calao**: 0.481
      - **homofobia**: 0.734
      - **racismo**: 0.422
      - **misoginia machismo**: 0.532
      - **xenofobia**: 0.329
      - **violencia extremismo**: 0.364
      - **intolerancia religiosa**: 0.549
      - **intolerancia politica**: 0.584
      - **anticapacitismo**: 0.443
      - **media**: 0.493
    - **grupo 2**:
      - **insulto de baixo calao**: 0.262
      - **homofobia**: 0.442
      - **racismo**: 0.332
      - **misoginia machismo**: 0.407
      - **xenofobia**: 0.42
      - **violencia extremismo**: 0.215
      - **intolerancia religiosa**: 0.555
      - **intolerancia politica**: 0.499
      - **anticapacitismo**: 0.218
      - **media**: 0.372
    - **observacao**: A concordância recalculada a partir das planilhas está em relatorios/concordancia_multidomain_yt_toxbr.json (comando `concordancia`).
  - **composicao reportada no artigo**:
    - **total**: 5000
    - **por dominio**: 1.000 comentários por domínio (100 por vídeo; 50% sinalizados como potencialmente tóxicos pelo Detoxify, 50% aleatórios)
    - **prevalencias reportadas**: insulto 18,5%; intolerância política 5,1%; homofobia 3,1%; racismo 17 comentários (0,34%); anticapacitismo 32 (0,64%); violência/extremismo 57 (1,14%)
  - **desempenho reportado no artigo**:
    - **binario**: F1 0,78 (BERTweet.BR, teste de 500 comentários). NÃO é indicador de capacidade de identificar categorias específicas.
    - **multirrotulo**: F1 médio 0,11; só insulto (0,50) e intolerância política (0,52) têm F1 > 0; as outras sete categorias têm F1 0,00; racismo tinha 2 exemplos e anticapacitismo 3 no teste.
  - **domino tematico disponivel por comentario**: False
- Limitações e vieses:
  - Sem licença declarada: uso restrito à pesquisa acadêmica local, sem redistribuição.
  - Amostragem enviesada: 50% dos comentários de cada vídeo foram escolhidos por pontuação do Detoxify (modelo treinado sobretudo em inglês), o que superestima a prevalência de toxicidade e favorece marcadores explícitos.
  - Domínio temático e identificador do vídeo ausentes nos arquivos: não é possível dividir por vídeo nem reportar resultados por domínio; comentários do mesmo vídeo podem cair em divisões diferentes.
  - Duas turmas de três anotadores (nenhum anotador viu o corpus inteiro); concordância moderada no grupo 1 e justa no grupo 2 (kappa médio 0,493 e 0,372).
  - Categorias raras: racismo tem apenas 17 comentários por consenso; resultados por classe são instáveis.
  - Os anotadores trabalharam sem discutir; divergências foram preservadas nas planilhas, mas o CSV só traz o consenso por maioria.
  - A coluna 'inválido' (marcada em 1.472 de 2.500 linhas pelo anotador 2) é descartada pelos autores; foi preservada aqui como metadado e não como rótulo.
  - Rótulo binário inclui insulto de baixo calão: 'tóxico' neste corpus não é sinônimo de discurso de ódio.

## RacismoBR — discurso racista em português do Brasil (UFMG, 2026) (`racismobr`)

- Versão/revisão: `indisponivel (sem revisão pública verificável)` · data: 2026-04-13
- Licença: Não declarada. O artigo diz que o dataset será liberado sob protocolo de divulgação responsável.
- Redistribuição: Não. Sem fonte pública nem licença verificadas, nenhuma redistribuição é presumida.
- Acesso: `sem_fonte_publica` · status: **pendente_fonte** · integração: `pendente_fonte`
- Formatos: — · plataforma: twitter · idioma: pt-BR
- Registros confirmados: não confirmado (nenhum arquivo foi lido) · declarados no artigo: 1.054 (corpus original, derivado) e 858 (subconjunto experimental balanceado); ver ficha_cientifica. NENHUM confirmado por leitura de arquivo.
- Esquema de anotação: Binário: 1 = racista, 0 = não racista (racismo contra pessoas negras). Pares independentes de pesquisadores negros; terceiro avaliador nos casos de divergência.
- Contexto: Posts do X (antigo Twitter): 405 coletados entre setembro/2024 e janeiro/2025 por palavras-chave, mais 629 posts de trabalhos anteriores (2017-2021) reanotados.
- Integridade: indisponível: nenhum arquivo foi obtido
- Referência: Vaz, J. V., Benevenuto, F., Gonçalves, M. A. (2026). RacismoBR: A Manually Annotated Dataset for Racist Discourse Detection in Brazilian Portuguese. PROPOR 2026, vol. 1, pp. 770-779. aclanthology 2026.propor-1.76.
- Fonte: https://github.com/joaovitorvaz/RacismoBR-Dataset
- Artigo: https://aclanthology.org/2026.propor-1.76/
- Condições de licença (verificadas em 2026-10-29):
  - declarada: NÃO · identificador: nenhuma verificada; artigo: liberação sob protocolo de divulgação responsável
  - fonte da verificação: Seção de Considerações Éticas do artigo; a URL do repositório citado devolve 404.
  - uso neste projeto: Nenhum dado é usado. Só o contrato do adaptador é validado, com fixtures sintéticas.
  - exige reconhecimento explícito do operador antes do download: sim (`--aceito-licenca`)
  - restrições:
    - seguir o protocolo de divulgação responsável dos autores quando houver acesso
    - não contornar controle de acesso nem buscar cópias não oficiais
    - sem redistribuição
- **Pendência**: Não há URL oficial nova verificada. Próximos passos legítimos: pedir aos autores (contato publicado no artigo, UFMG/DCC) o acesso pelo protocolo de divulgação responsável, ou aguardar o repositório voltar. Enquanto isso o dataset fica pendente_fonte e nenhum resultado real é reportado.
- Fontes verificadas:
  - https://github.com/joaovitorvaz/RacismoBR-Dataset (página): HTTP 404 (2026-10-29)
  - API do GitHub para o mesmo repositório: HTTP 404 (2026-10-29)
  - raw.githubusercontent.com para o mesmo repositório: HTTP 404 (2026-10-29)
  - Lista dos repositórios públicos do autor no GitHub (14): nenhum chamado RacismoBR ou equivalente (2026-10-29)
  - Busca por 'RacismoBR' no GitHub e no Hugging Face: sem resultados (2026-10-29)
  - Zenodo: HTTP 403 (INCONCLUSIVO: bloqueio automático, não prova ausência) (2026-10-29)
  - Internet Archive (Wayback Machine): HTTP 429 (INCONCLUSIVO: limite de requisições) (2026-10-29)
- Ficha científica:
  - **definicao operacional**:
    - **original en**: Racism is any form of expression, direct or indirect, that conveys the hierarchization of phenotypes, the internalization of a negative self-image, or the subordination of black people. This includes discourse that demeans, offends, discriminates, or stigmatizes black individuals on the basis of race, ancestry, or phenotypic traits, whether explicitly or implicitly. (adaptada de Almeida, 2019)
    - **traducao pt**: Racismo é toda forma de expressão, direta ou indireta, que transmita a hierarquização de fenótipos, a internalização de uma autoimagem negativa ou a subordinação de pessoas negras. Inclui discurso que deprecia, ofende, discrimina ou estigmatiza pessoas negras com base em raça, ascendência ou traços fenotípicos, de forma explícita ou implícita.
    - **alvo**: racismo contra pessoas negras; outras formas de preconceito racial ou étnico não são o foco declarado
  - **rotulos originais binarios**:
    - **1**: racista
    - **0**: nao_racista
  - **proveniencia**:
    - **coleta nova**: 405 posts e respostas do X, coletados de setembro/2024 a janeiro/2025 por serviço pago da API, só conteúdo público, identificadores diretos removidos; seleção intencional por palavras-chave (mulambo, racismo, racista, angolano/a, candomblé, africano/a, neguinho/a).
    - **literatura**: 629 posts do X, coletados em 2017-2021 e rotulados como racistas em trabalhos anteriores (Fortuna et al. 2019; Leite et al. 2020 [ToLD-Br]; Augusto 2021; Silva Neto 2017), reanotados do zero com a mesma definição.
    - **plataforma unica**: X (Twitter)
  - **composicao de classes**:
    - **coleta nova apos reanotacao**:
      - **racista**: 113
      - **nao racista**: 312
    - **literatura apos reanotacao**:
      - **racista**: 316
      - **nao racista**: 313
    - **total racista**: 429
    - **reservatorio nao racista**: 625
    - **corpus original derivado**: 1.054 = 429 racistas + 625 não racistas (soma derivada pelo projeto; o artigo cita 429 e 625, não o total)
    - **subconjunto experimental balanceado**:
      - **total**: 858
      - **racista**: 429
      - **nao racista**: 429
      - **metodo**: subamostragem aleatória da classe majoritária antes da validação cruzada (semente 42)
    - **observacao**: Corpus original (desbalanceado) e subconjunto experimental (balanceado artificialmente) são objetos distintos: resultados do subconjunto não refletem a prevalência real.
  - **anotacao e consenso**:
    - **anotadores**: 8 pesquisadores negros, em 4 pares independentes, de origens acadêmicas e regiões diversas
    - **regras**: cada par rotulou de forma independente o seu subconjunto; divergências foram revisadas por um terceiro avaliador independente
    - **concordancia**: 386 dos 405 posts novos com concordância completa; kappa de Cohen mínimo entre os pares = 0,655; 39 posts divergentes revistos por um terceiro avaliador, com 16 reclassificados
    - **posicionalidade**: anotação feita exclusivamente por pesquisadores negros, como escolha epistêmica declarada
  - **limitacoes de amostragem**:
    - Amostragem intencional por palavras-chave: pode moldar a distribuição lexical e não é probabilística.
    - Foco em racismo contra pessoas negras; não separa outras formas de preconceito.
    - Análise de turno único, sem contexto conversacional.
    - Mistura de posts de 2017-2021 e 2024-2025: possível deriva temporal de linguagem, mitigada pela reanotação única.
    - Plataforma única (X).
    - Parte dos posts da literatura vem do ToLD-Br: sobreposição esperada com o ToLD-Br (e com o TuPyE), que deve ser medida antes de qualquer avaliação cruzada.
  - **inconsistencias do artigo**:
    - Declara 405 posts novos anotados, mas 113 racistas + 312 não racistas somam 425.
    - Declara 386 de 405 com concordância completa e, em seguida, 39 posts divergentes: 386 + 39 = 425, não 405.
  - **contrato esperado do arquivo**:
    - **status**: NÃO verificado contra o arquivo real, que não foi obtido
    - **colunas minimas**:
      - text
      - label
    - **colunas opcionais**:
      - origin
      - subset
    - **label**: 1 = racista, 0 = não racista (convenção do artigo)
    - **origin**: coleta_nova | literatura (proveniência por exemplo)
    - **subset**: experimental_balanceado | reservatorio (separa o subconjunto de 858 do restante)
    - **nota**: O adaptador aceita um mapa de colunas para absorver os nomes reais quando o arquivo existir e recusa o que não bater.
- Limitações e vieses:
  - Fonte pública indisponível hoje: nenhum número sobre o dataset foi confirmado, apenas os declarados no artigo.
  - Amostragem por palavras-chave, foco em racismo contra pessoas negras, turno único, plataforma única (X).
  - Sobreposição esperada com o ToLD-Br e com o TuPyE: avaliação cruzada exige deduplicação por texto.
  - O subconjunto de 858 é balanceado artificialmente (429/429) e não representa prevalência.
  - Inconsistência numérica no artigo (405 versus 425 posts novos).

## TuPyE — Expanded Brazilian Hate Speech Dataset (somente análise de sobreposição) (`tupye`)

- Versão/revisão: `master@b89c2c3a8d3bc784677f12131e2c2ee560909886` · data: 2024-01-02
- Licença: CC-BY-4.0 no cartão do Hugging Face; o repositório do GitHub não tem arquivo de licença; conflito com as licenças dos componentes (ToLD-Br CC-BY-SA-4.0, HateBR CC-BY-NC-4.0).
- Redistribuição: Não. O conflito de licenças com os componentes impede presumir permissão; o corpus não vai ao Git nem ao site.
- Acesso: `aberto` · status: **acessado** · integração: `somente_sobreposicao`
- Formatos: csv · plataforma: twitter e instagram · idioma: pt-BR
- Registros confirmados: 43668 (34.934 linhas no treino e 8.734 no teste (binário); soma 43.668, igual ao total do README. Os arquivos multirrótulo e de votos não foram baixados.)
- Esquema de anotação: Binário agressivo/ódio (colunas aggressive e hate) agregando três fontes por voto de maioria. 'hate' EXCLUI textos que só são ofensivos ou obscenos: definição de ódio diferente da do ToLD-Br e da do HateBR. A versão multirrótulo (13 colunas) não foi usada.
- Contexto: Composição por pesquisador: Leite et al. (ToLD-Br) 21.000, TuPy 10.000, Vargas et al. (HateBR) 7.000, Fortuna et al. 5.668. Por construção, 28.000 dos 43.668 documentos (64%) vêm do ToLD-Br e do HateBR.
- Integridade: sha256 dos arquivos (acima) e commit git b89c2c3a8d
- Referência: Oliveira et al. (2023). TuPy-E: detecting hate speech in Brazilian Portuguese social media with a novel dataset and comprehensive analysis of models. arXiv:2312.17704.
- Fonte: https://github.com/Silly-Machine/TuPyE-Expanded-Brazilian-Hate-Speech-Dataset
- Condições de licença (verificadas em 2026-10-29):
  - declarada: sim · identificador: CC-BY-4.0 (cartão HF) — inconsistente com componentes CC-BY-SA-4.0 e CC-BY-NC-4.0
  - fonte da verificação: Cartão do dataset no Hugging Face (Silly-Machine/TuPyE-Dataset) e árvore do repositório GitHub (sem LICENSE).
  - uso neste projeto: Leitura local só para contar sobreposição de textos com ToLD-Br, HateBR, MultiDomainYT-ToxBR e RacismoBR; os rótulos do TuPyE NÃO entram nos experimentos.
  - exige reconhecimento explícito do operador antes do download: sim (`--aceito-licenca`)
  - restrições:
    - a licença do TuPyE não sobrepõe as dos componentes: tratar o conjunto sob a mais restritiva (CC-BY-NC-4.0 e CC-BY-SA-4.0)
    - sem redistribuição
- Ficha científica:
  - **sobreposicao por construcao**: A coluna 'researcher' identifica a fonte de cada documento; a sobreposição com ToLD-Br e HateBR é estrutural. O resultado medido está em relatorios/sobreposicao_corpora.json.
  - **risco de uso**: Treinar com TuPyE e avaliar em ToLD-Br, HateBR ou RacismoBR (cuja parte da literatura também vem de Fortuna e Leite) produz vazamento. Qualquer uso futuro exige remoção prévia por texto.
- Limitações e vieses:
  - Mistura corpora com definições de ódio e esquemas de anotação diferentes, unificados por voto de maioria.
  - Sobreposição estrutural com ToLD-Br e HateBR.
  - Licença declarada inconsistente com as dos componentes.
  - Classes específicas muito raras no multirrótulo (ex.: etarismo 57, aporofobia 66 em 43.668).

