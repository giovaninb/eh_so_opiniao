"""Contrato versionado das submissões do formulário (Formspree Free).

schema_version=2. Tipos novos: avaliacoes_voluntarias, sugestao_frase, contestacao.
Registros antigos (voto, frase, discordancia) continuam válidos na importação.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA_PARTICIPACAO = "2"
AVISO_VERSAO = "participacao-2"
AVALIACOES = ("opiniao", "discriminacao", "contexto")
TIPOS_V2 = ("avaliacoes_voluntarias", "sugestao_frase", "contestacao")
TIPOS_LEGADO = {
    "voto": "avaliacoes_voluntarias",
    "frase": "sugestao_frase",
    "discordancia": "contestacao",
    "avaliacoes": "avaliacoes_voluntarias",
}
MODOS = ("descobrir", "inicio", "explorar", "frase", "comparar", "assuntos", "desconhecido")
MOTIVOS_CONTESTACAO = (
    "falta_contexto",
    "discordo_classificacao",
    "explicacao_incompleta",
    "interpretacao_excessiva",
    "erro_no_texto",
    "erro_texto",
    "outro",
)
MOTIVO_CANONICO = {"erro_texto": "erro_no_texto"}
CAMPOS_PROIBIDOS = (
    "email", "e-mail", "nome", "name", "telefone", "phone", "ip", "user_agent",
    "user-agent", "fingerprint", "geo", "lat", "lon", "cpf", "endereco",
)
MAX_AVALIACOES_LOTE = 5
MAX_COMENTARIO = 280
MIN_FRASE = 10
MAX_FRASE = 280
MAX_CONTEXTO = 280
MAX_PAYLOAD = 8000
_CONSENTIU = {"sim", "true", "on", "1", "yes", "aceito"}


def payload_editorial(frase: dict[str, Any]) -> dict[str, Any]:
    rotulos = []
    for r in frase.get("rotulos") or []:
        rotulos.append(r["id"] if isinstance(r, dict) else str(r))
    return {
        "aviso_conteudo": bool(frase.get("aviso_conteudo")),
        "contexto": frase.get("contexto") or "",
        "id": frase.get("id") or "",
        "mecanismo": frase.get("mecanismo") or "",
        "muda_se": frase.get("muda_se") or "",
        "razoes": list(frase.get("razoes") or []),
        "rotulos": sorted(rotulos),
        "texto": frase.get("texto") or "",
        "tipo": frase.get("tipo") or "",
    }


def versao_editorial(frase: dict[str, Any]) -> str:
    """Hash determinístico do conteúdo publicado. Muda só se o editorial mudar."""
    bruto = json.dumps(payload_editorial(frase), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()[:12]


def tipo_canonico(valor: str) -> str:
    v = (valor or "").strip().lower()
    return TIPOS_LEGADO.get(v, v)


def consentiu(valor: str) -> bool:
    return (valor or "").strip().lower() in _CONSENTIU


def sim_nao(valor: Any) -> str:
    if valor in (True, 1, "1", "sim", "true", "on"):
        return "sim"
    return "nao"
