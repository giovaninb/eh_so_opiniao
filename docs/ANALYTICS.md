# Relatórios locais de participação

Os relatórios **não** vão ao GitHub Pages. Ficam em `datasets/_local/participacoes/` (ignorado pelo Git).

Não confundir submissão, avaliação e pessoa:

- 1 lote com 5 avaliações = **1 submissão** e **5 avaliações**.
- Não dá para saber quantas pessoas participaram.

Amostra voluntária e autoselecionada: não representa a população, não estima prevalência de preconceito e não diagnostica quem leu.

## Importar

Formatos: CSV (inclusive o legado `tipo,frase,avaliacao,frase_id,consentimento,site`), JSON, JSONL, `.eml` de notificação, dump D1 `{submissions,evaluations,contestations,suggestions}`.

```bash
python -m eh_so_opiniao analytics importar --arquivo caminho/exportacao.json
python -m eh_so_opiniao participacao caminho/exportacao.csv
```

O parser de `.eml` é heurístico (pares chave/valor, JSON ou URL-encoded). Sem exemplo real versionado, um formato não reconhecido é rejeitado — não inventamos campos.

Não há credencial de e-mail no código. Não há chamada à API do Formspree nem ao D1 remoto: o dump é um arquivo que você exportou com Wrangler.

```bash
# no cloudflare/, D1 local
npx wrangler d1 execute eh-so-opiniao-db --local --json --command "SELECT * FROM submissions"
```

Monte um JSON com as quatro tabelas e passe a `analytics importar`. Aliases Cloudflare (`avaliacoes`, `nao_vejo_problema`, `erro_texto`) são aceitos e gravados no vocabulário interno (`avaliacoes_voluntarias`, `opiniao`, `erro_no_texto`).

O observatório científico **não** lê o D1. Participações não entram em treino sem revisão, licença e análise de privacidade posteriores.

## Relatórios

```bash
python -m eh_so_opiniao analytics relatorio
python -m eh_so_opiniao analytics atencao
python -m eh_so_opiniao analytics retencao --dias 90
```

Saídas (padrão: `datasets/_local/participacoes/relatorios/`):

- `resumo.json` / `resumo.md` / `painel.html` / `por_frase.csv`
- `frases_em_atencao.json` — sugestões de revisão editorial, não conclusão sobre o rótulo

Limiares configuráveis no código (`LIMIAR_MIN=5`, `LIMIAR_DIVISAO=0.60`): volume mínimo antes de percentual; maioria **não** é verdade.

## Esquema

`schema_version=2` (Formspree) e `3` (Cloudflare). Tipos internos: `avaliacoes_voluntarias`, `sugestao_frase`, `contestacao`.

Registros antigos `voto` / `frase` / `discordancia` continuam válidos na importação.

Campos de uma avaliação no lote: `frase_id`, `conteudo_versao`, `tema_id`, `modo`, `avaliacao`, `contexto_exibido`, `analise_revelada`.

`conteudo_versao` é um hash SHA-256 (12 hex) do conteúdo editorial publicado. Avaliações de versões distintas da mesma frase **não** são somadas automaticamente.

## Retenção

O Formspree Free guarda 30 dias. O arquivo local também não deve reter textos originais sem necessidade. `analytics retencao` esvazia `frase` / `comentario` / `contexto` antigos e regenera os agregados.

Não envie esses arquivos a GitHub Actions, artefatos públicos ou o repositório.
