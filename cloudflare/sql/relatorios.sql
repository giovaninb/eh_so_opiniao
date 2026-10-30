-- Consultas privadas (Wrangler). Nunca expor no site público.
-- 1 submissão com 5 avaliações = 1 submission + 5 evaluations.

-- Totais
SELECT
  (SELECT COUNT(*) FROM submissions) AS submissoes,
  (SELECT COUNT(*) FROM evaluations) AS avaliacoes,
  (SELECT COUNT(*) FROM contestations) AS contestacoes,
  (SELECT COUNT(*) FROM suggestions) AS sugestoes;

-- Avaliações por frase e versão editorial
SELECT frase_id, conteudo_versao, avaliacao, COUNT(*) AS n
FROM evaluations
GROUP BY frase_id, conteudo_versao, avaliacao
ORDER BY frase_id, conteudo_versao;

-- Avaliações por tema
SELECT tema_id, avaliacao, COUNT(*) AS n
FROM evaluations
GROUP BY tema_id, avaliacao
ORDER BY tema_id;

-- Distribuição das interpretações
SELECT avaliacao, COUNT(*) AS n FROM evaluations GROUP BY avaliacao;

-- Motivos de contestação
SELECT motivo, COUNT(*) AS n FROM contestations GROUP BY motivo;

-- Sugestões pendentes
SELECT id, texto, interpretacao, contexto, estado_revisao
FROM suggestions
WHERE estado_revisao IN ('recebida', 'em_revisao')
ORDER BY id DESC;

-- Evolução temporal (dia UTC)
SELECT substr(created_at, 1, 10) AS dia, tipo, COUNT(*) AS n
FROM submissions
GROUP BY dia, tipo
ORDER BY dia;

-- Frases para revisão editorial (limiar mínimo de 8 avaliações)
-- Maioria de votos NÃO prova que a classificação editorial está errada.
SELECT
  e.frase_id,
  e.conteudo_versao,
  COUNT(*) AS n_avaliacoes,
  SUM(CASE WHEN e.avaliacao = 'possivel_discriminacao' THEN 1 ELSE 0 END) AS n_possivel_disc,
  SUM(CASE WHEN e.avaliacao = 'nao_vejo_problema' THEN 1 ELSE 0 END) AS n_sem_problema,
  SUM(CASE WHEN e.avaliacao = 'preciso_contexto' THEN 1 ELSE 0 END) AS n_contexto,
  (SELECT COUNT(*) FROM contestations c WHERE c.frase_id = e.frase_id) AS n_contestacoes
FROM evaluations e
GROUP BY e.frase_id, e.conteudo_versao
HAVING COUNT(*) >= 8
   AND (
     1.0 * SUM(CASE WHEN e.avaliacao = 'possivel_discriminacao' THEN 1 ELSE 0 END) / COUNT(*) >= 0.4
     OR (SELECT COUNT(*) FROM contestations c WHERE c.frase_id = e.frase_id) >= 3
   )
ORDER BY n_contestacoes DESC, n_avaliacoes DESC;
