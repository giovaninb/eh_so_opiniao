# Testes de interface, celular e acessibilidade

Tudo que está aqui foi **executado**; os números vêm de rodadas reais (data e ambiente abaixo). O que não pôde ser verificado automaticamente está listado como pendente.

> **Emulação não é dispositivo físico.** Os testes simulam tamanho de tela, toque, escala de pixels e user agent (perfis do Playwright: Pixel 7, iPhone 13). Eles **não** reproduzem teclado virtual real, barras do navegador que encolhem ao rolar, rolagem com inércia, fontes do sistema, modo escuro do aparelho, leitores de tela, nem o desempenho de um celular de entrada. WebKit aqui é o motor do Safari, não o Safari do iPhone. Use o roteiro manual no fim deste documento antes de divulgar.

## Como rodar

```bash
cd e2e
npm install                                   # uma vez
npx playwright install chromium firefox webkit  # uma vez (fica em e2e/.browsers, fora do Git)
npm test                                      # funcionais: 3 navegadores + desktop (gera os dados de TESTE antes)
npm run test:visual                           # regressão visual contra as referências versionadas
npm run visual:atualizar                      # só após revisar a mudança visual por uma pessoa
npm run lighthouse                            # Lighthouse mobile, 3 execuções por página
```

Para evitar que os testes dependam de revisão humana, a biblioteca de 79 frases usada nos testes vem de `e2e/.dados/` (gerada por `tools/gerar_dados_e2e.py` num banco temporário, com um revisor fictício `fixture-e2e`). **Esses dados nunca são publicados** e não indicam aprovação real: hoje só 11 frases estão aprovadas por uma pessoa. Os testes de conteúdo (`conteudo.spec.mjs`) rodam também sobre os dados reais de `site/data/`.

## Matriz

| Projeto | Motor | Perfil | Observação |
|---|---|---|---|
| `chromium-movel` | Chromium | Pixel 7 (toque) | e as larguras 320, 360, 375, 390, 430, 768, 1024, 1440 e 3 paisagens, definidas dentro de `layout.spec.mjs` |
| `webkit-movel` | WebKit | iPhone 13 (toque) | no macOS o `Tab` pula links (comportamento do Safari); os testes usam `Option+Tab` |
| `firefox-movel` | Firefox | 390×844 | Playwright não emula toque no Firefox; vale para layout e lógica |
| `chromium-desktop` | Chromium | 1440×900 | navegação horizontal, sem barra inferior |
| `visual` | Chromium | 360, 390, 430, 768, 1440 | capturas comparadas com `tests/__baselines__/` |

### O que cada arquivo verifica

| Arquivo | Cobertura |
|---|---|
| `navegacao.spec.mjs` | cabeçalho de uma linha, menu (abre, Esc, clique fora, ao escolher), `aria-current`, foco no título da vista, todas as rotas, teclado, link "pular para o conteúdo", navegação desktop |
| `exploracao.spec.mjs` | carregamento progressivo (12 por vez), cartão enxuto, filtros (tema, leitura), busca (acentos, caixa, caracteres especiais), ordenação, URL compartilhável, responder → revelar análise → próxima, acesso direto, frase inexistente, par espelho recebe a mesma leitura |
| `descoberta.spec.mjs` | sequência de 5 frases, progresso "N de 5", pular, ver análise sem responder, resumo final sem nota, mistura de tipos, primeira interação da home |
| `participacao.spec.mjs` | envio indisponível por padrão (nada é simulado), contador, máscara de dados, validação com foco no primeiro erro, texto preservado em erro, caracteres especiais/HTML como texto, sucesso só com confirmação do serviço, erro 500, recusa 422, falha de rede, modo opaco, campo-armadilha, limite por visita, enquete só por ação explícita |
| `conteudo.spec.mjs` | só aprovadas por humano, sem rascunho, rótulo de natureza em cada cartão, IA separada e rotulada como hipótese, sem arquivos de corpora no pacote (jsonl/csv/sqlite…), sem cidade/evento/e-mail/telefone/revisor nos arquivos publicados, sem cookies/storage/analytics/CDN/innerHTML, contagens da enquete só ≥ 10, biblioteca ≥ 60 casos com proporção de não discriminatórios e ambíguos |
| `layout.spec.mjs` | em 8 larguras + 3 paisagens × 7 telas: sem rolagem horizontal, sem elemento fora da tela, sem texto cortado, alvos de toque ≥ 44 px; barra inferior não cobre campos nem rodapé; fonte a 200 %; reflow 320×256 (equivale a 400 % de zoom); texto com espaçamento ampliado; altura curta (paisagem) |
| `acessibilidade.spec.mjs` | axe-core com as tags WCAG 2.0/2.1/2.2 A e AA em todas as telas a 390 e 1440 px e em estados (filtros, sem resultados, menu, análise revelada, erro, validação); um `h1` por tela e hierarquia sem saltos; foco visível; formulário completável só por teclado; regiões `aria-live`; sem animações longas |
| `visual.spec.mjs` | 11 cenas × 5 larguras (home, menu, biblioteca com filtros, cartão antes/depois, análise revelada, formulário indisponível/com erros/erro do serviço, vazio, erro) |

