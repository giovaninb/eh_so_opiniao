# Metodologia

Este documento descreve **como** os experimentos são feitos. Os números ficam em [RESULTADOS.md](RESULTADOS.md), gerado a partir de `relatorios/*.json`. Nada aqui é desempenho de produção.

## Princípios

1. Datasets não são fundidos. Cada um mantém seus rótulos originais (`original_labels`); o mapeamento para a taxonomia comum fica em `normalized_labels`, com relação `equivalente`, `aproximado` ou `incompatível`. Rótulo ausente é permitido e não vira "falso".
2. Taxonomia comum com duas camadas: **supervisionada** (há exemplos anotados em bases científicas) e **exploratória** (não há base anotada; serve para leitura humana, nunca para métrica). Crítica política legítima, ironia/humor e ambígua são salvaguardas.
3. Classificação serve à **triagem com revisão humana**. Não conclui crime, intenção nem identidade, e não infere preferência política.
4. A TybyrIA **não** é usada como classificador de preconceito regional ou intolerância política.
5. Experimentos reportam resultados reais, inclusive os ruins. Prototipo não é prova.

## Normalização

- Regra "primeiro vence" por alvo da taxonomia: se dois rótulos originais mapeiam ao mesmo alvo, vale o primeiro declarado em `label_mapping.yaml` (versionado).
- ToLD-Br: três anotadores. Política de consenso configurável (`qualquer_voto` ≥1, `maioria` ≥2 padrão, `unanimidade` 3). `obscene` fica só como rótulo original (incompatível).
- HateBR: nome da conta e URL descartados; mantém-se apenas o hash do grupo de publicação. HateBRXplain: justificativas separadas por `;` ("n/a" = nenhuma); os offsets são derivados por busca e marcados `derivado_de_rationale`.
- MultiDomainYT-ToxBR: o vetor de nove categorias do CSV é o consenso por maioria (≥ 2 de 3). A ordem das classes **não** é a do README (inconsistente): foi verificada contra as seis planilhas dos anotadores e é reconferida a cada normalização; se não bater, o adaptador recusa. O número de votos de cada classe e o grupo de anotadores ficam em `annotation_metadata`; a coluna `inválido` nunca vira rótulo. Todas as relações com a taxonomia são `aproximado`.
- RacismoBR: adaptador com contrato **suposto** (colunas `text`/`label`), validado só com fixtures sintéticas, porque a fonte pública não foi encontrada (`pendente_fonte`). Corpus original (1.054 derivado) e subconjunto balanceado (858) são objetos distintos e ficam separados.
- TuPyE: lida só para medir sobreposição de textos; nunca treina nem avalia.
- Nunca se reidentificam autores nem anotadores.

## Datasets do catálogo ampliado

- **Licença e proveniência primeiro.** Condições de licença, fontes verificadas e ficha científica ficam no `registry.yaml` antes da integração; sem licença formal, uso só local e acadêmico, com reconhecimento explícito do operador (ver [LICENCAS.md](LICENCAS.md)).
- **Esquema real antes do mapeamento.** Cabeçalhos e valores dos arquivos foram inspecionados antes de qualquer mapeamento; divergências (README do MultiDomainYT-ToxBR; 405 × 425 posts no artigo do RacismoBR) ficam registradas, não corrigidas em silêncio.
- **Compatibilidade.** [COMPATIBILIDADE_DATASETS.md](COMPATIBILIDADE_DATASETS.md) compara plataforma, domínio, anotação, consenso, licença, relação de cada classe e sobreposição de textos.
- **Referências.** [REFERENCIAS.md](REFERENCIAS.md) e a seção científica do site vêm da mesma fonte (`registry.yaml` + `referencias.yaml`). A Escala de Preconceito contra Nordestinos é referência teórica, nunca dataset supervisionado.

## Divisões sem vazamento

- Agrupamento por publicação (HateBR) ou por chave de quase-duplicata (ToLD-Br: texto sem acento/caixa/pontuação, URLs e menções removidas).
- Deduplicação entre splits (treino→validação/teste, validação→teste) e auditoria (`auditar_vazamento`) que precisa dar zero.
- Em avaliação entre datasets, textos presentes em mais de um corpus são excluídos do corpus de teste.
- Três sementes (13, 42, 2026). Reporta-se média ± desvio.
- Limiares são escolhidos **na validação**, nunca no teste.

## Baselines

| | Descrição |
|---|---|
| A | Léxico genérico de insultos + regras do monitor (cópia congelada em `regras_monitor/`), mapeados à taxonomia. Sem regras específicas de grupo; **declara** que não cobre racismo, xenofobia, misoginia e lgbtfobia. |
| B | TF-IDF (palavra 1–2 + caractere 3–5) com regressão logística (balanceada) ou LinearSVC. |
| C | Plano para BERTimbau/transformer. **Não executado**: sem fine-tuning pesado antes de um baseline reprodutível. |

## Métricas

Precisão, revocação e F1 por classe; macro-F1; matriz de confusão; falsos positivos/negativos; avaliação fora de domínio; curva precisão-revocação; calibração (Brier, ECE) e escolha de limiar; sempre ao lado de **chutes triviais**. Classes com menos de 30 positivos recebem aviso "não interpretar". F1 da classe positiva engana quando a prevalência é alta (no ToLD-Br, o rótulo derivado por votos tem prevalência de ~19%, o que também distorce o F1 do chute); use macro-F1 ao lado do chute trivial.

