export const AVALIACOES = [
  { valor: "opiniao", rotulo: "Não vejo problema", curto: "não vê problema" },
  { valor: "discriminacao", rotulo: "Pode ser desrespeitosa ou discriminatória", curto: "pode ser desrespeitosa" },
  { valor: "contexto", rotulo: "Preciso de mais contexto", curto: "precisa de mais contexto" },
];
export const NOME_AVALIACAO = Object.fromEntries(AVALIACOES.map((a) => [a.valor, a.curto]));

export const LEITURA_HUMANA = {
  exclusao: "Frase discriminatória explícita: atinge pessoas, não só ideias.",
  nao_discriminatoria: "Sem discriminação identificável.",
  ambigua: "A leitura depende de um contexto que esta frase, sozinha, não traz.",
};

export const NATUREZA = {
  ficticio: { rotulo: "Exemplo fictício", aviso: "Esta frase foi escrita pela equipe para fins educativos. Não é fala de uma pessoa real." },
  adaptado: { rotulo: "Exemplo adaptado", aviso: "Esta frase foi adaptada e anonimizada a partir de uma situação fornecida. Não identifica ninguém." },
  documentado: { rotulo: "Caso documentado", aviso: "Esta frase vem de um caso documentado, anonimizado antes da publicação." },
  contribuicao: { rotulo: "Contribuição de visitante", aviso: "Esta frase foi enviada por um visitante e reescrita por uma pessoa da equipe para não identificar ninguém." },
};

export const AUTORIA = {
  nome: "Giovani Bettoni",
  licenca: "CC BY 4.0",
  linha: "CC BY 4.0 · Giovani Bettoni",
  linkedin: "linkedin.com/in/giovani-bettoni",
};

export const LIMITE_MIN = 10;
export const LIMITE_MAX = 280;
export const TAMANHO_SESSAO = 5;
export const PAGINA = 12;
export const MAX_ENVIOS_POR_VISITA = 3;
export const TEMPO_ENVIO_MS = 15000;
