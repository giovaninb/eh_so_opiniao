import type { Env } from "../types";

export async function jaExiste(db: D1Database, id: string): Promise<boolean> {
  const r = await db.prepare("SELECT id FROM submissions WHERE id = ?").bind(id).first<{ id: string }>();
  return !!r;
}

export async function gravar(env: Env, dados: Record<string, unknown>, createdAt: string): Promise<"nova" | "idempotente"> {
  const id = String(dados.submission_id);
  if (await jaExiste(env.DB, id)) return "idempotente";

  const stmts: D1PreparedStatement[] = [
    env.DB.prepare(
      "INSERT INTO submissions (id, tipo, schema_version, created_at, aviso_versao, consentimento, estado_revisao) VALUES (?, ?, ?, ?, ?, 1, 'recebida')",
    ).bind(id, dados.tipo, dados.schema_version, createdAt, dados.aviso_versao || ""),
  ];

  if (dados.tipo === "avaliacoes") {
    for (const a of dados.avaliacoes as Record<string, unknown>[]) {
      stmts.push(env.DB.prepare(
        "INSERT INTO evaluations (submission_id, frase_id, tema_id, modo, avaliacao, conteudo_versao, contexto_exibido, analise_revelada) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
      ).bind(id, a.frase_id, a.tema_id, a.modo, a.avaliacao, a.conteudo_versao, a.contexto_exibido, a.analise_revelada));
    }
  } else if (dados.tipo === "contestacao") {
    stmts.push(env.DB.prepare(
      "INSERT INTO contestations (submission_id, frase_id, conteudo_versao, motivo, comentario, estado_revisao) VALUES (?, ?, ?, ?, ?, 'recebida')",
    ).bind(id, dados.frase_id, dados.conteudo_versao, dados.motivo, dados.comentario));
  } else {
    stmts.push(env.DB.prepare(
      "INSERT INTO suggestions (submission_id, texto, interpretacao, contexto, estado_revisao) VALUES (?, ?, ?, ?, 'recebida')",
    ).bind(id, dados.texto, dados.interpretacao_sugerida, dados.contexto));
  }

  try {
    await env.DB.batch(stmts);
  } catch (e) {
    if (await jaExiste(env.DB, id)) return "idempotente";
    throw e;
  }
  return "nova";
}
