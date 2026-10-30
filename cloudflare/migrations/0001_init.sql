-- Participações. Sem IP, User-Agent, e-mail, nome ou token Turnstile.
CREATE TABLE submissions (
  id TEXT PRIMARY KEY,
  tipo TEXT NOT NULL CHECK (tipo IN ('avaliacoes', 'contestacao', 'sugestao_frase')),
  schema_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  aviso_versao TEXT,
  consentimento INTEGER NOT NULL CHECK (consentimento = 1),
  estado_revisao TEXT NOT NULL DEFAULT 'recebida'
    CHECK (estado_revisao IN ('recebida', 'em_revisao', 'aceita', 'rejeitada', 'expurgada'))
);

CREATE TABLE evaluations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  submission_id TEXT NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
  frase_id TEXT NOT NULL,
  tema_id TEXT,
  modo TEXT,
  avaliacao TEXT NOT NULL CHECK (avaliacao IN ('nao_vejo_problema', 'possivel_discriminacao', 'preciso_contexto')),
  conteudo_versao TEXT,
  contexto_exibido INTEGER NOT NULL DEFAULT 0 CHECK (contexto_exibido IN (0, 1)),
  analise_revelada INTEGER NOT NULL DEFAULT 0 CHECK (analise_revelada IN (0, 1))
);
CREATE INDEX idx_eval_frase ON evaluations (frase_id);
CREATE INDEX idx_eval_tema ON evaluations (tema_id);
CREATE INDEX idx_eval_versao ON evaluations (frase_id, conteudo_versao);
CREATE INDEX idx_eval_sub ON evaluations (submission_id);

CREATE TABLE contestations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  submission_id TEXT NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
  frase_id TEXT NOT NULL,
  conteudo_versao TEXT,
  motivo TEXT CHECK (
    motivo IS NULL OR motivo IN (
      '', 'falta_contexto', 'discordo_classificacao', 'explicacao_incompleta',
      'interpretacao_excessiva', 'erro_texto', 'outro'
    )
  ),
  comentario TEXT,
  estado_revisao TEXT NOT NULL DEFAULT 'recebida'
    CHECK (estado_revisao IN ('recebida', 'em_revisao', 'aceita', 'rejeitada', 'expurgada'))
);
CREATE INDEX idx_cont_frase ON contestations (frase_id);
CREATE INDEX idx_cont_sub ON contestations (submission_id);

CREATE TABLE suggestions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  submission_id TEXT NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
  texto TEXT NOT NULL,
  interpretacao TEXT NOT NULL CHECK (interpretacao IN ('nao_vejo_problema', 'possivel_discriminacao', 'preciso_contexto')),
  contexto TEXT,
  estado_revisao TEXT NOT NULL DEFAULT 'recebida'
    CHECK (estado_revisao IN ('recebida', 'em_revisao', 'aceita', 'rejeitada', 'expurgada'))
);
CREATE INDEX idx_sug_sub ON suggestions (submission_id);
CREATE INDEX idx_sub_created ON submissions (created_at);
CREATE INDEX idx_sub_tipo ON submissions (tipo);
