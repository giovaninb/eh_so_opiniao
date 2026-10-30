# Migração Formspree → Cloudflare

A Etapa E está autorizada: o destino principal é o Worker. O código Formspree permanece em `envio.js` para rollback (`provedor: formspree` + `_rollback_formspree`). A Etapa F (remoção) ainda não.

## Arquitetura atual (antes da troca)

```
GitHub Pages (site/) ──POST urlencoded──> Formspree Free
                         └── e-mail / cópia manual ──> analytics importar
```

Tipos no ar: `avaliacoes_voluntarias`, `sugestao_frase`, `contestacao` (`schema_version=2`). Campos de avaliação na UI: `opiniao` / `discriminacao` / `contexto`. Motivo `erro_no_texto`.

O Formspree Free não exporta CSV/JSON no dashboard. Não há migração automática do histórico privado. Preserve e-mails/.eml já baixados e importe com `analytics importar`.

## Etapas

| Etapa | Estado |
|---|---|
| A Preparação | Worker + D1 local neste repositório |
| B Testes | Vitest (D1 fake, chaves dummy), pytest, Playwright com mocks |
| C Configuração | **Sua ação:** criar Worker/D1/Turnstile na conta Free |
| D Validação | Um envio real no `wrangler dev` / workers.dev de teste, conferir SELECT no D1 |
| E Atualização | `provedor: "cloudflare"` + endpoint workers.dev + sitekey pública |
| F Encerramento | Remover Formspree do site **só depois** do teste ponta a ponta |

## Etapa E (quando autorizar)

Em `site/config_participacao.json`:

```json
{
  "ativo": true,
  "contribuicoes_abertas": true,
  "provedor": "cloudflare",
  "endpoint": "https://eh-so-opiniao-api.bettoni-gn.workers.dev/api/v1/participacoes",
  "turnstile_sitekey": "0x4AAAAAAFs35eoOZCM90BMD",
  "modo_resposta": "cors"
}
```

Nunca coloque a secret no JSON.

## Checklist para remover o Formspree (Etapa F)

- [ ] Worker no ar em `https://eh-so-opiniao-api.bettoni-gn.workers.dev` (código deste repositório, não o stub Hello World), D1 com migration remota, secret já existente conferida com `secret list`.
- [ ] Um envio real de cada tipo gravado (SELECT nas três tabelas-filhas).
- [ ] Turnstile Siteverify com hostname `giovaninb.github.io`.
- [ ] `provedor: cloudflare` publicado no GitHub Pages e testado no celular.
- [ ] Histórico Formspree (e-mails) importado ou arquivado fora do Git.
- [ ] Só então: apagar `endpoint` formspree, `_gotcha` específico, docs que apresentem o Formspree como caminho vivo.

## Mapeamento na borda

| Site / Formspree | D1 / API v3 |
|---|---|
| `avaliacoes_voluntarias` | `avaliacoes` |
| `opiniao` | `nao_vejo_problema` |
| `discriminacao` | `possivel_discriminacao` |
| `contexto` | `preciso_contexto` |
| `erro_no_texto` | `erro_texto` |
| `frase` (comentário) | `comentario` |
| `frase` (sugestão) | `texto` |
