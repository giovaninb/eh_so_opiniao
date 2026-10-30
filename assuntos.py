"""Camada editorial de assuntos: navegação para visitantes, sem substituir a taxonomia científica.

A fonte é `casos/assuntos_editoriais.yaml`. O build gera `site/data/assuntos.json` com contagens
calculadas sobre as frases já publicáveis. Uma frase pode pertencer a vários assuntos; não é duplicada
na base. Assuntos sem exemplos aprovados ficam `visivel: false`.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

from . import casos, paths, registry

ARQUIVO = paths.CASOS / "assuntos_editoriais.yaml"
SLUG = re.compile(r"^[a-z][a-z0-9_]{1,60}$")


def carregar(caminho=ARQUIVO) -> dict[str, Any]:
    bruto = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    if not isinstance(bruto, dict) or "assuntos" not in bruto or "grupos" not in bruto:
        raise ValueError("assuntos_editoriais.yaml precisa de grupos e assuntos")
    return bruto


def _ids(seq: list[Any] | None) -> list[str]:
    return [str(x) for x in (seq or []) if x]


def ids_rotulos_cientificos() -> set[str]:
    return {k for k in registry.carregar_taxonomia() if not str(k).startswith("__")}


def ids_temas_exibicao() -> set[str]:
    return {t["id"] for t in casos.temas()}


def ids_grupos_legado() -> set[str]:
    from . import expansao
    return set(expansao.ROTULO_POR_GRUPO) | {g["id"] for g in yaml.safe_load((paths.CASOS / "grupos_descoberta.yaml").read_text(encoding="utf-8"))["grupos"]}


def validar(cfg: dict[str, Any] | None = None) -> list[str]:
    """Inconsistências entre a camada editorial e a científica. Lista vazia = ok."""
    cfg = cfg or carregar()
    erros: list[str] = []
    grupos = cfg.get("grupos") or []
    assuntos = cfg.get("assuntos") or []
    situacoes = cfg.get("situacoes") or []
    ids_grupo = [g.get("id") for g in grupos]
    ids_assunto = [a.get("id") for a in assuntos]
    if len(ids_grupo) != len(set(ids_grupo)):
        erros.append("id de grupo duplicado")
    if len(ids_assunto) != len(set(ids_assunto)):
        erros.append("id de assunto duplicado")
    for g in grupos:
        if not SLUG.match(str(g.get("id") or "")):
            erros.append(f"grupo id inválido: {g.get('id')}")
        if not (g.get("nome") or "").strip():
            erros.append(f"grupo {g.get('id')} sem nome")
    cientificos = ids_rotulos_cientificos()
    temas = ids_temas_exibicao()
    legado = ids_grupos_legado()
    conhecidos = set(ids_assunto)
    for a in assuntos:
        aid = a.get("id")
        if not SLUG.match(str(aid or "")):
            erros.append(f"assunto id inválido: {aid}")
        if a.get("grupo") not in ids_grupo:
            erros.append(f"{aid}: grupo desconhecido {a.get('grupo')}")
        if not (a.get("nome") or "").strip() or not (a.get("descricao") or "").strip():
            erros.append(f"{aid}: nome ou descrição vazios")
        for campo, permitidos in (("temas", temas), ("rotulos", cientificos), ("grupos_legado", legado)):
            for x in _ids(a.get(campo)):
                if x not in permitidos:
                    erros.append(f"{aid}: {campo} desconhecido: {x}")
        for r in _ids(a.get("relacionados")) + _ids([a.get("pai")] if a.get("pai") else []):
            if r not in conhecidos:
                erros.append(f"{aid}: relacionado/pai desconhecido: {r}")
        if not any(_ids(a.get(c)) for c in ("temas", "rotulos", "grupos_legado", "subtemas")):
            erros.append(f"{aid}: sem critério de associação (tema, rótulo, grupo ou subtema)")
    ids_sit = [s.get("id") for s in situacoes]
    if len(ids_sit) != len(set(ids_sit)):
        erros.append("id de situação duplicado")
    for s in situacoes:
        if not SLUG.match(str(s.get("id") or "")):
            erros.append(f"situação id inválido: {s.get('id')}")
        for x in _ids(s.get("assuntos")):
            if x not in conhecidos:
                erros.append(f"situação {s.get('id')}: assunto desconhecido {x}")
    return erros


def frase_no_assunto(frase: dict[str, Any], assunto: dict[str, Any]) -> bool:
    """Uma frase pode entrar em vários assuntos; a base não é duplicada."""
    if frase.get("grupo") and frase["grupo"] in set(_ids(assunto.get("grupos_legado"))):
        return True
    if frase.get("tema") and frase["tema"] in set(_ids(assunto.get("temas"))):
        return True
    rotulos = {r["id"] for r in (frase.get("rotulos") or []) if isinstance(r, dict) and r.get("id")}
    if rotulos & set(_ids(assunto.get("rotulos"))):
        return True
    if frase.get("subtema") and frase["subtema"] in set(_ids(assunto.get("subtemas"))):
        return True
    return False


def _busca(assunto: dict[str, Any], grupo_nome: str) -> str:
    partes = [assunto.get("nome") or "", assunto.get("descricao") or "", grupo_nome]
    partes += _ids(assunto.get("palavras"))
    partes += _ids(assunto.get("subtemas"))
    partes += _ids(assunto.get("temas"))
    partes += _ids(assunto.get("rotulos"))
    texto = " ".join(partes)
    nfd = unicodedata.normalize("NFD", texto.casefold())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def exportar(frases: list[dict[str, Any]], pares: list[dict[str, Any]] | None = None,
             cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or carregar()
    erros = validar(cfg)
    if erros:
        raise ValueError("assuntos editoriais inconsistentes:\n- " + "\n- ".join(erros))
    minimo = int(cfg.get("minimo_para_exibir") or 1)
    grupos_cfg = sorted(cfg["grupos"], key=lambda g: (g.get("ordem", 99), g["id"]))
    nomes_grupo = {g["id"]: g["nome"] for g in grupos_cfg}
    ids_pub = {f["id"] for f in frases}
    pares = [p for p in (pares or []) if p.get("a") in ids_pub and p.get("b") in ids_pub]

    assuntos_saida: list[dict[str, Any]] = []
    for a in sorted(cfg["assuntos"], key=lambda x: (x.get("ordem", 99), x["id"])):
        membros = [f["id"] for f in frases if frase_no_assunto(f, a)]
        n = len(membros)
        visivel = n >= minimo
        n_pares = sum(1 for p in pares if p["a"] in membros and p["b"] in membros) if visivel else 0
        tipos: dict[str, int] = {}
        for f in frases:
            if f["id"] in membros:
                tipos[f["tipo"]] = tipos.get(f["tipo"], 0) + 1
        assuntos_saida.append({
            "id": a["id"],
            "nome": a["nome"],
            "descricao": a["descricao"],
            "grupo": a["grupo"],
            "grupo_nome": nomes_grupo[a["grupo"]],
            "ordem": int(a.get("ordem") or 99),
            "url": f"#/assuntos/{a['id']}",
            "descobrir": f"#/descobrir?assunto={a['id']}",
            "explorar": f"#/explorar?assunto={a['id']}",
            "temas": _ids(a.get("temas")),
            "rotulos": _ids(a.get("rotulos")),
            "grupos_legado": _ids(a.get("grupos_legado")),
            "subtemas": _ids(a.get("subtemas")),
            "palavras": _ids(a.get("palavras")),
            "relacionados": _ids(a.get("relacionados")),
            "pai": a.get("pai") or None,
            "n": n,
            "n_pares": n_pares,
            "tipos": tipos,
            "visivel": visivel,
            "busca": _busca(a, nomes_grupo[a["grupo"]]),
        })

    visiveis = {a["id"] for a in assuntos_saida if a["visivel"]}
    for a in assuntos_saida:
        a["relacionados"] = [r for r in a["relacionados"] if r in visiveis and r != a["id"]]
        if a["pai"] not in visiveis:
            a["pai"] = None

    situacoes = []
    for s in cfg.get("situacoes") or []:
        aids = [i for i in _ids(s.get("assuntos")) if i in visiveis]
        if not aids:
            continue
        situacoes.append({
            "id": s["id"],
            "nome": s["nome"],
            "descricao": s.get("descricao") or "",
            "assuntos": aids,
            "url": f"#/assuntos?situacao={s['id']}",
        })

    grupos_saida = []
    for g in grupos_cfg:
        itens = [a["id"] for a in assuntos_saida if a["grupo"] == g["id"] and a["visivel"]]
        n = sum(a["n"] for a in assuntos_saida if a["id"] in itens)
        grupos_saida.append({
            "id": g["id"],
            "nome": g["nome"],
            "descricao": g.get("descricao") or "",
            "ordem": int(g.get("ordem") or 99),
            "url": f"#/assuntos?grupo={g['id']}",
            "assuntos": itens,
            "n_assuntos": len(itens),
            "n": n,
            "visivel": bool(itens),
        })

    return {
        "versao": str(cfg.get("versao") or "1"),
        "aviso": "Camada editorial de navegação. Os rótulos científicos de cada frase continuam em frases.json.",
        "grupos": grupos_saida,
        "assuntos": assuntos_saida,
        "situacoes": situacoes,
        "n_visiveis": sum(1 for a in assuntos_saida if a["visivel"]),
        "n_ocultos": sum(1 for a in assuntos_saida if not a["visivel"]),
    }
