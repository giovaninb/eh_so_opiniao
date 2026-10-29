# Expansão 2026-10: mulheres, homens, pessoas idosas, religiões e pessoas trans

Esta página descreve os **176 exemplos ilustrativos** (`NX-248` a `NX-423`) integrados em `casos/expansao_2026_10.jsonl`, o que muda no site e o que **ainda depende de pessoas**.

## Em uma frase

Os 176 exemplos entram na fila de revisão como **Pendente**, com `pode_publicar = false`. **Nada foi aprovado, nada foi publicado.** O site publicado continua com as 169 frases anteriores.

## Origem dos exemplos

- São frases **escritas para educação**, sem autoria real, sem comentário coletado de pessoa verdadeira e sem nome, lugar ou evento reais. Não vêm de corpus de treino (HateBR, ToLD-Br etc.).
- Cada registro traz `origem` (como foi escrito), `colecao`, `subtema` e `justificativa_editorial`. Isso fica guardado na fila de revisão. O site **não expõe** autoria, revisor nem coleção.
- A leitura (`discriminação`, `ambígua`, `sem discriminação`) é uma **proposta editorial provisória**. Não é julgamento jurídico e não declara crime.
- O arquivo `catalogo_completo_atualizado.csv` (que traz 247 linhas `NX-001` a `NX-247` de origem não documentada) **não foi importado**.

## O que entra, e o que não entra

| Item | Valor |
|---|---|
| Registros | 176 |
| Discriminação (leitura proposta) | 128 |
| Ambígua / depende do contexto | 25 |
| Sem discriminação (controles) | 23 |
| Estado ao importar | Pendente (todos) |
| `pode_publicar` na entrada | `false` (a leitura recusa qualquer outro valor) |

IDs anteriores (`EX-01` a `EX-158`, `FR-01` a `FR-11`) não mudam. Reimportar não cria duplicatas nem sobrescreve decisão ou correção humana (`store.adicionar` é idempotente).

## Temas e grupos de descoberta

Temas novos em `casos/temas.yaml`: `transfobia`, `idadismo`, `estereotipos_masculinidade`. Continuam valendo `misoginia`, `intolerancia_religiosa`, `lgbtfobia`, `depende_contexto` e `sem_discriminacao`. Homofobia permanece em `lgbtfobia` (o ToLD-Br só tem a classe “homophobia”, mapeada para `lgbtfobia`).

Na taxonomia (`datasets/taxonomy.yaml`, versão 1.2.0) as três classes novas são **exploratórias**: não têm rótulo mapeado de nenhum dataset, e nenhum modelo as treina.

Grupos de descoberta (`casos/grupos_descoberta.yaml`): **Mulheres**, **Homens e expectativas sociais**, **Pessoas idosas**, **Religiões**, **Pessoas trans** e **Orientação sexual (LGB+)**. Só aparecem na tela os grupos que têm frases **publicadas**.

## Dimensões independentes

Cada exemplo tem cinco dimensões, em `casos/expansao_2026_10_dimensoes.yaml`. Elas não se derivam uma da outra e **são propostas da equipe, não resultado de medição**:

| Dimensão | Valores |
|---|---|
| `grupo` | mulheres, homens, pessoas_idosas, religioes, pessoas_trans, pessoas_lgbt |
| `mecanismo` | forma do discurso (desqualificação de mérito, falso elogio, patologização, tutela, demonização religiosa, negação de identidade…) |
| `gravidade` | `estereotipo`, `ofensa`, `exclusao_material`, `incitacao_violencia`, `nao_se_aplica` |
| `contexto_de_uso` | exclusão, dependente de tom e uso, ou posição respeitosa |
| `certeza_rotulo` | alta, média, baixa (ambíguas sempre baixa) |

Distinção usada na `gravidade`: **estereotipo** (generalização), **ofensa** (insulto ou termo pejorativo), **exclusão material** (barreira concreta a emprego, espaço ou serviço) e **incitação à violência**. Nesta remessa **nenhum** exemplo foi classificado como incitação: só a pessoa revisora pode decidir isso. Nenhum campo afirma crime.

## Contexto decide: palavra isolada não classifica

Os controles e as ambíguas existem para isso. Exemplos reais do conjunto:

