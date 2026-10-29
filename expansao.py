"""Expansão editorial 2026-10 (mulheres, homens, pessoas idosas, religiões e pessoas trans).

Lê `casos/expansao_2026_10.jsonl` (176 exemplos ilustrativos com metadados) e o converte para o MESMO formato dos demais
casos, para entrar na fila de revisão como PENDENTE. Aqui nada é aprovado nem publicado:

- o arquivo de entrada precisa dizer `estado_revisao: Pendente` e `pode_publicar: false`, ou a leitura é recusada;
- as dimensões (grupo, mecanismo, gravidade, contexto de uso, certeza do rótulo) são independentes e vêm de
  `casos/expansao_2026_10_dimensoes.yaml`, como PROPOSTA da equipe;
- o rótulo `leitura` é editorial e provisório: não é julgamento jurídico nem afirma crime;
- `alerta_de_contexto` vira `aviso_conteudo` (um aviso ao visitante, não um rótulo).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from . import paths

ARQUIVO = paths.CASOS / "expansao_2026_10.jsonl"
DIMENSOES = paths.CASOS / "expansao_2026_10_dimensoes.yaml"
GRUPOS = paths.CASOS / "grupos_descoberta.yaml"
LEITURA_TIPO = {"discriminação": "exclusao", "ambígua": "ambigua", "sem discriminação": "nao_discriminatoria"}
GRAVIDADES = ("estereotipo", "ofensa", "exclusao_material", "incitacao_violencia", "nao_se_aplica")
CERTEZAS = ("alta", "media", "baixa")
CONTEXTO_DE_USO = {"exclusao": "fala_dirigida_ou_opiniao", "ambigua": "depende_do_tom_e_do_uso",
                   "nao_discriminatoria": "relato_pergunta_ou_posicao_respeitosa"}
CERTEZA_POR_TIPO = {"exclusao": "media", "ambigua": "baixa", "nao_discriminatoria": "media"}
ROTULO_POR_GRUPO = {"mulheres": "misoginia", "homens": "estereotipos_masculinidade", "pessoas_idosas": "idadismo",
                    "religioes": "intolerancia_religiosa", "pessoas_trans": "transfobia", "pessoas_lgbt": "lgbtfobia",
                    "raca_e_povos_indigenas": "racismo", "pessoas_com_deficiencia": "capacitismo",
                    "relacoes_nao_monogamicas": "estigma_nao_monogamia"}
TEMA_SEM_LEITURA_DE_EXCLUSAO = {"depende_contexto": "ambigua", "ironia": "ambigua", "sem_discriminacao": "nao_discriminatoria"}
MUDA_SE_AMBIGUA = "Quem fala, para quem, em que tom e em que situação decidiria a leitura. Sem isso, a leitura honesta é “depende”."
ORIGEM_PUBLICAVEL = "sintetica_ilustrativa"  # exemplo escrito para educação: nunca comentário real verificado


class ExpansaoInvalida(ValueError):
    pass


def _dimensoes() -> dict[str, Any]:
    return yaml.safe_load(DIMENSOES.read_text(encoding="utf-8"))


def grupos() -> list[dict[str, str]]:
    return yaml.safe_load(GRUPOS.read_text(encoding="utf-8"))["grupos"]


def grupo_de(tema: str | None, grupo_explicito: str | None = None) -> str | None:
    """Grupo de descoberta: o explícito do item, ou o do tema (para frases antigas, que não têm dimensões)."""
    return grupo_explicito or _dimensoes()["grupo_por_tema"].get(tema or "")


def _gravidade(iid: str, tipo: str, tabela: dict[str, list[str]]) -> str:
    if tipo != "exclusao":
        return "nao_se_aplica"
    for nivel in ("exclusao_material", "ofensa"):  # o mais forte prevalece
        if iid in tabela.get(nivel, []):
            return nivel
    return "estereotipo"


def carregar(caminho: Path | None = None) -> dict[str, Any]:
    from . import casos, registry

    caminho = Path(caminho or ARQUIVO)
    dim = _dimensoes()
    ids_tema = {t["id"] for t in casos.temas()}
    tax = registry.rotulos_taxonomia()
    ids_grupo = {g["id"] for g in grupos()}
    sobre = {n: set(ids) for n, ids in dim["gravidade"].items()}
    frases: list[dict[str, Any]] = []
    vistos: set[str] = set()
    embutidos = False
    for n, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), start=1):
        if not linha.strip():
            continue
        r = json.loads(linha)
        iid = r["id"]
        onde = f"{caminho.name}:{n} ({iid})"
        if iid in vistos:
            raise ExpansaoInvalida(f"{onde}: id duplicado")
        vistos.add(iid)
        if r.get("estado_revisao") != "Pendente" or r.get("pode_publicar") is not False:
            raise ExpansaoInvalida(f"{onde}: todo item de entrada deve vir Pendente e com pode_publicar=false (nada é aprovado na importação)")
        if r["leitura"] not in LEITURA_TIPO:
            raise ExpansaoInvalida(f"{onde}: leitura desconhecida {r['leitura']!r}")
        if r["tema"] not in ids_tema:
            raise ExpansaoInvalida(f"{onde}: tema desconhecido {r['tema']!r}")
        embutido = "mecanismo" in r  # registros com metadados próprios (catálogo anterior NX-001..247)
        embutidos = embutidos or embutido
        mecanismo = r["mecanismo"] if embutido else dim["mecanismos"].get(r["subtema"])
        if mecanismo not in set(dim["mecanismos"].values()) | set(dim["mecanismos_do_catalogo_anterior"]):
            raise ExpansaoInvalida(f"{onde}: mecanismo/subtema sem definição {r.get('mecanismo') or r['subtema']!r}")
        tipo = LEITURA_TIPO[r["leitura"]]
        esperado = TEMA_SEM_LEITURA_DE_EXCLUSAO.get(r["tema"], "exclusao")
        if tipo != esperado:
            raise ExpansaoInvalida(f"{onde}: tema {r['tema']} é incompatível com a leitura {r['leitura']}")
        if embutido:
            grupo = r.get("grupo")
        else:
            grupo = dim["grupo_por_subtema"].get(r["subtema"]) or dim["grupo_por_tema"].get(r["tema"])
        if grupo is None and tipo == "exclusao":
            raise ExpansaoInvalida(f"{onde}: discriminação precisa de grupo")
        if grupo is not None and grupo not in ids_grupo:
            raise ExpansaoInvalida(f"{onde}: grupo não definido {grupo!r}")
        rotulos: list[str] = []
        if tipo == "ambigua":
            rotulos.append("ambigua")
        if r["tema"] == "ironia":
            rotulos.append("ironia_humor")
        if tipo != "nao_discriminatoria" and grupo is not None:
            rotulos.append(ROTULO_POR_GRUPO[grupo])
        rotulos = list(dict.fromkeys(rotulos))
        if any(x not in tax for x in rotulos):
            raise ExpansaoInvalida(f"{onde}: rótulo fora da taxonomia em {rotulos}")
        gravidade = r["gravidade"] if embutido else _gravidade(iid, tipo, sobre)
        if gravidade not in GRAVIDADES or gravidade == "incitacao_violencia":
            raise ExpansaoInvalida(f"{onde}: gravidade inválida ou não permitida na importação ({gravidade!r})")
        if (tipo == "exclusao") == (gravidade == "nao_se_aplica"):
            raise ExpansaoInvalida(f"{onde}: gravidade {gravidade!r} incompatível com a leitura {r['leitura']}")
        frases.append({
            "id": iid, "tema": r["tema"], "tipo": tipo, "texto": r["texto"], "origem": ORIGEM_PUBLICAVEL,
            "rotulos_editoriais": rotulos, "mecanismo": r["justificativa_editorial"],
            "muda_se": MUDA_SE_AMBIGUA if tipo == "ambigua" else None, "pode_publicar_ambigua": tipo == "ambigua",
            "subtema": r["subtema"], "origem_original": r["origem"], "colecao": r["colecao"],
            "aviso_conteudo": bool(r.get("alerta_de_contexto")),
            "dimensoes": {"grupo": grupo, "mecanismo": mecanismo, "gravidade": gravidade,
                          "contexto_de_uso": CONTEXTO_DE_USO[tipo], "certeza_rotulo": CERTEZA_POR_TIPO[tipo]},
        })
    if not embutidos:  # a tabela de gravidade vale só para o arquivo sem metadados próprios
        sobrando = {i for ids in sobre.values() for i in ids} - vistos
        if sobrando:
            raise ExpansaoInvalida(f"gravidade definida para ids que não existem: {sorted(sobrando)}")
    return {"frases": frases}
