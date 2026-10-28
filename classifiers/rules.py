"""Baseline A — regras explícitas e auditáveis.

Composição:
1. Léxico genérico de insulto/xingamento -> `linguagem_ofensiva` e `insulto_hostilidade`.
   Deliberadamente SEM acusações (ex.: "ladrão", "corrupto"), pois crítica política dura
   pode usá-las; e SEM termos específicos de grupo (não há regra para racismo, xenofobia,
   misoginia ou LGBTfobia: o baseline A declara não cobrir essas classes).
2. Regras contextuais do monitor (cópia congelada em `eh_so_opiniao.regras_monitor`) para as classes
   exploratórias, traduzidas para a taxonomia. Servem de hipótese, não de medição.

O baseline retorna, por classe, True/False apenas para as classes que cobre
(`COBERTURA`); para as demais devolve None.
"""

from __future__ import annotations

import re
from typing import Any

from eh_so_opiniao.regras_monitor.intolerancia import classificar_conteudo
from eh_so_opiniao.regras_monitor.normalizer import norm

VERSAO = "regras-1.0.0"

_TERMOS = (
    "idiota", "imbecil", "burro", "burra", "lixo", "merda", "bosta", "porcaria", "nojento", "nojenta",
    "canalha", "otario", "otaria", "babaca", "cretino", "cretina", "vagabundo", "vagabunda", "desgracado",
    "desgracada", "safado", "safada", "maldito", "maldita", "palhaco", "palhaca", "verme", "vermes",
    "estupido", "estupida", "inutil", "escoria", "porra", "caralho", "puta", "puto", "fdp", "vtnc",
    "cuzao", "arrombado", "arrombada", "trouxa", "energumeno", "analfabeto", "analfabeta", "mentecapto",
    "debil mental", "filho da puta", "filha da puta", "vai se foder", "vai tomar no cu", "cala a boca",
)
_LEXICO = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in _TERMOS) + r")\b")

# monitor -> taxonomia (rótulos do monitor sem correspondente são ignorados de propósito)
_MONITOR_PARA_TAXONOMIA = {
    "possivel_assedio_eleitoral_trabalhista": "possivel_assedio_eleitoral_contextual",
    "discriminacao_em_contratacao": "possivel_assedio_eleitoral_contextual",
    "ameaca_emprego": "possivel_assedio_eleitoral_contextual",
    "coercao_voto": "possivel_assedio_eleitoral_contextual",
    "participacao_compulsoria": "possivel_assedio_eleitoral_contextual",
    "retaliacao_laboral": "possivel_assedio_eleitoral_contextual",
    "violacao_sigilo": "possivel_assedio_eleitoral_contextual",
    "discriminacao_regional_potencial": "discriminacao_regional",
    "possivel_preconceito_regional": "discriminacao_regional",
    "estereotipo_regional": "discriminacao_regional",
    "retorica_excludente": "exclusao_social_territorial",
    "estigmatizacao_socioeconomica": "estigmatizacao_socioeconomica",
    "linguagem_desumanizante": "desumanizacao",
    "hostilidade_politica": "hostilidade_politica",
    "hostilidade_contextual": "hostilidade_politica",
    "critica_politica": "critica_politica_legitima",
    "expressao_politica": "critica_politica_legitima",
    "propaganda_eleitoral": "critica_politica_legitima",
    "humor_ou_ironia": "ironia_humor",
    "contexto_insuficiente": "ambigua",
}

COBERTURA = frozenset({"linguagem_ofensiva", "insulto_hostilidade", *set(_MONITOR_PARA_TAXONOMIA.values())})


class RegrasBaseline:
    nome = "A_regras"
    versao = VERSAO
    cobertura = COBERTURA

    def prever(self, texto: str) -> dict[str, bool]:
        base = norm(texto or "")
        achados = _LEXICO.findall(base)
        saida = {rotulo: False for rotulo in COBERTURA}
        saida["linguagem_ofensiva"] = bool(achados)
        saida["insulto_hostilidade"] = bool(achados)
        monitor = classificar_conteudo(texto)
        for rotulo in monitor["labels"]:
            alvo = _MONITOR_PARA_TAXONOMIA.get(rotulo)
            if alvo:
                saida[alvo] = True
        return saida

    def prever_ofensivo(self, textos: list[str]) -> list[bool]:
        """Só a parte léxica (rápida) para os experimentos binários em corpora externos."""
        return [bool(_LEXICO.search(norm(t or ""))) for t in textos]

    def termos_encontrados(self, texto: str) -> list[str]:
        return _LEXICO.findall(norm(texto or ""))

    def descricao(self) -> dict[str, Any]:
        return {"nome": self.nome, "versao": self.versao, "n_termos_lexico": len(_TERMOS),
                "classes_cobertas": sorted(COBERTURA), "nao_cobre": ["racismo", "xenofobia", "misoginia", "lgbtfobia"]}
