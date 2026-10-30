type Linha = Record<string, unknown>;

class Stmt {
  sql: string;
  db: FakeD1;
  params: unknown[];
  constructor(sql: string, db: FakeD1, params: unknown[] = []) {
    this.sql = sql;
    this.db = db;
    this.params = params;
  }
  bind(...p: unknown[]): Stmt {
    return new Stmt(this.sql, this.db, p);
  }
  async first<T>(): Promise<T | null> {
    const r = this.db.executar(this.sql, this.params);
    return (r[0] as T) || null;
  }
  async run(): Promise<{ success: boolean }> {
    this.db.executar(this.sql, this.params);
    return { success: true };
  }
}

export class FakeD1 {
  submissions = new Map<string, Linha>();
  evaluations: Linha[] = [];
  contestations: Linha[] = [];
  suggestions: Linha[] = [];
  falhar = false;

  prepare(sql: string): Stmt {
    return new Stmt(sql, this);
  }

  async batch(stmts: { run(): Promise<unknown> }[]): Promise<unknown[]> {
    if (this.falhar) throw new Error("d1");
    const out = [];
    for (const s of stmts) out.push(await s.run());
    return out;
  }

  executar(sql: string, p: unknown[]): Linha[] {
    if (this.falhar) throw new Error("d1");
    const s = sql.replace(/\s+/g, " ").trim();
    if (s.startsWith("SELECT id FROM submissions")) {
      const row = this.submissions.get(String(p[0]));
      return row ? [row] : [];
    }
    if (s.startsWith("INSERT INTO submissions")) {
      const id = String(p[0]);
      if (this.submissions.has(id)) throw new Error("UNIQUE");
      this.submissions.set(id, {
        id, tipo: p[1], schema_version: p[2], created_at: p[3], aviso_versao: p[4], consentimento: 1, estado_revisao: "recebida",
      });
      return [];
    }
    if (s.startsWith("INSERT INTO evaluations")) {
      this.evaluations.push({
        submission_id: p[0], frase_id: p[1], tema_id: p[2], modo: p[3], avaliacao: p[4],
        conteudo_versao: p[5], contexto_exibido: p[6], analise_revelada: p[7],
      });
      return [];
    }
    if (s.startsWith("INSERT INTO contestations")) {
      this.contestations.push({
        submission_id: p[0], frase_id: p[1], conteudo_versao: p[2], motivo: p[3], comentario: p[4],
      });
      return [];
    }
    if (s.startsWith("INSERT INTO suggestions")) {
      this.suggestions.push({
        submission_id: p[0], texto: p[1], interpretacao: p[2], contexto: p[3],
      });
      return [];
    }
    throw new Error(`SQL não mockado: ${s}`);
  }
}