## Experimentos

- **A.** Classes de insulto e de grupo no ToLD-Br, só em domínio (é o único dataset aprovado que as anota; não há avaliação fora de domínio para elas).
- **B.** Regras (A) vs TF-IDF (B) no HateBR; transferência HateBR → ToLD-Br (rótulo `ofensivo` aproximado).
- **C.** Matriz treino × teste e efeito de combinar bases (corpora combinados só quando o rótulo é compatível).
- **D.** Neutralidade partidária: troca espelhada (Lula↔Bolsonaro etc.) nos mesmos textos, com IC95% por bootstrap; taxa de falsos positivos em comentários não ofensivos com e sem termo político. As 27 fixtures do monitor são lidas **apenas qualitativamente**.
- **E.** Destaque de trechos (F1 por token) contra os trechos derivados das justificativas do HateBRXplain; comparação com chute aleatório e "tudo". Treino e avaliação no mesmo dataset.

Destaque de trechos é auxílio de leitura, **não** explicação causal.

### Protocolos do catálogo ampliado (AMP-A a AMP-G)

Código em `evaluation/experiments_ampliados.py`; resultados em `relatorios/experimento_amp_*.json` e em [RESULTADOS.md](RESULTADOS.md). Regras comuns: resultados por dataset, por classe e por par treino × teste; **nenhuma fusão automática**; um classificador binário por classe; nenhum modelo multirrótulo cuja qualidade não tenha sido validada; suporte < 30 positivos sinalizado; textos em comum entre treino e avaliação removidos; dataset `pendente_fonte` devolve `pendente_fonte` em vez de números.

- **AMP-A.** Classificadores binários de racismo dentro do RacismoBR: subconjunto balanceado (858) e corpus original reportados separadamente, validação cruzada de 5 dobras (semente 42), chute trivial como referência. **Pendente de fonte**: só testado com fixtures sintéticas.
- **AMP-B.** Generalização treino × teste entre RacismoBR, ToLD-Br, HateBR e MultiDomainYT-ToxBR, por rótulo-alvo (`racismo`, `linguagem_ofensiva`), com a relação entre definições explícita em cada célula. A queda fora de domínio mistura definição, plataforma e época.
- **AMP-C.** Racismo explícito × implícito. Nenhum dataset traz a distinção; o protocolo gera uma folha **local** para avaliação humana e só calcula a revocação por estrato com ≥ 20 itens anotados em cada um. Nada é inferido por regra.
- **AMP-D.** Xenofobia (ToLD-Br e MultiDomainYT-ToxBR, em domínio e entre bases) e composição dos positivos por marcadores lexicais regionais e de nacionalidade. Não há rótulo de discriminação regional em nenhum dataset: o protocolo **não mede** discriminação regional.
- **AMP-E.** Falsos positivos em comentários políticos que os anotadores consideraram não tóxicos (proxy de crítica legítima, não revisão humana específica), com IC95% de Wilson, comparados aos demais negativos.
- **AMP-F.** Trechos humanos (HateBRXplain) × trechos destacados por modelos (coeficientes TF-IDF e oclusão): teto humano (anotador 1 × 2), F1 por token, ranking independente de limiar, e sensibilidade do modelo à remoção. Destaque de modelo não prova causa.
- **AMP-G.** MultiDomainYT-ToxBR: κ recalculado, desempenho por nível de acordo (AUC-ROC, revocação e taxa de FP, pois F1 depende da prevalência do estrato) e por grupo de anotadores, curva de aprendizado por número de positivos e **portão de validação por classe** (≥ 30 positivos no teste em todas as sementes e AP ≥ 2× a prevalência). O F1 binário de 0,78 do artigo não é indicador de capacidade por categoria.

## Estudo de caso

`casos/estudo_de_caso.yaml`: cinco frases de exclusão, frases não discriminatórias e duas ambíguas, com um par espelho (FR-03/FR-04) para checar simetria partidária. As frases atuais são sintéticas; ver README. Todas entram **Pendentes**; só o que uma pessoa aprovar chega ao site.

## Limitações

- Domínio: textos de redes sociais, épocas e temas diferentes do contexto local.
- Rótulos humanos são ruidosos; classes raras (racismo, xenofobia) têm poucos positivos e métricas instáveis.
- Assimetria partidária observada no contrafactual (ver RESULTADOS D) é evidência de que o modelo B **não** é neutro; por isso não pode decidir nada sozinho.
- Rótulos "aproximados" combinados tendem a **piorar** o desempenho em domínio.
- MultiDomainYT-ToxBR: sem identificador de vídeo nem domínio temático nos arquivos publicados, comentários do mesmo vídeo não podem ser agrupados no split e não há resultado por domínio; 28 textos duplicam outros (quase-duplicatas agrupadas no split).
- RacismoBR: sem arquivo, não há número real; sobreposição com ToLD-Br e TuPyE é esperada e **não foi medida**.
- TuPyE contém o ToLD-Br (100% dos textos) e 75% do HateBR: não serve para medir generalização entre eles.
