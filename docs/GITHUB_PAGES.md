# Site: execução local e GitHub Pages

O site é 100% estático: `site/` (HTML, CSS, JS, JSON). Não há classificação no navegador nem servidor.

## Local

```bash
python -m eh_so_opiniao site                 # gera site/data/*.json a partir do que foi aprovado
cd site && python3 -m http.server 8000
# abra http://localhost:8000
```

Use servidor HTTP; `file://` bloqueia o `fetch` dos JSON.

Prévia com frases ainda não aprovadas (só local):

```bash
python -m eh_so_opiniao site --rascunho
# http://localhost:8000/?rascunho=1
```

`site/data/_rascunho/` está no `.gitignore`. Itens de rascunho aparecem marcados **RASCUNHO**. Nunca publique essa pasta.

## Fluxo antes de publicar

1. `python -m eh_so_opiniao casos` (ou adicione frases) → entram **Pendentes**.
2. Uma pessoa revisa: `revisao aprovar|rejeitar|ambiguo|corrigir --id ... --revisor "Nome"`.
3. `python -m eh_so_opiniao site` → só aprovados/corrigidos. A varredura de vazamento aborta se achar texto dos corpora.
4. Confira `git status`: só `site/` e documentos devem mudar; nada de `_local/`, `.parquet`, `.tab` (exceto fixtures).
5. Commit e push.

## GitHub Pages

### Opção 1: pasta do repositório (workflow)

`.github/workflows/pages.yml`:

```yaml
name: Pages
on:
  push:
    branches: [main]
    paths: ["site/**"]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
    steps:
      - uses: actions/checkout@v4
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - uses: actions/deploy-pages@v4
```

Em *Settings → Pages → Source*, escolha **GitHub Actions**. O workflow publica apenas a pasta `site/`, não o repositório inteiro.

### Opção 2: branch de publicação

Copie `site/` para a raiz de uma branch `gh-pages`. O arquivo `.nojekyll` já está na pasta.

## Cuidados

- Caminhos no site são relativos, então funcionam em `https://usuario.github.io/repositorio/`.
- O repositório precisa estar sem corpora: confira o `.gitignore` antes do primeiro commit (o diretório atual não é um repositório Git até você rodar `git init`).
- O site não deve ser indexado como prova de nada: o rodapé afirma que o conteúdo é educativo e experimental.
