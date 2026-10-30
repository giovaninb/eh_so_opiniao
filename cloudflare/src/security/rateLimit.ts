/** Limite aproximado e por localidade Cloudflare — não é cota global. Não grava IP no D1. */

export async function dentroDoLimite(
  limiter: { limit(opts: { key: string }): Promise<{ success: boolean }> } | undefined,
  chave: string,
): Promise<boolean> {
  if (!limiter) return true;
  try {
    const { success } = await limiter.limit({ key: chave });
    return success;
  } catch {
    return true;
  }
}

export async function chaveAbuso(ip: string | null): Promise<string> {
  const bruto = ip && ip.trim() ? ip.trim() : "local";
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`participacao:${bruto}`));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 16);
}
