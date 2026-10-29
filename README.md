# É Só Opinião?

*Onde termina a opinião e começa a discriminação?* — projeto da exposição **Quem Pode Pertencer?**

Duas partes, deliberadamente separadas:

1. **Observatório de pesquisa** (Python, local): integra datasets brasileiros públicos, normaliza sem fundir, treina baselines simples e mede com honestidade. Roda no seu computador; nada disso vai para a internet.
2. **Site educativo estático** (`site/`): HTML/CSS/JS puros, publicável no GitHub Pages. Só mostra frases **revisadas por pessoas**. Não executa IA e não carrega nenhum corpus científico.

O que o projeto **não** faz: identificar pessoas, inferir preferência eleitoral, concluir crime, ranquear indivíduos, vigiar alvos ou denunciar automaticamente. Pontuação de modelo não é evidência de crime.

## Fluxo

```
Dataset → Adaptador → Validação → Normalização → Mapeamento → Experimento → Avaliação → Revisão humana → Site
```

| Etapa | Onde |
|---|---|
| Catálogo (licença, acesso, riscos) | `datasets/registry.yaml` |
| Adaptadores (um por dataset, sem fusão) | `adapters/` |
| Download com cache e SHA-256 | `pipeline/download.py` |
| Esquema `NormalizedTextSample` | `schema.py` |
| Mapeamento de rótulos versionado | `datasets/label_mapping.yaml` |
| Taxonomia (supervisionada x exploratória) | `datasets/taxonomy.yaml` |
| Baselines A (regras) e B (TF-IDF) | `classifiers/` |
| Métricas e experimentos A–E e AMP-A..AMP-G | `evaluation/` |
| Revisão humana (SQLite, histórico) | `review/` |
| Publicação (só aprovados, varredura de vazamento) | `publicacao.py` |

## Instalação

```bash
git clone git@github.com:giovaninb/eh_so_opiniao.git && cd eh_so_opiniao
python3 -m venv .venv && .venv/bin/pip install -e .   # instala o pacote `eh_so_opiniao` e as dependências
```

Os comandos `python -m eh_so_opiniao ...` rodam depois do `pip install -e .` (a raiz deste repositório **é** o pacote `eh_so_opiniao`). Os dados locais ficam em `datasets/_local/` (ignorado pelo Git) ou em `ESO_DATA_DIR`.

## Comandos

```bash
python -m eh_so_opiniao datasets                 # catálogo e estado no cache
python -m eh_so_opiniao baixar                   # só datasets abertos (cache + integridade)
python -m eh_so_opiniao normalizar               # JSONL normalizado local
python -m eh_so_opiniao experimentos             # A–E; grava relatorios/experimento_*.json
python -m eh_so_opiniao experimentos --quais amp_a,amp_b,amp_c,amp_d,amp_e,amp_f,amp_g   # catálogo ampliado (ou --ampliados para A–E + AMP)
python -m eh_so_opiniao baixar --dataset multidomain_yt_toxbr --aceito-licenca           # só após ler as condições de licença (sem licença formal)
python -m eh_so_opiniao concordancia             # kappa/alfa do MultiDomainYT-ToxBR, recalculados das planilhas
python -m eh_so_opiniao sobreposicao             # textos em comum entre os corpora do cache
python -m eh_so_opiniao mapeamento               # tabela de correspondência de rótulos
python -m eh_so_opiniao casos                    # enfileira o estudo de caso como Pendente
python -m eh_so_opiniao revisao listar --estado Pendente
python -m eh_so_opiniao revisao aprovar --id FR-06 --revisor "Seu Nome" --nota "..."
python -m eh_so_opiniao revisao rejeitar|ambiguo|corrigir|historico ...
python -m eh_so_opiniao site                     # gera site/data/*.json só do que foi aprovado
python -m eh_so_opiniao site --rascunho          # + prévia LOCAL com ?rascunho=1 (não versionada)
python -m eh_so_opiniao docs                     # regenera tabelas e resultados em docs/
```

### Datasets

| Dataset | Licença | Acesso e estado |
|---|---|---|
| ToLD-Br | CC-BY-SA-4.0 | aberto, baixado e conferido por SHA-256 |
| HateBR / HateBRXplain | CC-BY-NC-4.0 | aberto, baixado e conferido por SHA-256 |
| MultiDomainYT-ToxBR (PUCRS, 2026) | **não declarada** (artigo: só fins acadêmicos) | aberto no GitHub; só baixa com `--aceito-licenca`; uso local, sem redistribuição |
| RacismoBR (UFMG, 2026) | não declarada | **`pendente_fonte`**: o repositório citado no artigo dá 404; nada é lido nem inventado |
| TuPyE | inconsistente entre cartão e componentes | só para medir sobreposição (reúne ToLD-Br e HateBR); não treina nem avalia |

A Escala de Preconceito contra Nordestinos (Psico/PUCRS) é só referência teórica para a classe exploratória `discriminacao_regional`; não é base de comentários nem gera classificador. Detalhes em [docs/DATASETS.md](docs/DATASETS.md), [docs/COMPATIBILIDADE_DATASETS.md](docs/COMPATIBILIDADE_DATASETS.md) e [docs/REFERENCIAS.md](docs/REFERENCIAS.md).

