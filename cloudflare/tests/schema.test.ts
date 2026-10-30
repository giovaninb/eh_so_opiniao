import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { validar } from "../src/validation/schema";

const base = {
  schema_version: "3",
  submission_id: "550e8400-e29b-41d4-a716-446655440000",
  consentimento: "sim",
  turnstile_token: "XXXX.DUMMY.TOKEN.XXXX",
};

describe("validar", () => {
  it("aceita sugestão canônica", () => {
    const r = validar({
      ...base,
      tipo: "sugestao_frase",
      texto: "Frase nova de teste.",
      interpretacao_sugerida: "opiniao",
    });
    assert.equal(r.ok, true);
    if (r.ok) assert.equal(r.dados.interpretacao_sugerida, "nao_vejo_problema");
  });

  it("rejeita script no texto", () => {
    const r = validar({
      ...base,
      tipo: "sugestao_frase",
      texto: "<script>x</script> frase longa o bastante",
      interpretacao_sugerida: "contexto",
    });
    assert.equal(r.ok, false);
  });

  it("rejeita honeypot", () => {
    const r = validar({
      ...base,
      tipo: "contestacao",
      frase_id: "EX-1",
      comentario: "falta contexto na análise",
      armadilha: "bot",
    });
    assert.equal(r.ok, false);
  });

  it("mapeia avaliacoes_voluntarias", () => {
    const r = validar({
      ...base,
      tipo: "avaliacoes_voluntarias",
      avaliacoes: [{ frase_id: "NX-1", avaliacao: "discriminacao" }],
    });
    assert.equal(r.ok, true);
    if (r.ok) {
      assert.equal(r.dados.tipo, "avaliacoes");
      assert.equal((r.dados.avaliacoes as { avaliacao: string }[])[0].avaliacao, "possivel_discriminacao");
    }
  });
});