- `NX-397` “Sinto que nasci no corpo errado, é como descrevo minha vivência.”: **ambígua**, autodescrição, não ofensa.
- `NX-385` “Você é o homem da casa agora.” (ambígua) × `NX-281` “…é o homem da casa e precisa ser forte.” para um adolescente (exclusão, estereótipo).
- `NX-297` “Você está linda para a sua idade.” (ambígua) × `NX-301` “Até que você está lúcido para a sua idade.” (exclusão, falso elogio).
- `NX-400` “Não conheço bem o termo travesti, pode me explicar?”: pergunta, ambígua; `NX-371` usa o mesmo termo para excluir.
- “Macumba” em `NX-326` é uso pejorativo; a mesma palavra citada em denúncia não seria endosso.

O baseline automático (regras) é só rascunho e **não conhece** as classes novas: um teste garante que ele não as atribui.

## Avisos de conteúdo

56 exemplos com termo pejorativo explícito levam `aviso_conteudo`. Na tela:

- aviso não bloqueante antes da frase (`role="note"`), com a opção de pular ou ir direto à análise;
- chip “Aviso de conteúdo” nas listas;
- o **título da página** usa só o ID, nunca o texto;
- a frase **nunca** é o destaque da página inicial;
- a mensagem de compartilhamento **não cita** a frase, só o link.

O aviso não é um rótulo e não diz se a frase é discriminatória.

## Interface de descoberta

Em **Descobrir**, “Tema: Ao acaso. Escolher outro” abre botões com `aria-pressed` e a contagem de frases publicadas de cada grupo. Escolher um tema sorteia cinco frases dele. Continuam valendo “Pular” e “Ver análise sem responder”. Não há nota, ranking nem “acertou/errou”. Em **Pessoas trans** aparece um painel recolhido “Dados e fontes sobre este tema”.

## Dados sobre pessoas trans (ANTRA)

`datasets/contexto_dados.yaml` separa **dado, fonte, ano, metodologia e limitações**:

- **80 assassinatos de pessoas trans em 2025**, cerca de 34% a menos do que os 122 de 2024, segundo o Dossiê ANTRA 2026 (26/01/2026). É um **registro de casos documentados** pela sociedade civil, **sujeito a subnotificação**; não é censo nem taxa por habitante, e a queda de casos registrados não prova queda da violência.
- A estimativa de “35 anos” **não é tábua de mortalidade** e **o site não afirma** que “pessoas trans vivem até 35 anos”.
- **Conferência:** o número, a queda e a metodologia foram conferidos na página da ANTRA e na Agência Brasil em 2026-10-29. **Os PDFs não foram lidos.** O item dos 35 anos segue a nota metodológica recebida pela equipe.

## Avaliação humana (o que falta)

1. Revisar os 176 (folha compacta: `revisao folha --compacta --arquivo folha.csv`; em lote: `revisao lote --arquivo folha.csv --revisor SEU_NOME --aprovar-restantes`, que registra o revisor e a data).
2. Confirmar ou corrigir, por exemplo, `gravidade`, `mecanismo`, `certeza_rotulo` e o `aviso_conteudo` de cada item.
3. Só então rodar `python -m eh_so_opiniao site`. O site publica **apenas** Aprovado/Corrigido (e Ambíguo marcado como publicável).

Recomenda-se que a revisão inclua pessoas dos grupos retratados (mulheres, pessoas idosas, pessoas de religiões de matriz africana, pessoas trans). Isso não foi feito e **não há avaliação humana registrada** para estes 176 exemplos.

## Limites estatísticos

- Os exemplos são **ilustrativos**, não amostra de nada. As contagens (128/25/23) descrevem a biblioteca, não a sociedade.
- Nenhuma métrica de desempenho de modelo foi calculada com eles; as classes novas são exploratórias.
- Proporções entre grupos refletem o que a equipe escreveu, não prevalência de discriminação.

## Testes

`tests/test_eso_expansao.py` (26 testes): IDs únicos e preservados (345), importação idempotente, nada aprovado nem publicado, entrada aprovada recusada, dimensões válidas, casos de contexto, classes exploratórias e dados ANTRA. `e2e/tests/expansao.spec.mjs`: temas, avisos, contexto, larguras 320/360/390/430/768, fonte a 200%, teclado e axe. Resultados: [TESTES_MOBILE.md](TESTES_MOBILE.md).
