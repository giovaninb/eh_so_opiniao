export function origemPermitida(origin: string | null, lista: string): string | null {
  if (!origin) return null;
  const extras = lista.split(",").map((s) => s.trim()).filter(Boolean);
  if (extras.includes(origin)) return origin;
  return null;
}

export function cabecalhosCors(origin: string | null, lista: string): Record<string, string> {
  const ok = origemPermitida(origin, lista);
  const h: Record<string, string> = {
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "600",
    Vary: "Origin",
  };
  if (ok) h["Access-Control-Allow-Origin"] = ok;
  return h;
}
