# Casos editoriais (biblioteca de exemplos)

A biblioteca tem **158 candidatos fictícios** escritos pela equipe: `casos/biblioteca_editorial.yaml` (`EX-01` a `EX-68`) e `casos/biblioteca_ampliada.yaml` (`EX-69` a `EX-158`, com foco em racismo, LGBTfobia, intolerância religiosa, capacitismo, misoginia e xenofobia, mais os contrapontos sem discriminação e ambíguos). Há ainda 11 frases do estudo de caso (`FR-01` a `FR-11`, já revisadas e publicadas). Os temas ficam em `casos/temas.yaml` (15 temas; é uma organização editorial para navegar, separada da taxonomia científica).

## Natureza e limites

- Todas são **fictícias**: escritas a partir de padrões gerais de linguagem, **não** são citações de pessoas reais, **não** foram copiadas dos datasets científicos nem de redes sociais. O site marca cada cartão como "Exemplo fictício".
- Sem lugares, eventos, empresas, órgãos, partidos, políticos ou perfis reais (um teste automático barra isso).
- Ninguém é identificado, e nenhuma frase afirma crime. A leitura é uma análise de linguagem, não uma acusação.

## Distribuição

| Tipo | Quantidade (68 candidatos originais; a ampliação mantém a mesma lógica, com cerca de um terço sem discriminação ou ambíguo) |
|---|---|
| Discriminação / exclusão | 44 |
| Sem discriminação (crítica legítima, humor, citação, denúncia…) | 17 |
| Ambíguo (depende de contexto) | 7 |

Mais de um terço dos candidatos **não** é discriminação clara de propósito: o projeto mostra a linha entre opinião e discriminação, e para isso é preciso mostrar o outro lado dela. Há pares-espelho (mesmo ato, lado político trocado) para o teste de neutralidade.

Cada caso traz: `tema`, `contexto` (cena imaginada), `mecanismo` (o que a frase faz), `razoes` (o que sustenta a leitura), `muda_se` (o que alteraria a leitura) e rótulos **propostos** (não decisão).

## Fluxo: candidato → revisado → publicado

Contagens atuais, separadas (a fila local não é versionada):

| Etapa | Quantidade |
|---|---|
| Criados (arquivos YAML e JSONL) | 345 (169 anteriores + 176 da [expansão 2026-10](EXPANSAO_GENERO_IDADISMO_RELIGIAO_TRANS.md)) |
| Revisados por uma pessoa (decididos) | 169 (158 aprovados em lote pelo revisor após ler a folha compacta) |
| Publicados em `site/data/` | 169 |
| Pendentes de revisão | 176 (todos da expansão 2026-10; nenhum aprovado ou publicado) |

Novos candidatos entram como **Pendente** e **não aparecem no site** até uma pessoa decidir (os 169 anteriores já foram decididos; os 176 NX-248 a NX-423 aguardam revisão). Os testes de interface usam uma cópia de teste (revisor fictício `fixture-e2e`), nunca publicada.

```bash
cd eh_so_opiniao
.venv/bin/python -m eh_so_opiniao casos                      # coloca (idempotente) os casos na fila como Pendente
.venv/bin/python -m eh_so_opiniao revisao folha --arquivo revisao.csv   # planilha com texto, contexto, razões, o que mudaria a leitura
# preencha as colunas decisao (aprovar|rejeitar|ambiguo|corrigir), rotulos_finais e nota
.venv/bin/python -m eh_so_opiniao revisao lote --arquivo revisao.csv --revisor "Seu Nome" --simular   # confere sem gravar
.venv/bin/python -m eh_so_opiniao revisao lote --arquivo revisao.csv --revisor "Seu Nome"             # grava
.venv/bin/python -m eh_so_opiniao revisao interativa --revisor "Seu Nome"                              # alternativa: um por um
.venv/bin/python -m eh_so_opiniao site                                                                # publica só o aprovado
```

Regras do lote (reaproveitam as mesmas funções da revisão individual):

- o **revisor é obrigatório** e fica no histórico de cada item (nunca vai ao site);
- rejeitar, marcar ambíguo e corrigir **exigem justificativa** na coluna `nota`; aprovar não exige;
- é **tudo ou nada**: um erro em qualquer linha impede a gravação de todas, e o relatório lista as linhas com problema;
- linhas sem decisão continuam Pendentes;
- um item já decidido só é decidido de novo com `--reabrir` (o histórico anterior permanece);
- frases enviadas por visitantes só podem ser rejeitadas em lote; para aprová-las é preciso anonimizá-las antes (`revisao anonimizar`).

### Revisão rápida (para quem tem pouco tempo)

A folha **compacta** traz só id, tema, tipo, texto e rótulos propostos, ordenada por tema, e dá para ler 158 frases curtas de uma vez:

```bash
.venv/bin/python -m eh_so_opiniao revisao folha --compacta --arquivo revisao_compacta.csv
# abra no Excel/Numbers, leia e preencha 'decisao' SÓ nas linhas que não devem ser aprovadas (rejeitar/ambiguo/corrigir + nota)
.venv/bin/python -m eh_so_opiniao revisao lote --arquivo revisao_compacta.csv --revisor "Seu Nome" --aprovar-restantes --simular
.venv/bin/python -m eh_so_opiniao revisao lote --arquivo revisao_compacta.csv --revisor "Seu Nome" --aprovar-restantes
```

Com `--aprovar-restantes`, as linhas **sem decisão** são aprovadas **em nome do revisor**, e o histórico de cada uma registra a nota "aprovada em lote… (sem decisão item a item)". Isso é uma decisão sua: só use depois de ler a folha. Sem a flag, linha vazia continua Pendente. Frases enviadas por visitantes nunca entram nessa aprovação em lote. Os exemplos fictícios não trazem nome nem dado pessoal, mas a leitura continua sendo o controle: se uma frase não deveria ir ao ar, marque `rejeitar`.

A publicação **não mudou**: só `Aprovado`/`Corrigido` (e `Ambíguo` quando permitido) saem, e a varredura de vazamento e de dados identificáveis continua abortando a exportação.
