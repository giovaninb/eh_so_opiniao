import { afterEach, describe, it } from "node:test";
import assert from "node:assert/strict";
import { tratar } from "../src/index";
import type { Env } from "../src/types";
import { FakeD1 } from "./fakeD1";

const UUID = "550e8400-e29b-41d4-a716-446655440000";
const TOKEN = "XXXX.DUMMY.TOKEN.XXXX";
const originalFetch = globalThis.fetch;

function envBase(db = new FakeD1(), extras: Partial<Env> = {}): Env {
  return {
    DB: db as unknown as D1Database,
    TURNSTILE_SECRET_KEY: "1x0000000000000000000000000000000AA",
    ALLOWED_ORIGINS: "https://giovaninb.github.io,http://127.0.0.1:4177",
    ALLOWED_HOSTNAMES: "giovaninb.github.io,localhost,127.0.0.1",
    TURNSTILE_ACTION: "participacao",
    ...extras,
  };
}

function req(corpo: unknown, opts: { origin?: string; method?: string; ct?: string; ip?: string } = {}): Request {
  const headers: Record<string, string> = {
    "content-type": opts.ct ?? "application/json",
    Origin: opts.origin ?? "https://giovaninb.github.io",
  };
  if (opts.ip) headers["CF-Connecting-IP"] = opts.ip;
  return new Request("https://eh-so-opiniao-api.workers.dev/api/v1/participacoes", {
    method: opts.method ?? "POST",
    headers,
    body: opts.method === "GET" || opts.method === "OPTIONS" ? undefined : typeof corpo === "string" ? corpo : JSON.stringify(corpo),
  });
}

const siteverifyOk = {
  success: true,
  hostname: "giovaninb.github.io",
  action: "participacao",
};

function mockVerify(payload: unknown = siteverifyOk, status = 200, throwNet = false) {
  globalThis.fetch = (async (input: RequestInfo | URL) => {
    if (String(input).includes("siteverify")) {
      if (throwNet) throw new Error("net");
      return new Response(JSON.stringify(payload), { status });
    }
    return new Response("no", { status: 404 });
  }) as typeof fetch;
}

const aval = {
  schema_version: "3",
  tipo: "avaliacoes",
  submission_id: UUID,
  aviso_versao: "2026-10-30",
  consentimento: "sim",
  turnstile_token: TOKEN,
  avaliacoes: [{
    frase_id: "EX-154",
    tema_id: "pcd",
    modo: "descobrir",
    avaliacao: "nao_vejo_problema",
    conteudo_versao: "abc123",
    contexto_exibido: true,
    analise_revelada: false,
  }],
};

afterEach(() => { globalThis.fetch = originalFetch; });

