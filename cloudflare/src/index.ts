import type { Env } from "./types";
import { participacoes } from "./routes/participacoes";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    return participacoes(request, env);
  },
};

export { participacoes as tratar };