Teste de serviço de envio: o endpoint é **simulado** com `page.route` (resposta 200, 422, 500, falha de rede, resposta opaca). Isso valida o comportamento do site, **não** o serviço real. O endpoint real (Formspree) está configurado em `site/config_participacao.json`, mas os testes o mantêm bloqueado e usam a configuração "indisponível" por padrão.

## Resultados da última rodada

Ambiente: macOS 26.4 (arm64), Playwright 1.64.1, Chromium 156 (Chrome for Testing build 1248), Firefox e WebKit do Playwright, axe-core 4.14, Lighthouse 12.8.2. Rodada de 29/10/2026.

| Projeto | Passaram | Ignorados¹ | Falharam |
|---|---|---|---|
| chromium-movel | 160 | 1 | 0 |
| webkit-movel | 160 | 1 | 0 |
| firefox-movel | 160 | 1 | 0 |
| chromium-desktop | 158 | 3 | 0 |
| visual (64 referências) | 54 | 1 | 0 |
| **Total** | **692** | **7** | **0** |

¹ Ignorados de propósito: testes que só fazem sentido em celular (menu em painel) ou só em desktop (navegação horizontal).

Python: 127 testes passam (`.venv/bin/python -m pytest -q`).

O que os testes encontraram **e foi corrigido** (não passou de primeira):

- botão de menu, cartões, lista das "cinco perguntas" e barra inferior estouravam a largura com fonte a 200 % e em 320×256; corrigido com `minmax(0, 1fr)`, quebra de palavras e gutters proporcionais;
- `select` dos filtros com menos de 44 px no WebKit; corrigido com `appearance: none` e altura explícita;
- rodapé sobrepunha a barra inferior no fim da rolagem (era do teste, não do site: o teste passou a medir o último texto);
- a vista Início aparecia por um instante antes de abrir um link direto para uma frase (CLS), e o rodapé era empurrado; corrigido;
- `favicon.ico` inexistente gerava erro de console (Boas práticas 96); corrigido com ícone embutido;
- dois testes meus eram frágeis (corrida no limite de envios e `Tab` no WebKit/macOS); corrigidos sem afrouxar a verificação.

### Lighthouse (mobile)

`npm run lighthouse`. Configuração padrão de celular do Lighthouse: Moto G Power emulado, rede "Slow 4G" e CPU 4× mais lenta, **simuladas**. 3 execuções por página; vale a mediana. Servidor local (`e2e/servidor.mjs`) **com gzip**, como faz o GitHub Pages; sem CDN. O resultado em produção pode diferir. Bruto em `e2e/resultados/lighthouse.json`.

| Página | Desempenho | Acessibilidade | Boas práticas | SEO | LCP | CLS | TBT | Peso |
|---|---|---|---|---|---|---|---|---|
| Início | 100 | 100 | 100 | 100 | 1,5 s | 0 | 0 ms | 42 KB |
| Explorar (dados reais, 11 frases) | 100 | 100 | 100 | 100 | 1,5 s | 0 | 0 ms | 42 KB |
| Frase | 100 | 100 | 100 | 100 | 1,5 s | 0 | 0 ms | 42 KB |
| Participar | 100 | 100 | 100 | 100 | 1,5 s | 0 | 0 ms | 42 KB |
| Explorar (79 frases, pior caso) | 100 | 100 | 100 | 100 | 1,7 s | 0 | 0 ms | 54 KB |

Metas: desempenho ≥ 90, acessibilidade ≥ 95, boas práticas ≥ 90, LCP ≤ 2,5 s, CLS < 0,1. Atingidas em todas as páginas.

