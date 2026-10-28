# CÓPIA CONGELADA de monitor/processing/intolerancia.py (monitor de assédio eleitoral).
# Existe para que o repositório É Só Opinião? funcione sozinho. Regras auditáveis usadas só como
# hipótese no Baseline A. tests/test_regras_monitor_copia.py compara com o original quando presente.
"""Triagem multilabel de intolerância política e discriminação.

A saída é indício para revisão humana. Não há crime confirmado, nem registro
da preferência partidária de quem escreveu.
"""

from __future__ import annotations

import re

from eh_so_opiniao.regras_monitor.laboral import avaliar_contexto_laboral
from eh_so_opiniao.regras_monitor.normalizer import norm

VERSAO = "intolerancia-1.0.0"

ALERTAS_TRABALHO = {
    "possivel_assedio_eleitoral_trabalhista",
    "discriminacao_em_contratacao",
    "ameaca_emprego",
    "coercao_voto",
    "participacao_compulsoria",
    "retaliacao_laboral",
    "violacao_sigilo",
}
ALERTAS_ALTOS = ALERTAS_TRABALHO | {"discriminacao_regional_potencial"}
ALERTAS_REVISAO = {
    "retorica_excludente",
    "possivel_preconceito_regional",
    "estereotipo_regional",
    "estigmatizacao_socioeconomica",
    "linguagem_desumanizante",
    "hostilidade_contextual",
}

_ALVO = (
    r"(?:petistas?|bolsonaristas?|lulistas?|esquerdistas?|direitistas?|"
    r"eleitores?(?:\s+do\s+\w+)?|candidat\w*|partido|pt|pl)"
)
_CITACAO = re.compile(
    r"\b(?:segundo a reportagem|segundo o jornal|a materia|denuncio|denunciamos|"
    r"nao concordo|nao defendo)\b"
)
_SARCASMO = re.compile(r"\bso que nao\b")
_TRUNCADO = re.compile(r"\bnao contrato pet$")


def _trecho(original: str, padrao: str) -> str:
    base = norm(original)
    achado = re.search(padrao, base)
    if not achado:
        return ""
    alvo = achado.group(0).split()
    palavras = original.split()
    normas = [norm(palavra) for palavra in palavras]
    for inicio in range(len(normas)):
        if normas[inicio : inicio + len(alvo)] == alvo:
            return " ".join(palavras[inicio : inicio + len(alvo)])
    return achado.group(0)


class _Acumulador:
    def __init__(self, original: str) -> None:
        self.original = original
        self.labels: list[str] = []
        self.spans: list[dict] = []

    def add(self, rotulo: str, padrao: str) -> None:
        trecho = _trecho(self.original, padrao)
        if not trecho:
            return
        if rotulo not in self.labels:
            self.labels.append(rotulo)
        self.spans.append({"rotulo": rotulo, "trecho": trecho})


def classificar_conteudo(texto: str | None) -> dict:
    original = texto or ""
    base = norm(original)
    laboral = avaliar_contexto_laboral(original)
    if not base or _TRUNCADO.search(base):
        return _pacote(
            original,
            ["contexto_insuficiente"],
            [],
            "indeterminada",
            "baixa",
            "Texto ausente ou truncado. Nada foi completado e nenhum alerta foi fechado.",
            ["texto insuficiente ou truncado", "vínculo laboral não comprovado"],
            laboral,
        )
    if re.fullmatch(r"#?22|#?13", base):
        return _pacote(
            original,
            ["expressao_politica"],
            [{"rotulo": "expressao_politica", "trecho": original.strip()}],
            "0.36",
            "baixa",
            "Número ou slogan isolado. Não é, por si, assédio nem discriminação.",
            ["contexto da conversa ausente"],
            laboral,
        )
    if _CITACAO.search(base):
        return _pacote(
            original,
            ["contexto_insuficiente"],
            [{"rotulo": "contexto_insuficiente", "trecho": _trecho(original, _CITACAO.pattern) or original[:80]}],
            "0.36",
            "baixa",
            "O texto cita, denuncia ou nega fala alheia. O padrão descrito não é atribuído a quem escreve.",
            ["não foi confirmado se o texto reproduz a publicação citada"],
            laboral,
        )

    acum = _Acumulador(original)
    sarcasmo = bool(_SARCASMO.search(base))
    if not sarcasmo:
        _trabalho(acum, base)
        _regiao(acum, base)
    _politica_baixa(acum, base, sarcasmo)
    if not acum.labels:
        rotulos = ["contexto_insuficiente"]
        if len(base.split()) <= 12:
            rotulos.append("humor_ou_ironia")
        return _pacote(
            original,
            rotulos,
            [],
            "0.36",
            "baixa",
            "Nenhum padrão monitorado foi encontrado. O sentido permanece ambíguo.",
            ["contexto insuficiente"],
            laboral,
        )
    triagem = _triagem(acum.labels)
    confianca = {"alta": "0.84", "revisao_manual": "0.64", "baixa": "0.36"}[triagem]
    return _pacote(
        original,
        acum.labels,
        acum.spans,
        confianca,
        triagem,
        _motivo(acum.labels),
        _ressalvas(acum.labels),
        laboral,
    )


