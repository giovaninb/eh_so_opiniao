"""Relatórios locais e privados. Amostra voluntária: nunca representa a população."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from .. import participacao_esquema as esq
from .importar import ler_arquivo_local, pasta_arquivo

AVISO_AMOSTRA = (
    "Amostra voluntária e autoselecionada. Não representa a população, não estima prevalência "
    "de preconceito e não diagnostica quem participou. Uma submissão com várias avaliações "
    "conta como uma submissão e N avaliações — não como N pessoas."
)

LIMIAR_MIN = 5
LIMIAR_DIVISAO = 0.60


def _agregar(registros: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    regs = registros if registros is not None else ler_arquivo_local()
    submissoes = len(regs)
    avaliacoes: list[dict[str, str]] = []
    contestacoes: list[dict[str, Any]] = []
    sugestoes: list[dict[str, Any]] = []
    por_tipo: Counter[str] = Counter()
    for r in regs:
        tipo = r.get("tipo")
        por_tipo[tipo] += 1
        if tipo == "avaliacoes_voluntarias":
            avaliacoes.extend(r.get("avaliacoes") or [])
        elif tipo == "contestacao":
            contestacoes.append(r)
        elif tipo == "sugestao_frase":
            sugestoes.append(r)
    por_frase: dict[str, Counter[str]] = defaultdict(Counter)
    por_tema: dict[str, Counter[str]] = defaultdict(Counter)
    por_versao: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for a in avaliacoes:
        por_frase[a["frase_id"]][a["avaliacao"]] += 1
        if a.get("tema_id"):
            por_tema[a["tema_id"]][a["avaliacao"]] += 1
        por_versao[(a["frase_id"], a.get("conteudo_versao") or "legado")][a["avaliacao"]] += 1
    motivos = Counter(c.get("motivo") or "(sem motivo)" for c in contestacoes)
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aviso": AVISO_AMOSTRA,
        "submissoes": submissoes,
        "avaliacoes": len(avaliacoes),
        "contestacoes": len(contestacoes),
        "sugestoes": len(sugestoes),
        "por_tipo": dict(por_tipo),
        "por_frase": {k: dict(v) for k, v in sorted(por_frase.items())},
        "por_tema": {k: dict(v) for k, v in sorted(por_tema.items())},
        "por_versao": {f"{k[0]}|{k[1]}": dict(v) for k, v in sorted(por_versao.items())},
        "motivos_contestacao": dict(motivos),
        "interpretacoes": dict(Counter(a["avaliacao"] for a in avaliacoes)),
        "datas": [r.get("recebido_em") or r.get("importado_em") for r in regs if r.get("recebido_em") or r.get("importado_em")],
        "por_dia": dict(Counter((str(r.get("recebido_em") or r.get("importado_em") or ""))[:10]
                                for r in regs if r.get("recebido_em") or r.get("importado_em"))),
    }


def frases_em_atencao(agregado: dict[str, Any] | None = None, minimo: int = LIMIAR_MIN,
                      divisao: float = LIMIAR_DIVISAO) -> list[dict[str, Any]]:
    """Sugestões de revisão editorial, não conclusão sobre o rótulo."""
    a = agregado or _agregar()
    contestadas = Counter()
    for r in ler_arquivo_local():
        if r.get("tipo") == "contestacao" and r.get("frase_id"):
            contestadas[r["frase_id"]] += 1
    saida = []
    for fid, dist in a["por_frase"].items():
        n = sum(dist.values())
        if n < minimo and contestadas.get(fid, 0) == 0:
            continue
        maior = max(dist.values()) / n if n else 0
        motivos = []
        if n >= minimo and maior < divisao:
            motivos.append("leituras divididas (amostra voluntária)")
        if contestadas.get(fid, 0):
            motivos.append(f"{contestadas[fid]} contestação(ões)")
        versoes = [k for k in a["por_versao"] if k.startswith(fid + "|")]
        if len(versoes) > 1:
            motivos.append("há avaliações em mais de uma versão editorial")
        if not motivos:
            continue
        saida.append({
            "frase_id": fid, "n_avaliacoes": n, "distribuicao": dist,
            "contestacoes": contestadas.get(fid, 0), "motivos": motivos,
            "recomendacao": "Rever clareza da pergunta, do contexto, das opções e do momento em que a análise foi revelada. Não alterar o rótulo só pela maioria.",
        })
    saida.sort(key=lambda x: (x["contestacoes"], x["n_avaliacoes"]), reverse=True)
    return saida


def gerar(destino: Path | None = None) -> dict[str, Path]:
    pasta = Path(destino) if destino else pasta_arquivo() / "relatorios"
    pasta.mkdir(parents=True, exist_ok=True)
    a = _agregar()
    atencao = frases_em_atencao(a)
    json_path = pasta / "resumo.json"
    md_path = pasta / "resumo.md"
    html_path = pasta / "painel.html"
    at_path = pasta / "frases_em_atencao.json"
    json_path.write_text(json.dumps(a, indent=2, ensure_ascii=False), encoding="utf-8")
    at_path.write_text(json.dumps(atencao, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(a, atencao), encoding="utf-8")
    html_path.write_text(_html(a, atencao), encoding="utf-8")
    csv_path = pasta / "por_frase.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["frase_id", "opiniao", "discriminacao", "contexto", "n"])
        w.writeheader()
        for fid, dist in a["por_frase"].items():
            w.writerow({
                "frase_id": fid,
                "opiniao": dist.get("opiniao", 0),
                "discriminacao": dist.get("discriminacao", 0),
                "contexto": dist.get("contexto", 0),
                "n": sum(dist.values()),
            })
    return {"json": json_path, "markdown": md_path, "html": html_path, "atencao": at_path, "csv": csv_path}


def _markdown(a: dict[str, Any], atencao: list[dict[str, Any]]) -> str:
    linhas = [
        "# Participações (arquivo local)",
        "",
        a["aviso"],
        "",
        f"- Submissões importadas: {a['submissoes']}",
        f"- Avaliações contidas em lotes ou votos: {a['avaliacoes']}",
        f"- Contestações: {a['contestacoes']}",
        f"- Sugestões de frase: {a['sugestoes']}",
        "",
        "## Interpretações (avaliações, não pessoas)",
        "",
    ]
    for k, n in a["interpretacoes"].items():
        linhas.append(f"- {k}: {n}")
    linhas += ["", "## Evolução temporal (quando a data existe)", ""]
    if a.get("por_dia"):
        for d, n in sorted(a["por_dia"].items()):
            linhas.append(f"- {d}: {n} submissão(ões)")
    else:
        linhas.append("- (sem datas utilizáveis)")
    linhas += ["", "## Motivos de contestação", ""]
    if a["motivos_contestacao"]:
        for k, n in a["motivos_contestacao"].items():
            linhas.append(f"- {k}: {n}")
    else:
        linhas.append("- (nenhuma)")
    linhas += ["", "## Frases que merecem atenção editorial", ""]
    if not atencao:
        linhas.append("Nenhuma frase atingiu o limiar mínimo configurável.")
    for item in atencao:
        linhas.append(f"### {item['frase_id']} ({item['n_avaliacoes']} avaliações)")
        linhas.append(f"- Distribuição: {item['distribuicao']}")
        linhas.append(f"- Por quê: {'; '.join(item['motivos'])}")
        linhas.append(f"- {item['recomendacao']}")
        linhas.append("")
    return "\n".join(linhas) + "\n"


def _html(a: dict[str, Any], atencao: list[dict[str, Any]]) -> str:
    def tab(titulo: str, mapa: dict[str, Any]) -> str:
        rows = "".join(f"<tr><td>{escape(str(k))}</td><td>{escape(str(v))}</td></tr>" for k, v in mapa.items())
        return f"<h2>{escape(titulo)}</h2><table><thead><tr><th>chave</th><th>n</th></tr></thead><tbody>{rows}</tbody></table>"

    at = "".join(
        f"<article><h3>{escape(i['frase_id'])}</h3><p>{escape(str(i['n_avaliacoes']))} avaliações. "
        f"{escape('; '.join(i['motivos']))}</p><p>{escape(i['recomendacao'])}</p></article>"
        for i in atencao
    ) or "<p>Nenhuma frase atingiu o limiar mínimo.</p>"
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Participações (privado)</title>
<style>
body{{font:16px/1.5 system-ui;max-width:52rem;margin:2rem auto;padding:0 1rem;color:#17181c}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:.4rem .6rem;text-align:left}}
.aviso{{background:#fdf1d9;padding:1rem;border-radius:.5rem}}
</style></head><body>
<h1>Participações — painel local</h1>
<p class="aviso">{escape(a['aviso'])}</p>
<ul>
<li>Submissões: {a['submissoes']}</li>
<li>Avaliações: {a['avaliacoes']}</li>
<li>Contestações: {a['contestacoes']}</li>
<li>Sugestões: {a['sugestoes']}</li>
</ul>
{tab("Interpretações", a["interpretacoes"])}
{tab("Tipos de submissão", a["por_tipo"])}
{tab("Motivos de contestação", a["motivos_contestacao"])}
<h2>Frases que merecem atenção editorial</h2>
{at}
<p>Gerado em {escape(a['gerado_em'])}. Não publicar este arquivo.</p>
</body></html>
"""
