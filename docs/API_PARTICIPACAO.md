# API de participação `POST /api/v1/participacoes`

Único endpoint público. Sem listagem, sem admin, sem GET de registros.

## Contrato

- URL (local): `http://127.0.0.1:8787/api/v1/participacoes` (porta do `wrangler dev`).
- URL (produção): `https://eh-so-opiniao-api.bettoni-gn.workers.dev/api/v1/participacoes`.
- `Content-Type: application/json`.
- Corpo ≤ 8000 bytes.
- CORS: origem `https://giovaninb.github.io` ou localhost explícito. CORS **não** autentica.

### Campos comuns

| Campo | Quem gera | Notas |
|---|---|---|
| `schema_version` | cliente | `"3"` no caminho Cloudflare |
| `tipo` | cliente | `avaliacoes` \| `contestacao` \| `sugestao_frase` (aliases Formspree aceitos) |
| `submission_id` | cliente, UUID por tentativa | idempotência; **não** é id de pessoa |
| `aviso_versao` | cliente | versão do aviso lido |
| `consentimento` | cliente | obrigatório (`sim`) |
| `turnstile_token` | widget | Siteverify no Worker: `success`, hostname (`giovaninb.github.io` em produção), `action=participacao` quando presente; uso único; **não** gravado |
| `created_at` | servidor | ISO-8601; timestamps do navegador são ignorados |
| `armadilha` | honeypot | se preenchida, 422 |

Aliases aceitos na borda: `avaliacoes_voluntarias`→`avaliacoes`; `opiniao`/`discriminacao`/`contexto`; `erro_no_texto`→`erro_texto`.

### Avaliações (`tipo=avaliacoes`)

Até 5 itens. Cada um: `frase_id`, `tema_id`, `modo`, `avaliacao`, `conteudo_versao`, `contexto_exibido`, `analise_revelada`.

`avaliacao`: `nao_vejo_problema` \| `possivel_discriminacao` \| `preciso_contexto`.

Não constrói perfil individual. 1 lote = 1 submissão + N avaliações.

### Contestação

`frase_id`, `conteudo_versao`, `motivo` (opcional se houver comentário), `comentario` (opcional se houver motivo).

Motivos: `falta_contexto`, `discordo_classificacao`, `explicacao_incompleta`, `interpretacao_excessiva`, `erro_texto`, `outro`.

Não é publicada automaticamente.

### Sugestão

`texto` (10–280), `interpretacao_sugerida`, `contexto` opcional. HTML executável recusado.

## Respostas

```json
{ "ok": true, "submission_id": "…", "idempotente": false }
```

O mesmo `submission_id` de uma gravação já feita devolve `200` com `idempotente: true` (falha de rede depois do INSERT).

Erros: `{ "ok": false, "erro": "validacao|turnstile|indisponivel|abuso|payload|metodo", "mensagem": "…" }`. Validação inclui `falhas`.

| HTTP | Quando |
|---|---|
| 200 | gravado ou idempotente |
| 400 | JSON malformado |
| 403 | origem, Turnstile inválido/hostname/action |
| 405 | método ≠ POST |
| 409 | token Turnstile reutilizado/expirado |
| 413 | corpo grande |
| 415 | Content-Type |
| 422 | esquema |
| 429 | rate limit (aproximado) |
| 503 | D1 ou Siteverify indisponível; secret ausente |

Não há sucesso sem gravação no D1 (ou confirmação de que o UUID já existia).