O pipeline nunca contorna controle de acesso: se um dataset futuro exigir credencial (`acesso: restrito_autorizacao`), sem `HF_TOKEN` nada é tentado e 401/403 vira `pendente_autorizacao`, sem derrubar as demais fontes.

## Revisão humana e publicação

Estados: `Pendente`, `Aprovado`, `Rejeitado`, `Ambíguo`, `Corrigido`. Toda frase entra como **Pendente**. Só `Aprovado` e `Corrigido` são publicados (`Ambíguo` só se o item permitir, e sempre rotulado como ambígua). O revisor é obrigatório e fica no histórico local; o nome **não** vai para o site.

Três camadas separadas:

| Camada | Conteúdo | Onde |
|---|---|---|
| Conteúdo público | frases aprovadas, taxonomia, catálogo, achados reais | `site/data/` (Git) |
| Dados de pesquisa | corpora, normalizados, modelos, fila de revisão | `datasets/_local/` (fora do Git) |
| Evidência original | prints/arquivos de monitoramento | nunca neste repositório |

Antes de gerar `site/data/`, uma varredura compara o texto a publicar com os corpora locais e **aborta** se achar trecho coincidente.

## Site

Mobile-first, estático (HTML, CSS e módulos JS puros, sem build, sem cookies, sem rastreamento). Cinco áreas: **Início**, **Descobrir** (uma frase de cada vez), **Explorar** (busca, filtros e links por frase), **Participar** e **Entender**/**Pesquisa**. Veja [docs/GITHUB_PAGES.md](docs/GITHUB_PAGES.md). Prévia local:

```bash
cd site && python3 -m http.server 8000   # http://localhost:8000
```

Não abra `index.html` por `file://`: o navegador bloqueia o `fetch` dos JSON.

## Documentos

- [docs/METODOLOGIA.md](docs/METODOLOGIA.md): splits, baselines, métricas, limites.
- [docs/RESULTADOS.md](docs/RESULTADOS.md): números reais (gerado).
- [docs/DATASETS.md](docs/DATASETS.md), [docs/MAPEAMENTO_ROTULOS.md](docs/MAPEAMENTO_ROTULOS.md), [docs/TAXONOMIA.md](docs/TAXONOMIA.md): gerados a partir dos YAML.
- [docs/PARTICIPACAO.md](docs/PARTICIPACAO.md): frases e leituras enviadas por visitantes (privadas até serem anonimizadas e aprovadas).
- [docs/CASOS_EDITORIAIS.md](docs/CASOS_EDITORIAIS.md): biblioteca de exemplos fictícios e revisão em lote (candidato → revisado → publicado).
- [docs/TESTES_MOBILE.md](docs/TESTES_MOBILE.md): testes de interface, matriz de telas, Lighthouse, acessibilidade e roteiro em celulares reais.
- [docs/AUDITORIA_USABILIDADE.md](docs/AUDITORIA_USABILIDADE.md): auditoria heurística e perguntas para teste com pessoas.
- [docs/LICENCAS.md](docs/LICENCAS.md), [docs/PRIVACIDADE_LGPD.md](docs/PRIVACIDADE_LGPD.md), [docs/GITHUB_PAGES.md](docs/GITHUB_PAGES.md).

## Testes

```bash
.venv/bin/python -m pytest -q
```

Usam só fixtures sintéticas em `fixtures/`; não precisam de rede nem dos corpora.

Interface (Playwright em Chromium, Firefox e WebKit, axe-core, regressão visual e Lighthouse), em `e2e/`:

```bash
cd e2e && npm install && npx playwright install chromium firefox webkit
npm test                # funcionais (usam uma biblioteca de TESTE, nunca publicada)
npm run test:visual     # regressão visual
npm run lighthouse      # Lighthouse mobile
```

Detalhes, resultados e limites (emulação não é celular real) em [docs/TESTES_MOBILE.md](docs/TESTES_MOBILE.md).

## Limitações principais

- Baseline C (transformer) é só um plano: `torch`/`transformers` não fazem parte do ambiente reprodutível e nada foi treinado.
- As frases do estudo de caso são **sintéticas e ilustrativas** (cidade não identificada); para usar frases reais, anonimize antes (sem nomes de cidades, eventos, empresas ou pessoas) e edite `casos/estudo_de_caso.yaml`.
- O site tem 79 frases de exemplo na biblioteca, mas só **11 estão aprovadas e publicadas**: as outras 68 aguardam revisão humana (veja [docs/CASOS_EDITORIAIS.md](docs/CASOS_EDITORIAIS.md)).
- O envio de frases pelo formulário está **desligado** até um serviço de recebimento real ser configurado ([docs/PARTICIPACAO.md](docs/PARTICIPACAO.md)).
- Resultados refletem datasets de outros contextos (rede social, época, tema). Não são desempenho em produção.