Como chegamos lá (a primeira execução não passava em tudo): sem otimização o pior caso (79 frases) deu desempenho 96 e **LCP 2,7 s (acima da meta)**, e o CLS da página de frase era 0,07. Mudanças feitas: `modulepreload` dos módulos, `preload` do JSON de frases (e cache HTTP padrão em vez de `no-cache`), espaço reservado para o cartão enquanto carrega, rodapé oculto até o conteúdo estar montado, rota interna sem flash da Início, e gzip no servidor de teste. **O gzip espelha o GitHub Pages, mas é uma diferença do ambiente de medição:** sem ele, o LCP do pior caso seria o do primeiro resultado (2,7 s). Nada foi feito para enganar a ferramenta (nenhuma auditoria foi desligada).

Ressalvas: números de laboratório com simulação não são experiência de usuários reais; 100 em um site estático pequeno é esperado e não garante bom desempenho em aparelhos de entrada com rede ruim. A auditoria `bf-cache` do Lighthouse aparece como falha no Chrome de teste e não conta na nota.

## Acessibilidade (WCAG 2.2 AA)

Automatizado (axe-core, sem violações nas 7 telas a 390 e 1440 px e nos estados interativos testados): contraste, nomes acessíveis, rótulos de formulário, `aria-*` válidos, landmarks, idioma, alvos de toque, reflow, espaçamento de texto, foco visível e alvo mínimo 24 px (2.5.8) — e o projeto adota 44 px.

O axe cobre só parte dos critérios. **Dependem de teste manual com leitor de tela e não foram verificados:**

- **VoiceOver (iPhone/Safari)** e **TalkBack (Android/Chrome)**: ordem de leitura; se o título da vista é anunciado ao mudar de rota (o foco vai ao `h2`/`h1`); se `aria-live` da contagem de resultados, do envio e da revelação da análise é lido sem repetição; se o grupo de botões "É só opinião / Pode ser discriminação / Depende do contexto" é anunciado como pressionado/não pressionado; se o botão Menu anuncia expandido/recolhido; se o contador de caracteres não é verboso demais a cada tecla.
- Rotor/lista de links no VoiceOver: cada "Ler e responder" aponta para a sua frase por `aria-describedby`, mas o rotor lista só o nome do link (todos iguais). Verificar se isso atrapalha; se sim, trocar por `aria-label` com o início da frase.
- Navegação por gestos no TalkBack com a barra inferior fixa.
- Zoom do sistema (iOS Zoom, ampliação do Android) e "Texto maior" do sistema além de 200 %.
- Modo de alto contraste/inversão de cores, e `prefers-reduced-motion` em aparelho real (o site respeita a preferência; foi testado só por emulação).

## Roteiro manual em celulares reais

Para quem for testar (Android e iPhone). **Não há resultados de usuários reais neste repositório**: o que está abaixo é só o roteiro e a lista de verificação.

Tarefas (marque tempo, se concluiu sozinho/a, onde hesitou):

1. **Responder uma frase.** "Abra o site e diga o que acha de uma frase. Depois descubra o que a revisão pensa." (esperado: chegar à análise em menos de 30 s sem ajuda.)
2. **Achar um tema.** "Encontre frases sobre racismo que *não* sejam discriminatórias e compartilhe o link de uma delas." (esperado: usar Explorar e filtros; colar o link em outro app e ele abrir na mesma frase.)
3. **Participar.** "Você ouviu uma frase que o incomodou. Tente enviá-la sem identificar ninguém." (esperado: entender a mensagem de envio indisponível hoje, ou, com serviço ativo, ver confirmação real; nunca achar que enviou sem ter enviado.)

Verificações por aparelho (Android: Chrome; iPhone: Safari — e uma vez no Chrome/Firefox do aparelho):

- [ ] Nenhuma rolagem horizontal em nenhuma tela; retrato e paisagem.
- [ ] Barra inferior não cobre botões nem o fim das páginas; com o teclado aberto no formulário, o campo e o botão continuam visíveis (barra do Safari recolhendo/expandindo não quebra o layout).
- [ ] Botões fáceis de tocar com o polegar; nenhum toque acidental em dois alvos.
- [ ] Menu abre e fecha; voltar do navegador leva à tela anterior.
- [ ] Formulário: teclado de texto com maiúscula automática; botão do teclado não envia sozinho; texto não some quando o envio falha (ligue o modo avião para testar).
- [ ] Link compartilhado de uma frase abre direto nela (WhatsApp, e-mail).
- [ ] Texto legível ao sol (contraste) e com fonte do sistema ampliada.
- [ ] Tempo de carregamento aceitável em 4G fraco.
- [ ] Modo escuro do aparelho não deixa nada ilegível (o site hoje não tem tema escuro: confira que continua legível).
- [ ] VoiceOver/TalkBack: itens da seção anterior.
