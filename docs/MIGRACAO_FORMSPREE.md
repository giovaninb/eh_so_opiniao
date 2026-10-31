# Migração Formspree → Cloudflare

A Etapa F está concluída: o site público envia só ao Worker. O Formspree não é mais caminho vivo nem rollback no frontend.

## Arquitetura

```
GitHub Pages (site/) ──POST JSON + Turnstile──> Worker + D1
                         └── analytics importar (dump Wrangler ou .eml antigo) ──> revisão humana ──> site
```

Tipos na API v3: `avaliacoes`, `contestacao`, `sugestao_frase`. A UI ainda usa `opiniao` / `discriminacao` / `contexto` e o Worker mapeia.

Não há migração automática do histórico privado do Formspree. Preserve e-mails/.eml já baixados e importe com `analytics importar`.

## Etapas

| Etapa | Estado |
|---|---|
| A–E | Feitas. Destino público: `https://eh-so-opiniao-api.bettoni-gn.workers.dev/api/v1/participacoes` |
| F Encerramento | Formspree removido do site e da config |

## Mapeamento na borda

| Site (histórico / UI) | D1 / API v3 |
|---|---|
| `avaliacoes_voluntarias` | `avaliacoes` |
| `opiniao` | `nao_vejo_problema` |
| `discriminacao` | `possivel_discriminacao` |
| `contexto` | `preciso_contexto` |
| `erro_no_texto` | `erro_texto` |
| `frase` (comentário) | `comentario` |
| `frase` (sugestão) | `texto` |
