/* Defesas contra envio automático no navegador. Não identificam a pessoa e não param um POST direto ao serviço.
   O site estático continua no ar mesmo se as contribuições forem suspensas. */

export function guardaInteracao(...elementos) {
  let ok = false;
  const marcar = () => { ok = true; };
  for (const el of elementos) {
    if (!el) continue;
    el.addEventListener("input", marcar);
    el.addEventListener("change", marcar);
    el.addEventListener("paste", marcar);
  }
  return { ok: () => ok, marcar, reset: () => { ok = false; } };
}

export function hashCorpo(texto) {
  let h = 2166136261;
  for (let i = 0; i < texto.length; i++) {
    h ^= texto.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16);
}
