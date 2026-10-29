"""Concordância entre anotadores do MultiDomainYT-ToxBR, recalculada a partir das planilhas.

O artigo reporta kappa de Fleiss por categoria e grupo (Tabela 4). Aqui os mesmos números são
RECALCULADOS dos votos 0-3 e comparados com os reportados; divergência é informação, nunca é corrigida.
Também mede o que o consenso esconde: quantos comentários de cada classe têm voto dividido (1 ou 2 de 3).
Sem identificar anotadores: planilhas são citadas só pelo número de ordem.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from .. import paths, registry
from ..adapters.multidomain_yt import CLASSES_VETOR, LIMIAR_CONSENSO, N_ANOTADORES_POR_GRUPO, carregar_votos
from ..adapters.xlsx_leve import ler_xlsx


def kappa_fleiss_binario(contagens: Sequence[int], n_anotadores: int = N_ANOTADORES_POR_GRUPO) -> float | None:
    """Kappa de Fleiss para duas categorias; `contagens[i]` = nº de anotadores que marcaram 1 no item i."""
    n_itens = len(contagens)
    if n_itens == 0 or n_anotadores < 2:
        return None
    p1 = sum(contagens) / (n_itens * n_anotadores)
    p_esperado = p1 ** 2 + (1 - p1) ** 2
    if p_esperado >= 1.0:
        return None  # sem variação: kappa indefinido
    p_itens = []
    for k in contagens:
        concordantes = k * (k - 1) + (n_anotadores - k) * (n_anotadores - k - 1)
        p_itens.append(concordantes / (n_anotadores * (n_anotadores - 1)))
    p_obs = sum(p_itens) / n_itens
    return (p_obs - p_esperado) / (1 - p_esperado)


def alfa_krippendorff_binario(contagens: Sequence[int], n_anotadores: int = N_ANOTADORES_POR_GRUPO) -> float | None:
    """Alfa de Krippendorff nominal (dados completos, 2 categorias)."""
    n_itens, m = len(contagens), n_anotadores
    total = n_itens * m
    n1 = sum(contagens)
    n0 = total - n1
    if n_itens == 0 or n1 == 0 or n0 == 0:
        return None
    d_obs = sum(2 * k * (m - k) / (m - 1) for k in contagens) / total
    d_esp = 2 * n1 * n0 / (total * (total - 1))
    return 1 - d_obs / d_esp


def _arred(x: float | None) -> float | None:
    return None if x is None else round(float(x), 4)


def taxa_invalido_por_planilha(arquivos: Sequence[Path]) -> dict[str, Any]:
    """Fração de linhas marcadas 'inválido' em cada planilha (anotador identificado só pelo número de ordem)."""
    saida: dict[str, Any] = {}
    for n, caminho in enumerate(arquivos, start=1):
        linhas = ler_xlsx(Path(caminho))
        cab = [(h or "").replace("\n", " ").strip().lower().replace("á", "a") for h in linhas[0]]
        col = next(i for i, h in enumerate(cab) if h.startswith("invalido"))
        corpo = linhas[1:]
        marcadas = sum(1 for l in corpo if len(l) > col and l[col] == "1")
        saida[f"planilha_{n}"] = {"linhas": len(corpo), "marcadas_invalido": marcadas,
                                  "fracao": round(marcadas / len(corpo), 4) if corpo else None}
    return saida


def calcular(arquivos: Sequence[Path]) -> dict[str, Any]:
    votos = carregar_votos(arquivos)
    reportado = registry.dataset("multidomain_yt_toxbr")["ficha_cientifica"]["concordancia_reportada_no_artigo"]
    por_grupo: dict[str, Any] = {}
    for grupo in (1, 2):
        itens = [v for v in votos if v["grupo"] == grupo]
        classes: dict[str, Any] = {}
        for c in CLASSES_VETOR:
            cont = [v["votos"][c] for v in itens]
            kappa, alfa = kappa_fleiss_binario(cont), alfa_krippendorff_binario(cont)
            rep = reportado[f"grupo_{grupo}"][c]
            marcados = [k for k in cont if k > 0]
            classes[c] = {
                "kappa_fleiss": _arred(kappa), "alfa_krippendorff": _arred(alfa), "kappa_reportado_no_artigo": rep,
                "diferenca_para_o_artigo": _arred(None if kappa is None else kappa - rep),
                "comentarios_com_algum_voto": len(marcados),
                "positivos_por_maioria": sum(1 for k in cont if k >= LIMIAR_CONSENSO),
                "marcados_so_por_um_anotador": sum(1 for k in cont if k == 1),
                "marcados_por_dois": sum(1 for k in cont if k == 2),
                "marcados_por_tres": sum(1 for k in cont if k == 3),
                "fracao_unanime_entre_os_marcados": _arred(sum(1 for k in marcados if k == N_ANOTADORES_POR_GRUPO) / len(marcados)) if marcados else None,
            }
        validos = [c["kappa_fleiss"] for c in classes.values() if c["kappa_fleiss"] is not None]
        por_grupo[f"grupo_{grupo}"] = {
            "comentarios": len(itens), "classes": classes,
            "kappa_medio_recalculado": _arred(sum(validos) / len(validos)) if validos else None,
            "kappa_medio_reportado": reportado[f"grupo_{grupo}"]["media"],
        }
    todos = [d["diferenca_para_o_artigo"] for g in por_grupo.values() for d in g["classes"].values() if d["diferenca_para_o_artigo"] is not None]
    return {
        "dataset": "multidomain_yt_toxbr", "fonte": "planilhas dos 6 anotadores (3 por grupo; 2.500 comentários por grupo)",
        "metodo": "Fleiss e Krippendorff (nominal) por categoria, dados completos, 3 anotadores, categoria binária",
        "por_grupo": por_grupo,
        "replicacao_da_tabela_4_do_artigo": {
            "maior_diferenca_absoluta": _arred(max((abs(x) for x in todos), default=None)),
            "leitura": "Diferenças pequenas indicam que a concordância reportada foi reproduzida a partir dos dados públicos.",
        },
        "comentarios_marcados_invalido_por_planilha": taxa_invalido_por_planilha(arquivos),
        "leitura": ("Classes com kappa baixo (racismo, xenofobia, violência, anticapacitismo no grupo 2) têm rótulo de consenso ruidoso: "
                    "métricas de modelo nelas medem também o desacordo humano. A coluna 'inválido' não é usada como rótulo."),
    }


def gerar(destino: Path | None = None) -> dict[str, Any]:
    from ..pipeline import download

    info = registry.dataset("multidomain_yt_toxbr")
    arqs = []
    for k in range(1, 7):
        nome = f"comentariosParaAnotacao{k}.xlsx"
        r = download.validar_integridade("multidomain_yt_toxbr", next(a for a in info["url_arquivos"] if a["arquivo"] == nome))
        if r.status != "integridade_ok" or not r.caminho:
            raise FileNotFoundError(f"{nome} ausente ou sem integridade no cache: rode `baixar --dataset multidomain_yt_toxbr --aceito-licenca`")
        arqs.append(Path(r.caminho))
    resultado = calcular(arqs)
    destino = destino or paths.RELATORIOS / "concordancia_multidomain_yt_toxbr.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    return resultado
