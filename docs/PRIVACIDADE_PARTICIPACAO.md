# Privacidade da participação

A aplicação **não coleta**:

- nome, e-mail, telefone
- IP (pela aplicação)
- geolocalização, user-agent detalhado, fingerprint
- preferência eleitoral do visitante
- histórico de navegação entre visitas
- identificadores persistentes (nada em `localStorage`, cookie ou similar)
- URL completa de origem que possa carregar dado pessoal

O **consentimento** é uma ação marcada no momento do envio. Não há consentimento presumido, pré-marcado ou herdado de outra tela.

## O que a hospedagem e o serviço de recebimento podem tratar

O site avisa isso com clareza. O recebimento público é o Worker + D1 + Turnstile.

- GitHub Pages hospeda o site estático.
- As participações vão ao D1 **sem** IP, User-Agent ou token Turnstile gravados pela aplicação. O Siteverify da Cloudflare processa o token (e metadados de rede da verificação). A Rate Limiting API pode usar um hash efêmero de IP só em memória, por localidade, sem persistir.
- Isso **não** é anonimato absoluto. A aplicação não lê, não armazena e não reenvia esses dados técnicos.

## Finalidade

As contribuições servem para **revisar a clareza editorial** das frases e análises, não para medir preconceito na sociedade nem para perfilar quem participa.

Sugestões recebidas **não** são usadas automaticamente como dado de treinamento.

Contestações **não** são publicadas automaticamente e **não** geram resposta individual.

## Envio voluntário

Explorar o site funciona sem enviar nada. Avaliações da visita ficam só na memória da página. Só saem se a pessoa confirmar “Contribuir com minhas avaliações”, enviar uma sugestão em Participar, ou uma contestação.

Não há fila de reenvio em segundo plano. Não há acúmulo em armazenamento local para enviar depois sem nova autorização.
