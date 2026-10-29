# Compartilhamento, páginas estáticas e comparações

Como cada caso ganha um endereço estável com prévia própria em redes sociais, como a imagem para Status e Stories é gerada e o que falta decidir. Tudo aqui roda em HTML, CSS e JavaScript simples; o observatório em Python é independente do site público.

## Endereço de cada caso

- Cada frase **publicada** tem uma página estática em `site/casos/<id-em-minúsculas>/index.html` (ex.: `/casos/ex-01/`). Ela traz título, descrição, `canonical`, Open Graph e Twitter Card, a frase, a leitura da revisão em `<details>` e um link para a versão interativa. Funciona **sem JavaScript**.
- Com JavaScript, a página leva a pessoa a `#/frase/<ID>` (a experiência interativa). `?estatico=1` desativa o redirecionamento (usado nos testes).
- O botão WhatsApp, "Copiar link" e o menu nativo compartilham **esse endereço**, não o `#/frase/...`, porque o WhatsApp e outras redes **não executam JavaScript** ao montar a prévia.
- Não existe página para frase Pendente, Rejeitada ou Retirada. Frase com `aviso_conteudo` **nunca é citada** no título, na descrição nem na imagem de prévia.
- `site/sitemap.xml` lista só o que está publicado. `site/robots.txt` aponta para ele. `site/og/padrao.png` (1200×630) é a imagem padrão de prévia (`node e2e/gerar-og.mjs`).

### O que acontece com links antigos

`casos/registro_publicacao.json` (versionado) lembra todo id já publicado. Se um caso for rejeitado, retirado ou deixar de estar publicado, o endereço **não vira 404**: `site/casos/<id>/index.html` passa a ser uma página curta com `noindex`, sem o conteúdo, que explica que o caso foi retirado ou revisado. Se o caso for **corrigido**, a mesma página passa a mostrar o texto corrigido e o endereço permanece. Voltar a publicar remove o aviso.

## Mensagem do WhatsApp

> Essa frase parece comum, mas o contexto pode mudar a interpretação. Onde você coloca a linha? Veja a análise no É Só Opinião?: https://giovaninb.github.io/eh_so_opiniao/casos/ex-01/

É uma pergunta, sem rótulo e sem a frase no texto: a **prévia do link** é que mostra a frase (exceto as com aviso). Nenhum envio acontece até a pessoa tocar num botão. Não há rastreador: o site **não sabe** se alguém abriu o WhatsApp, e tocar no botão não prova que houve compartilhamento.

## Imagem para Status e Stories

Na página de cada frase, "Imagem para Status ou Stories" gera no aparelho, em `canvas`, um PNG de **1080×1920** (Stories/Status) ou **1200×630** (prévia). A miniatura na tela é menor de propósito: no celular, copiar a imagem da página pega o arquivo cheio e o recorte visual, e o WhatsApp recebe duas imagens. Use **Salvar imagem**, **Copiar imagem** ou **Compartilhar imagem**. O compartilhamento manda só o arquivo, sem o texto do link, para o WhatsApp não anexar também a prévia da página. Traz "Exemplo fictício · conteúdo educativo", a pergunta, o endereço curto do caso e o nome do projeto. Nenhum serviço externo é usado; frases com aviso de conteúdo não aparecem na imagem, e o texto alternativo diz isso.

## Duas frases, uma diferença

- Pares em `casos/pares.yaml` (13 propostas, P-01..P-13). Cada um aponta para duas frases já existentes e traz um texto editorial `diferenca` e um `limite` (o que a comparação **não** prova). Os títulos não revelam a leitura.
- Os 13 pares foram revisados e aprovados por Giovani Bettoni em 2026-10-29 (`casos/pares_revisao.json`). Um par só vai ao site com revisão humana do par **e** as duas frases publicadas:
  `python -m eh_so_opiniao pares listar` · `pares aprovar --id P-03 --revisor NOME` · `pares retirar --id P-03` · depois `python -m eh_so_opiniao site`.
- No celular as frases ficam empilhadas; a partir de 720 px, lado a lado. A leitura de cada frase abre em `<details>`; a diferença só aparece ao tocar "Ver o que muda". Cada par tem URL (`#/comparar/p-03`) e página estática (`/comparar/p-03/`, com Open Graph). Sem pares revisados, o atalho some e a rota explica por quê.

## "Discordo da interpretação"

Aparece na análise de cada frase **só se houver serviço de recebimento real** (`config_participacao.json`, hoje o mesmo formulário privado de "Participe"). Envia `tipo=discordancia`, `frase_id`, o comentário (mascarado: e-mail, telefone, @, links, documentos) e a leitura escolhida, com consentimento explícito e armadilha anti-robô. Nunca simula envio, avisa quando o serviço não permite confirmar o recebimento e jamais abre issue pública. É lido por uma pessoa; não há resposta individual.