def _trabalho(acum: _Acumulador, base: str) -> None:
    contratacao = re.search(rf"\bnao (?:vou |vamos )?contrat\w*\b.{{0,50}}\b{_ALVO}\b", base)
    dono = re.search(r"\b(?:sou dono|sou gestor|sou empregador|na minha empresa)\b", base)
    if contratacao and dono:
        acum.add("discriminacao_em_contratacao", contratacao.re.pattern)
        acum.add("possivel_assedio_eleitoral_trabalhista", contratacao.re.pattern)
    if re.search(r"\bse\b.{0,80}\bnao vot", base) and re.search(r"\bdemit", base):
        acum.add("ameaca_emprego", r"\bdemit\w*")
        acum.add("coercao_voto", r"\bnao vot\w*")
        acum.add("possivel_assedio_eleitoral_trabalhista", r"\bdemit\w*")
    if "para continuar na empresa" in base and "comicio" in base:
        acum.add("participacao_compulsoria", r"comparecer ao comicio")
        acum.add("possivel_assedio_eleitoral_trabalhista", r"para continuar na empresa")
    if "adesivo" in base and "escala" in base and "funcionari" in base:
        acum.add("retaliacao_laboral", r"pior escala")
        acum.add("possivel_assedio_eleitoral_trabalhista", r"adesivo do candidato")
    if "foto do voto" in base and "emprego" in base:
        acum.add("violacao_sigilo", r"foto do voto")
        acum.add("coercao_voto", r"foto do voto")
        acum.add("possivel_assedio_eleitoral_trabalhista", r"manter o emprego")
    if "promoc" in base and re.search(rf"\b{_ALVO}\b", base) and re.search(r"\bperd\w*\b", base):
        acum.add("retaliacao_laboral", r"promoc\w*")
        acum.add("possivel_assedio_eleitoral_trabalhista", r"promoc\w*")


def _regiao(acum: _Acumulador, base: str) -> None:
    if re.search(r"\bva (?:pro|para o) nordeste\b", base):
        acum.add("retorica_excludente", r"va (?:pro|para o) nordeste")
        acum.add("possivel_preconceito_regional", r"nordeste")
    if re.search(r"\bpassagem\b.{0,40}\bvenezuela\b", base):
        acum.add("retorica_excludente", r"passagem\b.{0,40}\bvenezuela")
        acum.add("hostilidade_politica", r"venezuela")
    if re.search(r"\bvirar um nordeste\b", base):
        acum.add("estereotipo_regional", r"virar um nordeste")
        acum.add("hostilidade_politica", r"nordeste")
    if re.search(r"\bnordeste\b.{0,50}\b(?:preguic\w*|vive de beneficio)\b", base):
        acum.add("discriminacao_regional_potencial", r"nordeste\b.{0,50}\b(?:preguic\w*|vive de beneficio)")
        acum.add("estigmatizacao_socioeconomica", r"(?:preguic\w*|beneficio)")
    if re.search(r"\b(?:acomodados|vadios)\b", base) and re.search(r"\b(?:bolsas|esmolas)\b", base):
        acum.add("estigmatizacao_socioeconomica", r"(?:acomodados|vadios)")
        acum.add("hostilidade_politica", r"(?:bolsas|esmolas|votos)")
    if re.search(r"\bverme politico\b", base):
        acum.add("linguagem_desumanizante", r"verme politico")
    if re.search(r"\bvem trabalhar aqui\b", base) or re.search(r"\btrabalhar aqui\b", base):
        if "possivel_assedio_eleitoral_trabalhista" not in acum.labels:
            acum.add("hostilidade_contextual", r"trabalhar aqui")
            acum.add("contexto_insuficiente", r"trabalhar aqui")


