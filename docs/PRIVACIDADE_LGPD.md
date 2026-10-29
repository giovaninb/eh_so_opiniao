# Privacidade e LGPD — É Só Opinião?

Não é parecer jurídico. Registra as decisões de projeto.

## O que o projeto não faz

- Não identifica pessoas, não infere preferência eleitoral, não monta perfis nem rankings de indivíduos.
- Não faz vigilância direcionada nem denúncia automatizada.
- Não reidentifica autores de comentários nem anotadores dos datasets.
- Não trata pontuação de modelo como evidência de crime. A decisão é sempre humana e, sobre crime, da Justiça.

## Dados em três camadas

| Camada | Conteúdo | Vai ao Git / GitHub Pages? |
|---|---|---|
| Conteúdo público | frases sintéticas ou fornecidas e anonimizadas, aprovadas por pessoa; taxonomia; catálogo; achados numéricos | Sim (`site/data/`) |
| Dados de pesquisa | corpora brutos e normalizados, relatórios locais, fila de revisão, modelos | **Não** (`datasets/_local/`, `relatorios/local/`) |
| Evidência original | capturas e arquivos do monitor de assédio eleitoral | **Não**; pasta própria, fora do site |

## Datasets científicos

- Corpora brutos **não** são commitados e **não** são exibidos no site. Isso vale mesmo para licenças que permitem redistribuição.
- Nomes de conta e URLs do HateBR são descartados na normalização; só um hash de agrupamento permanece.
- Votos individuais de anotadores, quando o dataset os traz, são guardados sem qualquer identificação do anotador.
- Conteúdo ofensivo dos datasets não é reproduzido em documentos; relatórios trazem só contagens, métricas e ids.
- A lista de falsos positivos com texto (experimento D) fica em `datasets/_local/experimentos/`, fora do Git.

## Frases do site

- Só origens `sintetica_ilustrativa`, `fornecida_pelo_operador` ou `visitante_anonimizada` (frase de visitante reescrita por pessoa). Origem de dataset científico é recusada na fila.
- Frase fornecida deve ser anonimizada antes: sem nomes, @, telefones, links, locais que identifiquem a pessoa.
- Revisão humana obrigatória; revisor registrado no histórico local, **não** exposto no site.
- Varredura de vazamento contra os corpora locais antes de gerar os JSON; se achar coincidência, a publicação aborta.

## Participação de visitantes

Detalhes em [PARTICIPACAO.md](PARTICIPACAO.md).

- Envio voluntário, por ação explícita, sem pedir nome nem e-mail e com consentimento marcado.
- Frase de visitante entra na fila como Pendente, mascarada, e **nunca** é publicável até uma pessoa anonimizá-la e aprová-la.
- O texto original não é guardado no banco local; o CSV exportado deve ser apagado após a importação.
- Votos viram só contagem por frase, exibida com no mínimo 10 votos.
- O serviço externo de formulário pode registrar dados técnicos (como IP). O site avisa; escolha o serviço com isso em mente.
- Pedido de remoção: rejeitar o item na fila e regenerar o site.

## Site

- Sem cookies, sem analytics, sem recursos externos (fontes/CDN), sem `localStorage`. A única chamada externa é o envio do formulário, só quando o visitante clica em enviar e o envio está ativado.
- As escolhas do visitante ("é só opinião / é discriminação / depende") ficam só na página aberta; só são enviadas se o visitante clicar em "Contar minha leitura na enquete".
- Todo texto é inserido por `textContent`; nada de HTML vindo de dados.

## Base legal e minimização (LGPD)

- Finalidade: pesquisa e educação sobre discriminação em contexto político, com revisão humana.
- Minimização: guarda-se o mínimo necessário; dados pessoais não são necessários para o produto público.
- Se uma pessoa pedir remoção de conteúdo fornecido por ela, o item é rejeitado na fila e o site é regenerado.

## Pendente de responsabilidade humana

- Confirmar a anonimização das frases reais antes de aprovar.
- Conferir os termos de uso de cada dataset antes de qualquer uso diferente do atual (pesquisa e educação sem fins comerciais).
