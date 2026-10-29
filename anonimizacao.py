"""Anonimização de frases enviadas por visitantes.

Duas camadas, e nenhuma substitui a revisão humana:
1. `mascarar`: troca por marcadores o que é identificável de forma mecânica (link, e-mail, @usuário,
   telefone, documento). É feita na importação, de modo que o texto original NÃO é guardado.
2. `alertas`: aponta o que a máquina não resolve (possíveis nomes próprios) para a pessoa revisora decidir.

Mascarar não garante anonimato: nomes, apelidos, cidades, empresas e eventos exigem olhar humano.
"""

from __future__ import annotations

import re

LIMITE_MIN = 10
LIMITE_MAX = 280

# Ordem importa: e-mail antes de link (senão sobra 'ana@'), ambos antes de @usuário; documento antes de telefone.
_PADROES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("e-mail", "[e-mail]", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("link", "[link]", re.compile(r"(?:https?:\S+|www\.\S+|\b[\w-]+\.(?:com|net|org|gov|edu|me|io|ly|tv|br)\b(?:/\S*)?)", re.I)),
    ("usuário", "[usuário]", re.compile(r"(?<![\w])@\w[\w.]*")),
    ("documento", "[documento]", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b|\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")),
    ("telefone", "[telefone]", re.compile(r"(?<![\w])(?:\+?55[\s-]?)?(?:\(?\d{2}\)?[\s-]?)?9?\d{4}[\s-]?\d{4}(?![\w])")),
    ("número longo", "[número]", re.compile(r"\d{6,}")),
)

# Palavra capitalizada no meio da frase (fora do início e depois de pontuação final): possível nome próprio.
_CAPITALIZADA = re.compile(r"(?<=[a-zà-ÿ,;])\s+([A-ZÀ-Ý][a-zà-ÿ]{2,}(?:\s+[A-ZÀ-Ý][a-zà-ÿ]{2,})*)")
_MARCADORES = {"[link]", "[e-mail]", "[usuário]", "[documento]", "[telefone]", "[número]"}


def normalizar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", (texto or "")).strip()


def mascarar(texto: str) -> tuple[str, list[str]]:
    """Retorna (texto mascarado, tipos de dado encontrados)."""
    saida = normalizar_espacos(texto)
    achados: list[str] = []
    for nome, marcador, padrao in _PADROES:
        saida, n = padrao.subn(marcador, saida)
        if n:
            achados.append(nome)
    return saida, achados


def identificaveis(texto: str) -> list[str]:
    """Tipos de dado identificável AINDA presentes no texto (ignora os marcadores já aplicados)."""
    sem_marcadores = texto
    for m in _MARCADORES:
        sem_marcadores = sem_marcadores.replace(m, " ")
    return mascarar(sem_marcadores)[1]


def alertas(texto: str) -> list[str]:
    """Possíveis nomes próprios, para a revisão humana conferir. Heurística: pode errar para os dois lados."""
    sem_marcadores = texto
    for m in _MARCADORES:
        sem_marcadores = sem_marcadores.replace(m, " ")
    vistos: list[str] = []
    for m in _CAPITALIZADA.finditer(sem_marcadores):
        if m.group(1) not in vistos:
            vistos.append(m.group(1))
    return vistos


def tamanho_valido(texto: str) -> bool:
    return LIMITE_MIN <= len(normalizar_espacos(texto)) <= LIMITE_MAX