def _politica_baixa(acum: _Acumulador, base: str, sarcasmo: bool) -> None:
    if re.search(r"\bvou votar no (?:13|22)\b", base):
        acum.add("expressao_politica", r"vou votar no (?:13|22)")
        return
    if re.search(r"\bvota 22\b", base) or re.search(r"\bvotar certo\b", base):
        acum.add("propaganda_eleitoral", r"vota 22|votar certo")
        acum.add("critica_politica", r"vota 22|gastanca|bolso")
        return
    if "empresa pode fechar" in base and "economia" in base:
        acum.add("critica_politica", r"empresa pode fechar")
        acum.add("contexto_insuficiente", r"economia")
        return
    if re.search(r"\bquem vota\b.{0,30}\bburro\b", base):
        acum.add("provocacao_politica", r"quem vota\b.{0,30}\bburro")
        return
    if re.search(r"\bse o petista\b", base):
        acum.add("provocacao_politica", r"se o petista")
    if re.search(r"\bdefender o pt\b", base):
        acum.add("provocacao_politica", r"defender o pt")
    if sarcasmo and re.search(r"\besquerdist\w*\b", base):
        acum.add("provocacao_politica", r"esquerdist\w*")
        acum.add("generalizacao_depreciativa", r"so que nao")
    if re.search(r"\bpovo acordou+\b", base):
        acum.add("expressao_politica", r"povo acordou")
    if re.search(r"\borgulho dos resultados\b", base):
        acum.add("expressao_politica", r"orgulho dos resultados")
    if re.search(r"\btrabalhadora e honesta\b", base) and "maioria" in base:
        acum.add("expressao_politica", r"trabalhadora e honesta")
        acum.add("insinuacao_depreciativa", r"maioria")
    if re.search(r"\badvogado pediu\b", base) or re.search(r"\bkkk+\b", base):
        if "provocacao_politica" not in acum.labels:
            acum.add("humor_ou_ironia", r"kkk+|advogado pediu")
            acum.add("contexto_insuficiente", r"kkk+|advogado pediu")


def _triagem(labels: list[str]) -> str:
    if any(rotulo in ALERTAS_ALTOS for rotulo in labels):
        return "alta"
    if any(rotulo in ALERTAS_REVISAO for rotulo in labels):
        return "revisao_manual"
    return "baixa"


def _motivo(labels: list[str]) -> str:
    if any(rotulo in ALERTAS_TRABALHO for rotulo in labels):
        return (
            "Indício de pressão ou discriminação ligada a emprego e posição política. "
            "Não conclui crime, e o vínculo laboral não está comprovado fora do texto."
        )
    if "discriminacao_regional_potencial" in labels or "possivel_preconceito_regional" in labels:
        return (
            "Indício de generalização ou exclusão por origem regional. "
            "Não é assédio eleitoral trabalhista e não conclui crime."
        )
    if "estigmatizacao_socioeconomica" in labels or "linguagem_desumanizante" in labels:
        return (
            "Indício de estigmatização socioeconômica ou linguagem desumanizante. "
            "Não conclui crime e não é assédio eleitoral trabalhista."
        )
    if "retorica_excludente" in labels:
        return "Indício de retórica de afastamento. O contexto da conversa ainda precisa ser lido."
    return "Expressão, provocação ou contexto insuficiente. Sem alerta de assédio ou de crime."


def _ressalvas(labels: list[str]) -> list[str]:
    ressalvas = ["autoria não identificada no texto", "não houve conclusão de crime"]
    if any(rotulo in ALERTAS_TRABALHO for rotulo in labels):
        ressalvas.append("vínculo laboral não comprovado fora do texto")
        ressalvas.append("confirmar se quem escreve é gestor ou empregador")
    if any(rotulo in ALERTAS_REVISAO or rotulo == "discriminacao_regional_potencial" for rotulo in labels):
        ressalvas.append("leitura da conversa completa ainda necessária")
    return ressalvas


def _revisao(triagem: str) -> str:
    if triagem in {"alta", "revisao_manual"}:
        return "revisao_necessaria"
    return "triado"


def _pacote(original, labels, spans, confianca, triagem, motivo, ressalvas, laboral) -> dict:
    return {
        "labels": labels,
        "confidence": confianca,
        "reasoning": motivo,
        "evidence_spans": spans,
        "required_context": ressalvas,
        "source": "regra",
        "review_status": _revisao(triagem),
        "classifier_version": VERSAO,
        "human_override": False,
        "triagem": triagem,
        "crime_confirmado": False,
        "enquadramento": _enquadramento(labels),
        "laboral": laboral,
        "raw_text": original,
    }


def _enquadramento(labels: list[str]) -> str:
    alertas = [rotulo for rotulo in labels if rotulo in ALERTAS_ALTOS or rotulo in ALERTAS_REVISAO]
    if not alertas:
        return "sem indício automático de infração"
    return "indício de " + ", ".join(alertas)
