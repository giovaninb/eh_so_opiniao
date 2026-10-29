# Auditoria heurística de usabilidade

**O que é:** avaliação de especialista (feita por quem implementou, com as dez heurísticas de Nielsen) sobre o site depois do redesign. **Não é teste com usuários.** Nenhum resultado de pessoas reais foi coletado; o roteiro de 3 tarefas está em [TESTES_MOBILE.md](TESTES_MOBILE.md) e precisa ser aplicado em celulares reais. Quem implementa tende a achar o próprio trabalho claro: trate esta lista como ponto de partida para o teste, não substituto.

## Diagnóstico do que existia (antes)

| Problema | Efeito provável no celular |
|---|---|
| Cabeçalho com 8 links em duas linhas | ocupa a primeira tela, nada indica o destino principal |
| Cartões densos com análise, rótulos e metadados juntos | leitura longa antes de qualquer ação |
| Formulário de participação burocrático (avisos primeiro) | desistência antes de começar |
| Apenas 11 frases | pouco a explorar, sensação de site "acabado" |
| Sem busca, filtro nem links por frase | impossível compartilhar ou achar um tema |

## Heurísticas

| # | Heurística | Estado | Evidência / risco |
|---|---|---|---|
| 1 | Visibilidade do estado | atende | progresso "3 de 5"; contagem de resultados em região `aria-live`; item atual da navegação com `aria-current`; botão de envio desabilitado enquanto envia |
| 2 | Linguagem do usuário | atende, com ressalva | textos curtos, sem jargão; "baseline", "rótulo" e "taxonomia" ainda aparecem em Pesquisa (público técnico). Verificar com leigos se "Pode ser discriminação" é entendido sem viés |
| 3 | Controle e liberdade | atende | pular qualquer frase, ver análise sem responder, limpar filtros, voltar à biblioteca, Esc fecha o menu |
| 4 | Consistência | atende | um só padrão de cartão (lista, descoberta, frase e home); mesmos três botões de resposta em todo lugar |
| 5 | Prevenção de erros | atende | contador de caracteres, máscara de dados com aviso antes do envio, consentimento explícito, armadilha anti-robô, limite por visita |
| 6 | Reconhecimento em vez de memória | atende | filtros mostram o que está ativo ("Filtros (2 ativos)"); exemplo do formato no formulário |
| 7 | Flexibilidade e eficiência | parcial | links diretos e filtros compartilháveis; não há atalhos de teclado nem "favoritos" (de propósito: nada fica no navegador) |
| 8 | Design estético e minimalista | atende | hero curto, uma ação principal por tela, análise só depois da escolha. **Risco:** a Início tem muitas seções abaixo da dobra; medir se alguém rola até "O que você quer fazer?" |
| 9 | Ajudar a reconhecer e recuperar de erros | atende | mensagens junto do campo, foco no primeiro erro, texto preservado quando o envio falha, estado vazio com "limpar filtros", frase inexistente com caminho de volta |
| 10 | Ajuda e documentação | atende | "Entender" (5 perguntas), metodologia recolhível na participação, "o que fazer diante de discurso de ódio" |

## Decisões de UX (e por quê)

- **Responder antes de ver a análise.** A pergunta "O que você acha desta frase?" vem primeiro porque a reflexão ativa ensina mais que a leitura passiva; mas há "ver análise sem responder" para não obrigar. Hipótese a validar: se o atrito reduz quem lê.
- **Nunca "certo/errado".** A análise se chama "a leitura da revisão" e o texto admite que pode divergir da pessoa; sem pontos, nota nem ranking. Evita transformar o tema em jogo de acertar e a revisão em autoridade absoluta.
- **Ambíguo é resposta legítima**, com filtro próprio.
- **Barra inferior de 4 destinos + menu**: alcance do polegar; os outros destinos ficam no menu. Em telas ≥ 960 px vira navegação horizontal.
- **Formulário imediato, privacidade em duas camadas**: o essencial (vai a uma pessoa, é mascarada, não pedimos nome, o serviço pode registrar IP) fica visível; o detalhe fica recolhível, mas acessível antes do envio.
- **Envio indisponível é dito claramente**, em vez de um formulário que finge funcionar.

## Perguntas que o teste real precisa responder

1. As pessoas encontram "Descobrir" e "Explorar" sem ajuda? Sabem a diferença?
2. "Pode ser discriminação" soa como acusação a quem fala? Alguém lê "É só opinião" como a resposta "errada"?
3. Quanto tempo até a primeira análise revelada? Alguém abandona na pergunta?
4. O aviso de privacidade resumido é suficiente, ou as pessoas esperam mais antes de escrever?
5. No celular real, o teclado esconde o botão de envio? A barra inferior atrapalha?
