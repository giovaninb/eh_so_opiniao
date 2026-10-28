# CÓPIA CONGELADA de monitor/processing/laboral.py (monitor de assédio eleitoral).
# Existe para que o repositório É Só Opinião? funcione sozinho. Regras auditáveis usadas só como
# hipótese no Baseline A. tests/test_regras_monitor_copia.py compara com o original quando presente.
"""Marcadores de relação de trabalho citados no próprio texto.

Um marcador presente no texto não comprova o vínculo. A comprovação depende
de revisão humana e de contexto que o comentário, sozinho, não traz.
"""

from __future__ import annotations

import re

from eh_so_opiniao.regras_monitor.normalizer import norm

MARCADORES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("autoapresentacao_gestor", re.compile(r"\b(?:sou dono|sou gestor|sou empregador|sou chefe|na minha empresa)\b")),
    ("admissao", re.compile(r"\bnao (?:vou |vamos |iremos )?(?:contrat\w*|admit\w*|empreg\w*)\b")),
    ("demissao", re.compile(r"\bdemit\w*\b")),
    ("escala", re.compile(r"\bescala\b")),
    ("promocao", re.compile(r"\bpromoc\w*\b")),
    ("beneficio_laboral", re.compile(r"\b(?:bonus|gratificacao|premio)\b")),
    ("ameaca", re.compile(r"\b(?:demit\w*|perdera a promocao|pior escala|manter o emprego)\b")),
    ("dependencia", re.compile(r"\b(?:para continuar na empresa|para manter o emprego)\b")),
    ("imposicao", re.compile(r"\b(?:comparecer ao comicio|foto do voto|usarem adesivo|usar adesivo)\b")),
    ("equipe", re.compile(r"\b(?:equipe|funcionari\w*)\b")),
)


def avaliar_contexto_laboral(texto: str | None) -> dict:
    base = norm(texto)
    presentes = []
    ausentes = []
    for nome, padrao in MARCADORES:
        achado = padrao.search(base)
        if achado:
            presentes.append({"nome": nome, "trecho": achado.group(0), "presente_no_texto": True})
        else:
            ausentes.append(nome)
    return {
        "comprovado": False,
        "marcadores": presentes,
        "ausentes": ausentes,
        "observacao": (
            "O texto pode mencionar emprego, contratação ou gestão. "
            "Isso não comprova relação de trabalho, subordinação nem autoria."
        ),
    }
