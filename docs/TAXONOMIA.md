<!-- GERADO AUTOMATICAMENTE por `python -m eh_so_opiniao docs`. Não edite à mão. -->

# Taxonomia (versão 1.2.0)

- **supervisionado**: há rótulo anotado por humanos em dataset catalogado que se relaciona com a classe.
- **exploratorio**: não há rótulo anotado; só regras e revisão humana. Resultado é hipótese, não medição.
- **salvaguarda**: evita confundir crítica política legítima, ironia ou ambiguidade com discriminação.

Nenhuma classe afirma crime, intenção ou identidade de autor. `possivel_assedio_eleitoral_contextual` só faz sentido com contexto laboral.

| Classe | Tipo | Definição | Não é |
|---|---|---|---|
| `linguagem_ofensiva` | supervisionado | Texto com insulto, xingamento ou linguagem que ofende, sem exigir alvo de grupo. | Crítica dura e fundamentada a ideias, decisões públicas ou políticas. |
| `insulto_hostilidade` | supervisionado | Ataque pessoal ou desqualificação dirigida a uma pessoa ou grupo. | Discordância educada, ainda que veemente. |
| `racismo` | supervisionado | Preconceito ou ódio com base em raça, cor ou etnia. | Menção neutra a raça/etnia ou denúncia de racismo. |
| `xenofobia` | supervisionado | Hostilidade contra pessoas por origem estrangeira ou, conforme a fonte, regional. | Piada sem alvo depreciativo ou comparação cultural neutra. |
| `misoginia` | supervisionado | Ódio, desprezo ou estereótipo depreciativo contra mulheres por serem mulheres. | Crítica a uma mulher específica por seus atos públicos. |
| `intolerancia_religiosa` | supervisionado | Ataque, zombaria ou desvalorização de pessoas por suas crenças ou pela religião que praticam. | Crítica a ideias, instituições ou líderes religiosos sem depreciar as pessoas que creem. |
| `capacitismo` | supervisionado | Zombaria, menosprezo ou desumanização de pessoas com deficiência, inclusive como insulto disfarçado. | Menção neutra a deficiência ou denúncia de capacitismo. |
| `lgbtfobia` | supervisionado | Hostilidade contra pessoas por orientação sexual ou identidade de gênero. | Menção neutra ou denúncia de LGBTfobia. |
| `transfobia` | exploratorio | Hostilidade, desvalorização ou exclusão de pessoas trans (travestis, mulheres e homens trans, pessoas não binárias) por sua identidade de gênero, inclusive negar nome, pronome ou identidade. | Pergunta respeitosa de quem quer aprender, relato de pessoa trans sobre a própria vivência (como "sinto que nasci no corpo errado"), ou denúncia que cita o termo ofensivo para combatê-lo. |
| `idadismo` | exploratorio | Estereótipo, desvalorização, infantilização ou exclusão de pessoas pela idade, em geral pessoas idosas. | Oferta de ajuda perguntada com respeito, adaptação de interface para quem precisa ou menção neutra à idade. |
| `estereotipos_masculinidade` | exploratorio | Cobrança de virilidade, repressão emocional ou papéis rígidos impostos a homens e meninos, inclusive usando o feminino como ofensa. | Misoginia (desprezo ou ódio contra mulheres) nem violência jurídica por si só; também não é cuidado ou apoio emocional a homens. |
| `hostilidade_politica` | supervisionado | Ofensa dirigida a pessoas por posição política ou ideológica. | Crítica política legítima a ideias, partidos, governos e candidaturas. |
| `discriminacao_regional` | exploratorio | Generalização depreciativa sobre pessoas de uma região, cidade ou território. | Comparação de indicadores regionais com fonte e sem desqualificar pessoas. |
| `desumanizacao` | exploratorio | Comparar pessoas ou grupos a animais, pragas, doenças ou objetos. | Metáfora com objeto não humano claramente ficcional. |
| `exclusao_social_territorial` | exploratorio | Defender que pessoas "não pertencem", devem sair, ser expulsas ou ser excluídas de espaços. | Opinião sobre política pública de ocupação do território sem alvo pessoal. |
| `estigmatizacao_socioeconomica` | exploratorio | Atribuir defeitos morais a pessoas por renda, benefício social ou classe. | Debate sobre desenho de políticas sociais. |
| `incitacao_violencia` | supervisionado | Convocar, desejar ou ameaçar dano físico a pessoas ou grupos. | Hipérbole claramente fora de contexto real ou citação em denúncia. |
| `possivel_assedio_eleitoral_contextual` | exploratorio | Indício de coação, promessa, ameaça ou discriminação em contexto de trabalho/emprego ligado a voto. Exige contexto laboral; texto isolado nunca basta. | Opinião política, provocação partidária ou xingamento sem vínculo laboral. |
| `critica_politica_legitima` | salvaguarda | Crítica a ideias, partidos, governos e candidaturas, ainda que dura. |  |
| `ironia_humor` | salvaguarda | Texto cujo sentido depende de ironia, sarcasmo ou humor. |  |
| `ambigua` | salvaguarda | Não é possível decidir sem contexto adicional. Resposta legítima e esperada. |  |
