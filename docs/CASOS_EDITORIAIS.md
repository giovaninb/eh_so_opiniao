# Casos editoriais (biblioteca de exemplos)

A biblioteca de `casos/biblioteca_editorial.yaml` tem **68 candidatos fictícios** (`EX-01` a `EX-68`) escritos pela equipe, mais 11 frases do estudo de caso (`FR-01` a `FR-11`, já revisadas e publicadas). Os temas ficam em `casos/temas.yaml` (13 temas; é uma organização editorial para navegar, separada da taxonomia científica).

## Natureza e limites

- Todas são **fictícias**: escritas a partir de padrões gerais de linguagem, **não** são citações de pessoas reais, **não** foram copiadas dos datasets científicos nem de redes sociais. O site marca cada cartão como "Exemplo fictício".
- Sem lugares, eventos, empresas, órgãos, partidos, políticos ou perfis reais (um teste automático barra isso).
- Ninguém é identificado, e nenhuma frase afirma crime. A leitura é uma análise de linguagem, não uma acusação.

## Distribuição

| Tipo | Quantidade (68 candidatos) |
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
| Criados (arquivos YAML) | 79 |
| Revisados por uma pessoa (decididos) | 11 |
| Publicados em `site/data/` | 11 |
| Pendentes de revisão | 68 |

Os 68 novos entram como **Pendente** e **não aparecem no site** até uma pessoa decidir. Os testes de interface usam uma cópia de teste (revisor fictício `fixture-e2e`), nunca publicada.

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

A publicação **não mudou**: só `Aprovado`/`Corrigido` (e `Ambíguo` quando permitido) saem, e a varredura de vazamento e de dados identificáveis continua abortando a exportação.
