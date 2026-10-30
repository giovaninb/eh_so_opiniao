# Esquema D1 `eh-so-opiniao-db`

Migration: `cloudflare/migrations/0001_init.sql`.

Nenhuma coluna de IP, User-Agent, e-mail, nome ou token Turnstile.

## Tabelas

**submissions** — recebimento. `id` (UUID), `tipo`, `schema_version`, `created_at` (servidor), `aviso_versao`, `consentimento=1`, `estado_revisao`.

**evaluations** — uma linha por avaliação do lote. FK `submission_id`. `avaliacao` só nos três valores canônicos.

**contestations** — uma por contestação. `estado_revisao` próprio.

**suggestions** — texto, interpretação, contexto. `estado_revisao`.

Índices: `frase_id`, `tema_id`, versão editorial, `created_at`, `tipo`. Só o que os relatórios usam.

Gravação: `batch()` atômico (submissão + filhos). Se o INSERT de `id` colidir, a API trata como idempotente.

## Consultas

Arquivo: `cloudflare/sql/relatorios.sql`. Exportação: `sql/backup.sql`. Exclusão: `sql/exclusao.sql` (apague filhos antes, depois a submissão).

```bash
npx wrangler d1 execute eh-so-opiniao-db --local --file=sql/relatorios.sql
```

Nunca rode isso a partir do site público.

## Retenção

Textos de sugestão e contestação: revisar e, se não forem necessários, expurgar (`estado_revisao='expurgada'` e esvaziar `texto`/`comentario`). Relatórios agregados podem permanecer. Comando local Python: `analytics retencao`. Dump D1: importe e depois apague o JSON.
