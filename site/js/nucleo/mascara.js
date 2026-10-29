/* Espelho do mascaramento do servidor (anonimizacao.py). O servidor mascara de novo e uma pessoa revisa:
   isto só avisa o visitante e evita enviar dado pessoal por descuido. */
const MASCARAS = [
  ["e-mail", "[e-mail]", /\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b/g],
  ["link", "[link]", /(?:https?:\S+|www\.\S+|\b[\w-]+\.(?:com|net|org|gov|edu|me|io|ly|tv|br)\b(?:\/\S*)?)/gi],
  ["usuário", "$1[usuário]", /(^|[^\w])@\w[\w.]*/g],
  ["documento", "[documento]", /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b|\b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b/g],
  ["telefone", "$1[telefone]", /(^|[^\w])(?:\+?55[\s-]?)?(?:\(?\d{2}\)?[\s-]?)?9?\d{4}[\s-]?\d{4}(?![\w])/g],
  ["número longo", "[número]", /\d{6,}/g],
];

export function mascarar(texto) {
  let saida = (texto || "").replace(/\s+/g, " ").trim();
  const tipos = [];
  for (const [nome, marcador, padrao] of MASCARAS) {
    const antes = saida;
    saida = saida.replace(padrao, marcador);
    if (saida !== antes) tipos.push(nome);
  }
  return { texto: saida, tipos };
}
