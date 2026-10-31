# Formspree Free — limites e o que o site realmente usa

Confirmado na documentação oficial em 30 de outubro de 2026:

- [Account limits](https://help.formspree.io/articles/account-management/account-limits/): plano Free com **50 submissões por mês**, **30 dias** de histórico, **formulários e projetos ilimitados**, até dois e-mails de notificação.
- [Exporting submissions](https://help.formspree.io/articles/form-and-project-settings/exporting-submissions/): exportação CSV/JSON do dashboard está em planos **Personal, Professional e Business**. **Não está no Free.**
- [Submit forms with JavaScript](https://help.formspree.io/articles/building-your-form/submit-forms-with-javascript-ajax): envio por JavaScript está em **todos os planos**. Este site usa `fetch` próprio, sem a biblioteca `@formspree/ajax` e sem CDN.

Não usamos API paga, webhooks pagos, exportação nativa nem raspagem do dashboard.

Documento **histórico**. O caminho público é o Worker + D1 + Turnstile. O Formspree não recebe mais envios do site. Mantenha este arquivo para importar e-mails/.eml antigos com `analytics importar`. Ver [MIGRACAO_FORMSPREE.md](MIGRACAO_FORMSPREE.md).

## O que o site envia

Três tipos, todos por ação explícita e com consentimento marcado:

| Tipo | Quando | Quantas submissões |
|---|---|---|
| `avaliacoes_voluntarias` | Fim de uma sequência em Descobrir, se a pessoa confirmar o lote | 1 submissão com até 5 avaliações |
| `sugestao_frase` | Formulário Participar | 1 |
| `contestacao` | “Discordo da interpretação” | 1 |

Navegar, escolher uma leitura, abrir a análise, pular ou trocar de página **não** gera POST.

## Bots e abuso (o site não “cai”)

O material educativo está no **GitHub Pages**: é um site estático. Um robô enchendo o formulário **não derruba as páginas**. Quem sofre é a cota do Formspree (50 envios/mês) e, no pior caso, a caixa de entrada.

O que o site faz no navegador, sem identificar ninguém:

- Campo-armadilha (`site`) e `_gotcha` do Formspree: se um robô preencher, **nada é enviado**.
- Exige digitação/interação real no campo; preencher só por script não gera POST.
- Limite por visita (3 de cada tipo, 6 no total) e recusa de payload idêntico já enviado nesta página.
- Botão desligado durante o envio; contribuições podem ser suspensas sem apagar o site.

O que **não** dá para garantir num site estático, sem rastreador e sem plano pago:

- Um robô que se comporta como pessoa (digita, marca o consentimento, espera) ainda pode gastar a cota.
- Um POST direto ao endpoint público do Formspree ignora o JavaScript.
- Sem identificação persistente, não há “um voto por pessoa” nem bloqueio por aparelho.

### O que fazer se houver ataque à cota

1. O site continua no ar. Ninguém precisa tirar o GitHub Pages do ar.
2. Em `site/config_participacao.json`, `"contribuicoes_abertas": false` e publique. O visitante lê as frases; nada é enviado.
3. No painel do Formspree (plano Free): **Restrict to Domain** = `giovaninb.github.io` (sem `https://`). Envios de outros sítios vão para o spam. Confira se a cota ainda se move; se se mover, desative o formulário no painel ou troque o endpoint depois.
4. Não ligue widget de reCAPTCHA do Google neste site: puxaria script externo e identificadores, o que o projeto recusa.
5. Quando passar, volte `"contribuicoes_abertas": true`.

## Cota

A aplicação **não consulta o saldo**. Não há API gratuita para isso. Quando a cota acaba, o Formspree pode responder HTTP 402 (`form over quota`). O site mostra o erro e não tenta reenviar sozinho.

Para suspender contribuições sem desligar o material educativo, em `site/config_participacao.json`:

```json
"contribuicoes_abertas": false
```

Isso não garante o limite global (outro dispositivo ainda pode enviar). É um interruptor operacional, não um contador.

## O que o Free não oferece

- Exportação CSV/JSON pelo dashboard.
- API de listagem de submissões.
- Webhooks (planos pagos).
- Histórico além de 30 dias no painel.
- Confiança de que o e-mail de notificação contenha um formato estável e documentado.

Preservação: baixe as notificações de e-mail (`.eml`) ou copie os campos visíveis no painel para um JSON/CSV local **enquanto o histórico de 30 dias existir**. Importe com o comando em [ANALYTICS.md](ANALYTICS.md). Apague o original se tiver dado pessoal.

## Endpoint

Configurado em `site/config_participacao.json`. Os testes automatizados **bloqueiam** `formspree.io` e usam um serviço simulado.
