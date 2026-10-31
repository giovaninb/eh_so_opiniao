# Participação de visitantes

Objetivo: levar mais gente a discutir discurso de ódio sem amplificá-lo. O visitante pode (1) enviar uma frase com contexto, (2) contestar uma análise e (3) **optar** por enviar, em lote, as leituras de uma sequência.

**Regra central:** nada enviado por visitante é publicado automaticamente. Só entra no site o que foi anonimizado por uma pessoa e aprovado.

Relatórios locais: [ANALYTICS.md](ANALYTICS.md). Privacidade: [PRIVACIDADE_PARTICIPACAO.md](PRIVACIDADE_PARTICIPACAO.md). Histórico da saída do Formspree: [FORMSPREE_FREE.md](FORMSPREE_FREE.md).

## Como funciona

```
Site (ação explícita) ──> Worker + D1 + Turnstile
                       └── analytics importar ──> revisão humana ──> site
```

API: [API_PARTICIPACAO.md](API_PARTICIPACAO.md). O destino está em `config_participacao.json` (`provedor: cloudflare`).

1. O site só envia quando a pessoa confirma. Tipos na API: `sugestao_frase`, `contestacao`, `avaliacoes` (`schema_version=3`). Nada vai a repositório público.
2. Você importa um CSV/JSON/.eml legitimamente acessível: `python -m eh_so_opiniao analytics importar --arquivo arquivo`.
3. **Frases** entram como `Pendente`, origem `enviada_por_visitante`, já mascaradas. Origem `enviada_por_visitante` **nunca** é publicável.
4. Você lê cada uma (`revisao listar --estado Pendente`) e reescreve sem nada identificável:
   `revisao anonimizar --id VS-... --revisor "Nome" --texto "frase reescrita" --tipo exclusao --rotulos exclusao_social_territorial`
   Isso muda a origem para `visitante_anonimizada`, mas **não aprova**. Depois use `aprovar`, `corrigir` ou `rejeitar`.
5. **Avaliações** viram contagem por frase **e** por `conteudo_versao`. `site` publica a contagem apenas de frases já publicadas e só com no mínimo 10 (`data/participacao.json`).
6. Depois de importar, **apague o arquivo original**: ele pode ter dado pessoal.

Registros antigos `tipo=voto|frase|discordancia` continuam sendo importados.

## Travas

- `aprovar`/`corrigir`/`ambiguo` recusam frase de visitante ainda não anonimizada.
- `anonimizar` recusa texto com link, @, e-mail, telefone ou documento e exige revisor.
- `site` aborta se qualquer frase publicada tiver dado identificável ou texto de corpus científico.
- Importação descarta: sem consentimento, campo-armadilha preenchido, tamanho inválido, avaliação ou `frase_id` inválidos, lote com mais de cinco avaliações, campos identificáveis.
- Reimportar o mesmo arquivo não duplica. Duas avaliações iguais no mesmo arquivo **contam as duas** (não são a mesma pessoa por serem iguais).
- O site limita 3 envios de cada tipo por visita (6 no total), desliga o botão durante o POST, recusa preenchimento só por script e não reenvia sozinho. Nada fica no aparelho. Um ataque de robô **não derruba** o GitHub Pages: suspenda as contribuições (`contribuicoes_abertas: false`). Detalhes em [CLOUDFLARE_SETUP.md](CLOUDFLARE_SETUP.md).

## Ativar, suspender e confirmar

O envio está **ligado** (`ativo: true`, `provedor: cloudflare`) para o Worker. `contribuicoes_abertas: false` suspende contribuições e **mantém** o site educativo. Só mostra sucesso com HTTP 2xx. Testes usam serviço **simulado** e **bloqueiam** POST remoto.

## Limites

- Mascarar não é anonimizar.
- A hospedagem e o Turnstile podem registrar dados técnicos. O site informa; não prometemos anonimato absoluto. O D1 da aplicação não guarda IP, User-Agent nem token.
- A participação é voluntária. Números não representam a população.
- Sem identificação persistente, não dá para garantir um voto por pessoa.
- Não implementa ranking de pessoas, denúncia automatizada nem busca de autores.