describe("API participações", () => {
  it("grava avaliações válidas", async () => {
    const db = new FakeD1();
    mockVerify();
    const r = await tratar(req(aval), envBase(db));
    assert.equal(r.status, 200);
    const j = await r.json() as { ok: boolean };
    assert.equal(j.ok, true);
    assert.equal(db.submissions.size, 1);
    assert.equal(db.evaluations.length, 1);
    assert.equal(db.evaluations[0].avaliacao, "nao_vejo_problema");
  });

  it("aceita alias opiniao e lote de 5", async () => {
    const db = new FakeD1();
    mockVerify();
    const itens = Array.from({ length: 5 }, (_, i) => ({
      frase_id: `EX-${100 + i}`,
      tema_id: "pcd",
      modo: "descobrir",
      avaliacao: "opiniao",
      conteudo_versao: "v",
    }));
    const r = await tratar(req({ ...aval, avaliacoes: itens }), envBase(db));
    assert.equal(r.status, 200);
    assert.equal(db.evaluations.length, 5);
  });

  it("rejeita lote maior que 5", async () => {
    mockVerify();
    const itens = Array.from({ length: 6 }, (_, i) => ({ frase_id: `EX-${i + 1}`, avaliacao: "opiniao" }));
    const r = await tratar(req({ ...aval, avaliacoes: itens }), envBase());
    assert.equal(r.status, 422);
  });

  it("rejeita campo desconhecido", async () => {
    mockVerify();
    const r = await tratar(req({ ...aval, email: "a@b.c" }), envBase());
    assert.equal(r.status, 422);
  });

  it("rejeita valor fora da enumeração", async () => {
    mockVerify();
    const r = await tratar(req({ ...aval, avaliacoes: [{ frase_id: "EX-1", avaliacao: "odio" }] }), envBase());
    assert.equal(r.status, 422);
  });

  it("rejeita JSON malformado", async () => {
    mockVerify();
    const r = await tratar(req("{", { ct: "application/json" }), envBase());
    assert.equal(r.status, 400);
  });

  it("rejeita consentimento ausente", async () => {
    mockVerify();
    const { consentimento: _c, ...resto } = aval;
    const r = await tratar(req(resto), envBase());
    assert.equal(r.status, 422);
  });

  it("rejeita frase_id inválido", async () => {
    mockVerify();
    const r = await tratar(req({ ...aval, avaliacoes: [{ frase_id: "../etc", avaliacao: "opiniao" }] }), envBase());
    assert.equal(r.status, 422);
  });

  it("grava contestação e sugestão", async () => {
    mockVerify();
    const db = new FakeD1();
    const c = await tratar(req({
      schema_version: "3", tipo: "contestacao", submission_id: "550e8400-e29b-41d4-a716-446655440001",
      consentimento: "sim", turnstile_token: TOKEN, frase_id: "EX-154", motivo: "erro_no_texto", comentario: "typo",
    }), envBase(db));
    assert.equal(c.status, 200);
    assert.equal(db.contestations[0].motivo, "erro_texto");
    const s = await tratar(req({
      schema_version: "3", tipo: "sugestao_frase", submission_id: "550e8400-e29b-41d4-a716-446655440002",
      consentimento: "sim", turnstile_token: TOKEN, texto: "Frase nova de teste.", interpretacao_sugerida: "preciso_contexto",
    }), envBase(db));
    assert.equal(s.status, 200);
    assert.equal(db.suggestions.length, 1);
  });

  it("idempotência no mesmo submission_id", async () => {
    mockVerify();
    const db = new FakeD1();
    const e = envBase(db);
    assert.equal((await tratar(req(aval), e)).status, 200);
    const r2 = await tratar(req(aval), e);
    assert.equal(r2.status, 200);
    assert.equal(((await r2.json()) as { idempotente: boolean }).idempotente, true);
    assert.equal(db.evaluations.length, 1);
  });

  it("falha do banco vira 503", async () => {
    mockVerify();
    const db = new FakeD1();
    db.falhar = true;
    const r = await tratar(req(aval), envBase(db));
    assert.equal(r.status, 503);
  });

  it("saúde GET não expõe dados privados", async () => {
    const r = await tratar(new Request("https://eh-so-opiniao-api.workers.dev/api/v1/saude", {
      method: "GET",
      headers: { Origin: "https://giovaninb.github.io" },
    }), envBase());
    assert.equal(r.status, 200);
    const j = await r.json() as Record<string, unknown>;
    assert.equal(j.ok, true);
    const serial = JSON.stringify(j);
    assert.equal(serial.includes("TURNSTILE"), false);
    assert.equal(serial.includes("secret"), false);
    assert.equal(Object.keys(j).join(","), "ok");
  });

  it("CORS recusa origem estranha e GET", async () => {
    mockVerify();
    const ruim = await tratar(req(aval, { origin: "https://evil.example" }), envBase());
    assert.equal(ruim.status, 403);
    assert.equal(ruim.headers.get("Access-Control-Allow-Origin"), null);
    const get = await tratar(req(aval, { method: "GET" }), envBase());
    assert.equal(get.status, 405);
    const opt = await tratar(req(null, { method: "OPTIONS" }), envBase());
    assert.equal(opt.status, 204);
    assert.equal(opt.headers.get("Access-Control-Allow-Origin"), "https://giovaninb.github.io");
    const local = await tratar(req(aval, { origin: "http://127.0.0.1:4173", method: "OPTIONS" }), envBase(new FakeD1(), {
      ALLOWED_ORIGINS: "https://giovaninb.github.io",
    }));
    assert.equal(local.status, 403);
    assert.equal(local.headers.get("Access-Control-Allow-Origin"), null);
  });

  it("rate limit 429", async () => {
    mockVerify();
    const r = await tratar(req(aval), envBase(new FakeD1(), {
      LIMITE: { limit: async () => ({ success: false }) },
    }));
    assert.equal(r.status, 429);
  });

  it("texto longo e Content-Type", async () => {
    mockVerify();
    const r = await tratar(req({
      ...aval, tipo: "sugestao_frase", texto: "x".repeat(400), interpretacao_sugerida: "opiniao",
    }), envBase());
    assert.equal(r.status, 422);
    const ct = await tratar(req(aval, { ct: "text/plain" }), envBase());
    assert.equal(ct.status, 415);
  });

  it("não guarda token Turnstile", async () => {
    mockVerify();
    const db = new FakeD1();
    await tratar(req(aval), envBase(db));
    const row = [...db.submissions.values()][0];
    assert.equal(JSON.stringify(row).includes("DUMMY"), false);
    assert.equal(JSON.stringify(db.evaluations).includes("token"), false);
  });
});

describe("Turnstile", () => {
  it("token inválido", async () => {
    mockVerify({ success: false, "error-codes": ["invalid-input-response"] });
    assert.equal((await tratar(req(aval), envBase())).status, 403);
  });
  it("token reutilizado", async () => {
    mockVerify({ success: false, "error-codes": ["timeout-or-duplicate"] });
    assert.equal((await tratar(req(aval), envBase())).status, 409);
  });
  it("hostname incorreto", async () => {
    mockVerify({ success: true, hostname: "evil.example", action: "participacao" });
    assert.equal((await tratar(req(aval), envBase())).status, 403);
  });
  it("hostname ausente", async () => {
    mockVerify({ success: true, action: "participacao" });
    assert.equal((await tratar(req(aval), envBase())).status, 403);
  });
  it("action incorreta", async () => {
    mockVerify({ success: true, hostname: "giovaninb.github.io", action: "login" });
    assert.equal((await tratar(req(aval), envBase())).status, 403);
  });
  it("API indisponível", async () => {
    mockVerify({}, 200, true);
    assert.equal((await tratar(req(aval), envBase())).status, 503);
  });
  it("ausência de secret", async () => {
    mockVerify();
    const r = await tratar(req(aval), envBase(new FakeD1(), { TURNSTILE_SECRET_KEY: "" }));
    assert.equal(r.status, 503);
  });
});
