-- Exclusão administrativa de uma participação (substitua o id).
-- Filhos primeiro: o D1 pode não aplicar ON DELETE CASCADE se foreign_keys estiver off.
-- DELETE FROM evaluations WHERE submission_id = 'UUID';
-- DELETE FROM contestations WHERE submission_id = 'UUID';
-- DELETE FROM suggestions WHERE submission_id = 'UUID';
-- DELETE FROM submissions WHERE id = 'UUID';
SELECT 'edite este arquivo com o UUID alvo; não execute em branco' AS aviso;
