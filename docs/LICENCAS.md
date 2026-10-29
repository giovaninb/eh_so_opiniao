# Licenças e termos de uso

As informações vêm de `datasets/registry.yaml` (fonte única). Confirme sempre no repositório oficial; licenças mudam.

| Dataset | Licença declarada | Acesso no pipeline | Redistribuído aqui? |
|---|---|---|---|
| ToLD-Br | CC-BY-SA-4.0 | aberto | Não |
| HateBR / HateBRXplain | CC-BY-NC-4.0 | aberto | Não |
| MultiDomainYT-ToxBR | **não declarada** (sem arquivo LICENSE; artigo: "exclusivamente para fins acadêmicos") | aberto, com reconhecimento do operador | Não |
| RacismoBR | não declarada | `pendente_fonte` (nenhum arquivo acessível) | Não |
| TuPyE | CC-BY-4.0 no cartão, inconsistente com as licenças dos componentes (CC-BY-SA-4.0 e CC-BY-NC-4.0) | aberto, só sobreposição | Não |

## Licença não declarada: o que o pipeline faz

- As condições são registradas em `condicoes_licenca` (`datasets/registry.yaml`) **antes** de qualquer arquivo entrar no cache.
- `baixar` recusa (`pendente_licenca`) enquanto o operador não reconhecer as condições com `--aceito-licenca` (ou `ESO_ACEITE_LICENCA=<dataset>`); nada é baixado antes disso. O aceite fica no `manifest.json` local, com data e restrições.
- Sem licença formal, **nenhuma redistribuição é presumida**: o corpus, os vetores de rótulos e as planilhas de anotadores ficam só no cache local; apenas métricas agregadas são publicadas.
- Recomendação aberta: pedir aos autores uma confirmação por escrito antes de qualquer uso além da pesquisa local.
- O aceite do operador **não** é uma licença; é um registro de que as condições foram lidas.

## Implicações

- **Nenhum corpus bruto é redistribuído**, nem no Git nem no site, mesmo quando a licença permitiria.
- **Uso não comercial** (HateBR): este projeto é de pesquisa e educação sem fins comerciais. Qualquer uso comercial exige revisão das licenças.
- **Mesma licença** (ToLD-Br): derivados que redistribuam dados devem manter a licença. O projeto publica apenas métricas agregadas e frases próprias.
- **Atribuição:** as citações completas estão em `DATASETS.md` e na seção "Referências científicas" do site.

## Código e conteúdo do projeto

O código, as frases sintéticas, os textos editoriais e os cartões deste projeto não herdam a licença dos datasets, pois não os contêm. Estão sob **CC BY 4.0**, com atribuição a **Giovani Bettoni** (`linkedin.com/in/giovani-bettoni`). Ver `LICENSE`.
