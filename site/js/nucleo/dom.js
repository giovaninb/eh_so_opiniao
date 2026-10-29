/* Helpers de DOM. Todo texto entra por textContent: nada de HTML vindo de dados. */

export function el(tag, atributos = {}, filhos = []) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(atributos)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "text") e.textContent = v;
    else if (k === "class") e.className = v;
    else if (k.startsWith("on") && typeof v === "function") e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const f of [].concat(filhos)) if (f !== null && f !== undefined && f !== false) e.append(f);
  return e;
}

export function limpar(no, ...filhos) {
  no.replaceChildren(...filhos.flat().filter(Boolean));
}

let contador = 0;
export function idUnico(prefixo = "id") {
  contador += 1;
  return `${prefixo}-${contador}`;
}

/** Move o foco sem rolar de modo brusco; útil depois de trocar de vista ou de frase. */
export function focar(no) {
  if (!no) return;
  if (!no.hasAttribute("tabindex")) no.setAttribute("tabindex", "-1");
  no.focus({ preventScroll: false });
}
