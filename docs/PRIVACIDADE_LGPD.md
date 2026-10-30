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

Detalhes em [PARTICIPACAO.md](PARTICIPACAO.md), [PRIVACIDADE_PARTICIPACAO.md](PRIVACIDADE_PARTICIPACAO.md), [FORMSPREE_FREE.md](FORMSPREE_FREE.md), [MIGRACAO_FORMSPREE.md](MIGRACAO_FORMSPREE.md) e [CLOUDFLARE_SETUP.md](CLOUDFLARE_SETUP.md).

- Envio voluntário, por ação explícita, sem pedir nome nem e-mail e com consentimento marcado (nunca presumido).
- Frase de visitante entra na fila como Pendente, mascarada, e **nunca** é publicável até uma pessoa anonimizá-la e aprová-la.
- O texto original não é o arquivo permanente: importe, revise e apague a exportação. Relatórios agregados podem permanecer sem os textos.
- Avaliações voluntárias em lote (até cinco por submissão) e votos importados viram contagem por frase e por versão editorial, exibida com no mínimo 10.
- A aplicação não coleta IP, geolocalização, fingerprint nem identificadores persistentes. Hospedagem e serviço de recebimento podem processar dados técnicos (como IP). Com o Worker, o D1 não guarda IP/UA; o Turnstile e a rede Cloudflare podem processar metadados na verificação. O site avisa; não há anonimato absoluto.
- Pedido de remoção: rejeitar o item na fila, apagar a submissão no D1 se já estiver lá, e regenerar o site. Textos: retenção limitada (`analytics retencao` e `sql/exclusao.sql`).

## Site

- Sem cookies, sem medição de audiência, sem fontes/CDN, sem `localStorage`. Chamadas externas só no envio: o serviço de recebimento e, se `provedor=cloudflare`, o script do Turnstile (`challenges.cloudflare.com`), carregado na hora de participar — não na mera navegação.
- As escolhas do visitante ficam só na memória da página; um lote só sai se a pessoa confirmar no fim da sequência. Navegação não é enviada.
- Todo texto é inserido por `textContent`; nada de HTML vindo de dados.

## Base legal e minimização (LGPD)

- Finalidade: pesquisa e educação sobre discriminação em contexto político, com revisão humana.
- Minimização: guarda-se o mínimo necessário; dados pessoais não são necessários para o produto público.
- Se uma pessoa pedir remoção de conteúdo fornecido por ela, o item é rejeitado na fila e o site é regenerado.

## Pendente de responsabilidade humana

- Confirmar a anonimização das frases reais antes de aprovar.
- Conferir os termos de uso de cada dataset antes de qualquer uso diferente do atual (pesquisa e educação sem fins comerciais).

## Compartilhar uma frase

Cada frase tem os botões "Compartilhar" (menu do celular), "WhatsApp" e "Copiar mensagem". A mensagem é um convite em forma de pergunta ("Onde você coloca a linha entre opinião e discriminação?"), com a frase de exemplo e o link direto; não rotula ninguém. Nada é enviado, medido ou guardado pelo site: o link do WhatsApp só abre quando a pessoa toca no botão, e o destino é o próprio WhatsApp (que tem a política dele). Frases em rascunho local não mostram esses botões.
