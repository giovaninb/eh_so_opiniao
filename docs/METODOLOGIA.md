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
- ToLD-Br: três anotadores. Política de consenso configurável (`qualquer_voto` ≥1, `maioria` ≥2 padrão, `unanimidade` 3). `obscene` e `profanity_obscene` (OLID) ficam só como rótulo original (incompatível).
- HateBR: nome da conta e URL descartados; mantém-se apenas o hash do grupo de publicação. HateBRXplain: justificativas separadas por `;` ("n/a" = nenhuma); os offsets são derivados por busca e marcados `derivado_de_rationale`.
- OLID-BR: offsets fora do texto marcam `spans_confiaveis=False` e saem da avaliação de trechos.
- Nunca se reidentificam autores nem anotadores.

## Divisões sem vazamento

- Agrupamento por publicação (HateBR) ou por chave de quase-duplicata (ToLD-Br, OLID-BR: texto sem acento/caixa/pontuação, URLs e menções removidas).
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

Precisão, revocação e F1 por classe; macro-F1; matriz de confusão; falsos positivos/negativos; avaliação fora de domínio; curva precisão-revocação; calibração (Brier, ECE) e escolha de limiar; sempre ao lado de **chutes triviais**. Classes com menos de 30 positivos recebem aviso "não interpretar". F1 da classe positiva engana quando a prevalência é alta (OLID-BR: ~85% ofensivos); use macro-F1.

## Experimentos

- **A.** Treinar no ToLD-Br, avaliar em domínio e no OLID-BR nas classes de grupo comparáveis.
- **B.** Regras (A) vs TF-IDF (B) no HateBR; transferência HateBR → OLID-BR.
- **C.** Matriz treino × teste e efeito de combinar bases (corpora combinados só quando o rótulo é compatível).
- **D.** Neutralidade partidária: troca espelhada (Lula↔Bolsonaro etc.) nos mesmos textos, com IC95% por bootstrap; taxa de falsos positivos em comentários não ofensivos com e sem termo político. As 27 fixtures do monitor são lidas **apenas qualitativamente**.
- **E.** Destaque de trechos (F1 por token) contra spans anotados; comparação com chute aleatório e "tudo".

Destaque de trechos é auxílio de leitura, **não** explicação causal.

## Estudo de caso

`casos/estudo_de_caso.yaml`: cinco frases de exclusão, frases não discriminatórias e duas ambíguas, com um par espelho (FR-03/FR-04) para checar simetria partidária. As frases atuais são sintéticas; ver README. Todas entram **Pendentes**; só o que uma pessoa aprovar chega ao site.

## Limitações

- Domínio: textos de redes sociais, épocas e temas diferentes do contexto local.
- Rótulos humanos são ruidosos; classes raras (racismo, xenofobia) têm poucos positivos e métricas instáveis.
- Assimetria partidária observada no contrafactual (ver RESULTADOS D) é evidência de que o modelo B **não** é neutro; por isso não pode decidir nada sozinho.
- Rótulos "aproximados" combinados tendem a **piorar** o desempenho em domínio.
