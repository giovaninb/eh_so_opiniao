export type Tipo = "avaliacoes" | "contestacao" | "sugestao_frase";
export type Avaliacao = "nao_vejo_problema" | "possivel_discriminacao" | "preciso_contexto";
export type Motivo =
  | "falta_contexto"
  | "discordo_classificacao"
  | "explicacao_incompleta"
  | "interpretacao_excessiva"
  | "erro_texto"
  | "outro";

export type Env = {
  DB: D1Database;
  LIMITE?: { limit(opts: { key: string }): Promise<{ success: boolean }> };
  TURNSTILE_SECRET_KEY: string;
  ALLOWED_ORIGINS: string;
  ALLOWED_HOSTNAMES: string;
  TURNSTILE_ACTION: string;
};

export type ErroCodigo =
  | "validacao"
  | "turnstile"
  | "rede"
  | "indisponivel"
  | "duplicado"
  | "abuso"
  | "payload"
  | "metodo";
