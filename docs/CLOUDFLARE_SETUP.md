# Configuração Cloudflare (plano Free)

Nada disto cria recursos na sua conta até você executar os comandos. O código local usa D1 em `.wrangler/` e as chaves de teste do Turnstile.

Confirmado na documentação oficial (outubro de 2026):

| Serviço | Limite Free usado aqui |
|---|---|
| Workers | 100.000 requisições/dia; 10 ms de CPU; 50 subrequisições; `workers.dev` |
| D1 | 5 milhões de linhas lidas/dia; 100 mil escritas/dia; 500 MB por banco; 5 GB na conta |
| Turnstile | widget e Siteverify gratuitos; token de uso único (~5 min) |
| Rate Limiting API | binding `ratelimits` (Wrangler ≥ 4.36); aproximado e **por localidade**, não é cota global |

Fontes: [Workers limits](https://developers.cloudflare.com/workers/platform/limits/), [D1 limits](https://developers.cloudflare.com/d1/platform/limits/), [Turnstile plans](https://developers.cloudflare.com/turnstile/plans/), [Rate Limit](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/).

Não habilite faturamento nem upgrade automático. Se a cota estourar, o site estático no GitHub Pages continua; o formulário mostra indisponibilidade.

## Ambientes

| | Local | Produção |
|---|---|---|
| Worker | `npx wrangler dev` | `https://eh-so-opiniao-api.bettoni-gn.workers.dev` |
| D1 | `--local` | `--remote` |
| Turnstile | chaves dummy oficiais | sitekey pública no JSON do site; secret só no Worker |
| Origens CORS | `.dev.vars` (`127.0.0.1`, `localhost`) | só `https://giovaninb.github.io` |

Hostname de produção esperado no Siteverify: `giovaninb.github.io`.

## Recursos já existentes (não criar outros)

1. Worker `eh-so-opiniao-api` → `https://eh-so-opiniao-api.bettoni-gn.workers.dev`
2. D1 `eh-so-opiniao-db`, binding `DB`, id `4e8735b1-6aa8-4fb9-b5e1-b939b24d4e7b`
3. Turnstile sitekey pública no site: `0x4AAAAAAFs35eoOZCM90BMD`
4. Secret `TURNSTILE_SECRET_KEY`: conferir com `npx wrangler secret list` (só nomes). Se já existir, **não** rode `secret put` de novo.
5. O site público já usa este Worker (`provedor: cloudflare`). Sem Formspree.

## Comandos (na pasta `cloudflare/`)

```bash
cd cloudflare
npm install
cp .dev.vars.example .dev.vars   # já traz a secret de teste
npx wrangler d1 migrations apply eh-so-opiniao-db --local
npx wrangler dev
npm test   # node:test + D1 fake + chaves dummy; não fala com D1 remoto
# depois de npm install, opcional: npm run test:vitest
```

Na conta, **neste computador** (o ambiente do Cursor não tem sessão Wrangler):

Se `npx` falhar com `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`:

```bash
export NODE_EXTRA_CA_CERTS="$(python3 -c 'import certifi; print(certifi.where())')"
```

```bash
cd cloudflare
npx wrangler login
npx wrangler secret list
# Se TURNSTILE_SECRET_KEY já aparecer na lista, NÃO rode secret put.
# Só se faltar:
# npx wrangler secret put TURNSTILE_SECRET_KEY
npx wrangler d1 migrations apply eh-so-opiniao-db --remote
npx wrangler deploy
```

Não use `wrangler d1 create` de novo. Não crie outro Worker. O `npm run deploy` do package.json recusa publicar sozinho; o comando acima é o `npx wrangler deploy` autorizado.

O stub atual em `https://eh-so-opiniao-api.bettoni-gn.workers.dev` responde `Hello World!` até este deploy.

Depois do deploy, sem gravar participação real e sem imprimir tokens:

```bash
curl -sS -D - -X GET "https://eh-so-opiniao-api.bettoni-gn.workers.dev/api/v1/participacoes" -o /dev/null
# esperado: 405
curl -sS -D - -X OPTIONS "https://eh-so-opiniao-api.bettoni-gn.workers.dev/api/v1/participacoes" \
  -H "Origin: https://giovaninb.github.io" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" -o /dev/null
# esperado: 204 e Access-Control-Allow-Origin: https://giovaninb.github.io
curl -sS -D - -X POST "https://eh-so-opiniao-api.bettoni-gn.workers.dev/api/v1/participacoes" \
  -H "Origin: https://giovaninb.github.io" \
  -H "Content-Type: application/json" \
  --data '{"tipo":"sugestao_frase"}' -o /dev/null
# esperado: 422 (sem token, sem gravar)
npx wrangler d1 execute eh-so-opiniao-db --remote --command "SELECT COUNT(*) AS n FROM submissions"
# só a contagem, não o conteúdo
```

## Secrets e variáveis

- Público no site: `turnstile_sitekey` = `0x4AAAAAAFs35eoOZCM90BMD` (`config_participacao.json` e `data-sitekey` no formulário Participar).
- Só no Worker: `TURNSTILE_SECRET_KEY`.
- `ALLOWED_ORIGINS` e `ALLOWED_HOSTNAMES` em produção: só `giovaninb.github.io`. Localhost fica em `.dev.vars`, não no Worker publicado.
- `secrets.required`: `TURNSTILE_SECRET_KEY`. Sem `Access-Control-Allow-Origin: *`.

Chaves oficiais de teste: sitekey `1x00000000000000000000AA`, secret `1x0000000000000000000000000000000AA`, token `XXXX.DUMMY.TOKEN.XXXX`. [Documentação](https://developers.cloudflare.com/turnstile/troubleshooting/testing/).

## Rate limiting

O binding `LIMITE` (8 chamadas / 60 s **por colo**) usa uma chave derivada de `CF-Connecting-IP` só na memória da API de limite. **Não** grava IP no D1. Os limites são aproximados e por localidade Cloudflare.

## Se o Worker cair

O GitHub Pages segue no ar. Os formulários mantêm o texto e permitem nova tentativa explícita. Exploração, Descobrir, Comparar e o catálogo não dependem da API.

## Backup

```bash
npx wrangler d1 execute eh-so-opiniao-db --local --json --file=sql/backup.sql > /tmp/d1-local.json
# remoto, só autenticado, depois da criação:
# npx wrangler d1 execute eh-so-opiniao-db --remote --json --file=sql/backup.sql
```

Time Travel do D1 Free: 7 dias. Não substitui exportação sua.
