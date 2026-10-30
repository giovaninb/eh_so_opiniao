"""Camada editorial de assuntos: validação, contagens reais e ausência de experiências vazias."""

from __future__ import annotations

import json

from eh_so_opiniao import assuntos, paths


def _publicadas():
    return json.loads((paths.SITE / "data" / "frases.json").read_text(encoding="utf-8"))["frases"]


def test_yaml_editorial_e_consistente_com_a_taxonomia():
    assert assuntos.validar() == []


def test_exportacao_esconde_assuntos_sem_frase_aprovada():
    frases = _publicadas()
    pares = json.loads((paths.SITE / "data" / "pares.json").read_text(encoding="utf-8"))["pares"]
    saida = assuntos.exportar(frases, pares)
    assert saida["n_visiveis"] >= 1
    for a in saida["assuntos"]:
        n = sum(1 for f in frases if assuntos.frase_no_assunto(f, {
            "temas": a["temas"], "rotulos": a["rotulos"], "grupos_legado": a["grupos_legado"], "subtemas": a["subtemas"],
        }))
        assert a["n"] == n
        if a["visivel"]:
            assert n >= 1
        else:
            assert n == 0
    assert any(a["id"] == "assedio_eleitoral" and not a["visivel"] for a in saida["assuntos"])


def test_json_publicado_bate_com_as_frases_aprovadas():
    pub = json.loads((paths.SITE / "data" / "assuntos.json").read_text(encoding="utf-8"))
    esperado = assuntos.exportar(_publicadas(), json.loads((paths.SITE / "data" / "pares.json").read_text(encoding="utf-8"))["pares"])
    por_id = {a["id"]: a["n"] for a in pub["assuntos"]}
    for a in esperado["assuntos"]:
        assert por_id[a["id"]] == a["n"]
        assert a["visivel"] == next(x["visivel"] for x in pub["assuntos"] if x["id"] == a["id"])


def test_frase_pode_estar_em_mais_de_um_assunto_sem_duplicar_a_base():
    frases = _publicadas()
    saida = assuntos.exportar(frases, [])
    visiveis = [a for a in saida["assuntos"] if a["visivel"]]
    soma = sum(a["n"] for a in visiveis)
    assert soma > len(frases)
    assert len({f["id"] for f in frases}) == len(frases)


def test_paginas_estaticas_existem_so_para_assuntos_visiveis():
    pub = json.loads((paths.SITE / "data" / "assuntos.json").read_text(encoding="utf-8"))
    visiveis = {a["id"] for a in pub["assuntos"] if a["visivel"]}
    pastas = {p.name for p in (paths.SITE / "assuntos").iterdir() if p.is_dir()} if (paths.SITE / "assuntos").exists() else set()
    assert pastas == visiveis
    sm = (paths.SITE / "sitemap.xml").read_text(encoding="utf-8")
    for aid in visiveis:
        assert f"/assuntos/{aid}/" in sm
        html = (paths.SITE / "assuntos" / aid / "index.html").read_text(encoding="utf-8")
        assert "noindex" not in html
        assert f"#/assuntos/{aid}" in html
