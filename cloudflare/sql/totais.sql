-- Só agregados. Não seleciona texto, comentário nem IDs de visitante.
SELECT
  (SELECT COUNT(*) FROM submissions) AS submissoes,
  (SELECT COUNT(*) FROM evaluations) AS avaliacoes,
  (SELECT COUNT(*) FROM contestations) AS contestacoes,
  (SELECT COUNT(*) FROM suggestions) AS sugestoes;
