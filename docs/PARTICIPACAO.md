# Participação de visitantes

Objetivo: levar mais gente a discutir discurso de ódio sem amplificá-lo. O visitante pode (1) enviar uma frase e dizer como a lê e (2) registrar sua leitura das frases publicadas.

**Regra central:** nada enviado por visitante é publicado automaticamente. Só entra no site o que foi anonimizado por uma pessoa e aprovado.

## Como funciona

```
Site (formulário) ──> serviço externo PRIVADO ──> CSV exportado por você ──> participacao ──> revisão ──> site
```

1. O formulário do site envia (`tipo=frase` ou `tipo=voto`) a um serviço de formulário externo. Nada vai a repositório público.
2. Você exporta o CSV e roda `python -m eh_so_opiniao participacao envios.csv`.
3. **Frases** entram como `Pendente`, origem `enviada_por_visitante`, já mascaradas (link, e-mail, @usuário, telefone, documento). O texto original **não** é guardado no banco. Origem `enviada_por_visitante` **nunca** é publicável.
4. Você lê cada uma (`revisao listar --estado Pendente` mostra também possíveis nomes próprios) e reescreve sem nada identificável:
   `revisao anonimizar --id VS-... --revisor "Nome" --texto "frase reescrita" --tipo exclusao --rotulos exclusao_social_territorial`
   Isso muda a origem para `visitante_anonimizada`, mas **não aprova**. Depois use `aprovar`, `corrigir` ou `rejeitar`.
5. **Votos** viram só contagem por frase. `site` publica a contagem apenas de frases já publicadas e só com no mínimo 10 votos (`data/participacao.json`).
6. Depois de importar, **apague o CSV**: ele pode ter dado pessoal que o visitante digitou.

## Travas

- `aprovar`/`corrigir`/`ambiguo` recusam frase de visitante ainda não anonimizada.
- `anonimizar` recusa texto com link, @, e-mail, telefone ou documento e exige revisor.
- `site` aborta se qualquer frase publicada tiver dado identificável ou texto de corpus científico.
- Importação descarta: sem consentimento, campo-armadilha preenchido, tamanho fora de 10–280, avaliação ou `frase_id` inválidos.
- Reimportar o mesmo CSV não duplica frases nem votos.
- O site limita 3 frases por visita e envia sem credenciais nem referência de origem. Nada fica no navegador.

## Ativar o envio

O envio está **ligado** e aponta para um formulário privado no Formspree (`site/config_participacao.json`: `"ativo": true`, `modo_resposta: "cors"`). Para desligar, mude `ativo` para `false`: o formulário fica desabilitado e nada é enviado. Os passos abaixo valem para trocar de serviço.

1. Crie um formulário privado que aceite **POST com CORS** e responda JSON, como o **Formspree** (campos `tipo`, `frase`, `avaliacao`, `frase_id`, `consentimento`, `site`). Alternativa sem CORS: **Google Forms** (veja "modo opaco" abaixo).
2. Em `config_participacao.json` coloque a URL de envio (precisa começar com `https:`), ajuste `campos` aos nomes que o serviço exige (no Google Forms são `entry.NNN`) e mude `ativo` para `true`.
3. Envie um teste, exporte o CSV e rode a importação para conferir.

### Confirmação de envio (`modo_resposta`)

- `"cors"` (padrão): o site lê a resposta do serviço. **Só mostra "Recebido" quando o serviço devolve sucesso** (HTTP 2xx e, se houver JSON, sem `ok: false`/`error`). Erro HTTP, recusa ou falha de rede mostram um erro claro, mantêm o texto escrito e permitem tentar de novo.
- `"opaca"` (serviços sem CORS, como o Google Forms): o navegador não consegue ler a resposta. O site envia, **avisa que não consegue confirmar o recebimento** e não diz "Recebido". Confira no serviço.
- Com `ativo: false`: o formulário fica desabilitado, explica que o envio não está disponível e **nada é simulado nem enviado**.

Os testes automatizados usam um serviço **simulado** (`page.route` do Playwright) para cada um desses cenários; isso valida o comportamento do site, não um serviço real. Os testes **nunca** contatam o Formspree (requisições a ele são bloqueadas). **O serviço real ainda não foi validado por mim**: depois de publicar, envie uma frase de verdade pelo site, confirme que chegou no painel do Formspree e rode `participacao envios.csv` para conferir a importação.

## Limites que você deve conhecer

- **Mascarar não é anonimizar.** A máquina pega padrões; nomes, apelidos, cidades, empresas e eventos só uma pessoa vê. Por isso a revisão é obrigatória.
- O serviço de formulário pode registrar dados técnicos (como IP) pelas regras dele. O site informa isso ao visitante. Escolha um serviço e uma configuração compatíveis com a LGPD e leia os termos.
- A enquete é voluntária e pode ser inflada por quem votar várias vezes (não há identificação de propósito). Os números são informais e o site diz isso.
- Frases novas passam pela sugestão dos baselines só para ajudar a revisão; isso não é decisão nem prova.
- Não implementa ranking de pessoas, denúncia automatizada nem busca de autores. Se uma frase apontar para alguém real, rejeite-a.