## Métricas e privacidade

**Nenhum contador foi instalado.** Não há infraestrutura de medição agregada sem rastreador no GitHub Pages, e a regra do projeto é não usar cookies, fingerprinting nem gravação de sessão (o teste `test_eso_revisao_site.py` proíbe analytics, cookies e armazenamento local). Opções documentadas para o futuro: (1) contagem agregada no lado do servidor de um serviço de formulário já usado, sem identificador; (2) logs de acesso do CDN, só agregados. Qualquer uma exige decisão e aviso de privacidade antes. Limites: abrir uma página não é compartilhamento, e toque em "WhatsApp" também não.

## Qualidade medida

Medições de **2026-10-29**, neste Mac (Playwright 1.x com Chromium, WebKit e Firefox):

| Verificação | Resultado |
|---|---|
| `pytest` | 265 passaram, 0 falharam |
| Playwright funcional (chromium-movel/Pixel 7, webkit-movel/iPhone 13, firefox-movel, chromium-desktop) | 905 passaram, 0 falharam, 7 ignorados (cenários só de desktop ou só de celular) |
| Visual (390 px de base + 360/430/768/1440) | 64 passaram, 1 ignorado |
| Larguras exercidas nas telas novas | 320, 360, 375, 390, 430, 768, 1024, 1440 (sem rolagem horizontal; alvos ≥ 44 px) |
| axe (WCAG 2.2 AA) | 390 e 1440 px: home, comparação revelada, imagem gerada e demais rotas: 0 violações detectáveis |

Lighthouse mobile (mediana de 3, Slow 4G e CPU 4× simulados, servidor local com gzip): home, explorar, frase, participar e comparação **desempenho 98–99, acessibilidade 100, boas práticas 100, SEO 100**, CLS 0, TBT 0 ms, LCP 2,1–2,3 s (meta ≤ 2,5 s). Página estática de caso: desempenho 100, acessibilidade 100, **boas práticas 96**, SEO 100, LCP 0,9 s. Metas atingidas; resultado de laboratório, não de usuários reais. Dados completos em `e2e/resultados/`.

Testes novos: `tests/test_eso_paginas.py` (17), `e2e/tests/produto.spec.mjs`. Os testes de segurança de publicação checam que não há página para NX-*, que nenhuma página cita revisor/corpus e que frase com aviso não é citada na prévia.

**Limite conhecido:** axe cobre só a parte automatizável da WCAG. Falta teste manual com VoiceOver (iOS/macOS) e TalkBack (Android), com fonte do sistema ampliada, e validação em aparelhos reais. Checklist em [TESTES_MOBILE.md](TESTES_MOBILE.md). Rodando todas as suítes em paralelo numa máquina sobrecarregada vários testes estouraram o tempo; com a máquina livre passaram, o que indica carga do ambiente e não falha do site.

## Como publicar e validar

1. `python -m eh_so_opiniao site` (gera `site/data`, `site/casos/*`, `sitemap.xml`, `robots.txt`).
2. `git add site casos/registro_publicacao.json` e `git push`. O workflow publica só `site/`.
3. Validar a prévia do WhatsApp: abra `https://giovaninb.github.io/eh_so_opiniao/casos/ex-01/` num chat consigo mesmo e confira título, descrição e imagem. O WhatsApp guarda a prévia em cache; se mudar o texto, use `?v=2` ao testar. Validadores: depurador de compartilhamento do Facebook e o inspetor de cartões do Twitter.
4. Para adicionar casos sem quebrar URLs: aprove (`revisao aprovar`/`lote`), rode `site`, publique. Ids antigos permanecem estáveis; nunca renomeie um id.

## Pendências (precisam de pessoas ou de decisão)

- Nada pendente de revisão editorial: os 423 NX-* e os 13 pares já foram decididos.
- **Páginas temáticas indexáveis** (capacitismo, bifobia, etarismo, racismo velado, transfobia, "crítica × generalização", expressões do dia a dia, monogamia × não monogamia consensual × infidelidade): exigem texto editorial e referências revisados. Não foram escritas para não publicar conteúdo sem revisão nem criar páginas quase duplicadas.
- **QR code**: não implementado para evitar dependência; qualquer gerador externo serve para os endereços `/casos/<id>/`, e a página estática é a melhor página de destino.
- "Já ouvi isso" (busca por expressão) e filtros por ambiente do dia a dia: dependem de metadados extras por frase.
- Protocolo de avaliação de compreensão (voluntário, sem nota individual), histórias autorizadas e materiais educativos (P2): só contratos de dados e documentação; nada coletado.
- Teste manual com leitores de tela e em aparelhos reais; decisão sobre métricas agregadas.
