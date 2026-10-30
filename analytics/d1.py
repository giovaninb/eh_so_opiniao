"""Converte dump local do D1 em registros do importer.

Não fala com a Cloudflare. O administrador exporta com Wrangler (credenciais dele)
e passa o JSON a `analytics importar`. Participações não entram em datasets científicos.
"""

from __future__ import annotations

from typing import Any


def registros_de_d1(dump: dict[str, Any]) -> list[dict[str, Any]]:
    subs = [x for x in (dump.get("submissions") or []) if isinstance(x, dict)]
    evals: dict[str, list[dict[str, Any]]] = {}
    for e in dump.get("evaluations") or []:
        if isinstance(e, dict) and e.get("submission_id"):
            evals.setdefault(str(e["submission_id"]), []).append(e)
    conts: dict[str, dict[str, Any]] = {}
    for c in dump.get("contestations") or []:
        if isinstance(c, dict) and c.get("submission_id"):
            conts[str(c["submission_id"])] = c
    sugs: dict[str, dict[str, Any]] = {}
    for s in dump.get("suggestions") or []:
        if isinstance(s, dict) and s.get("submission_id"):
            sugs[str(s["submission_id"])] = s

    saida = []
    for s in subs:
        sid = str(s.get("id") or "")
        rec: dict[str, Any] = {
            "schema_version": str(s.get("schema_version") or "3"),
            "tipo": s.get("tipo") or "",
            "consentimento": "sim" if s.get("consentimento") in (1, "1", True, "sim") else "",
            "aviso_versao": s.get("aviso_versao") or "",
            "recebido_em": s.get("created_at") or "",
            "submission_id": sid,
        }
        tipo = str(s.get("tipo") or "")
        if tipo in ("avaliacoes", "avaliacoes_voluntarias"):
            rec["avaliacoes"] = evals.get(sid, [])
        elif tipo == "contestacao":
            c = conts.get(sid, {})
            rec.update({
                "frase_id": c.get("frase_id") or "",
                "conteudo_versao": c.get("conteudo_versao") or "",
                "motivo": c.get("motivo") or "",
                "comentario": c.get("comentario") or "",
            })
        elif tipo == "sugestao_frase":
            g = sugs.get(sid, {})
            rec.update({
                "texto": g.get("texto") or "",
                "interpretacao_sugerida": g.get("interpretacao") or "",
                "contexto": g.get("contexto") or "",
            })
        saida.append(rec)
    return saida
