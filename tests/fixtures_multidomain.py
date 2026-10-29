"""Gera dados SINTÉTICOS no layout do MultiDomainYT-ToxBR (CSV binário, CSV multirrótulo e planilhas .xlsx).

Nenhum texto real: frases numeradas. A ORDEM das classes usada aqui é a verificada nos dados reais
(planilhas dos anotadores), não a do README do repositório original.
"""

from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

CLASSES = ("insulto_de_baixo_calao", "homofobia", "racismo", "misoginia_machismo", "xenofobia",
           "violencia_extremismo", "intolerancia_religiosa", "intolerancia_politica", "anticapacitismo")
CABECALHO_XLSX = ["comentario", "insulto de \nbaixo calão", "homofobia", "racismo", "misoginia/\nmachismo", "xenofobia",
                  "violência/\nextremismo", "intolerância\n religiosa", "intolerância \npolítica", "anticapacitismo", "inválido"]
# (votos por classe: nº de anotadores de 0 a 3 que marcaram; invalido: idem)
LINHAS = [
    {},
    {"insulto_de_baixo_calao": 3},
    {"insulto_de_baixo_calao": 1},
    {"racismo": 2, "insulto_de_baixo_calao": 1},
    {"homofobia": 3, "insulto_de_baixo_calao": 2},
    {"intolerancia_politica": 2},
    {"xenofobia": 3},
    {"anticapacitismo": 2, "insulto_de_baixo_calao": 2},
    {"violencia_extremismo": 1, "invalido": 1},
    {"misoginia_machismo": 3},
    {"intolerancia_religiosa": 2},
    {"invalido": 3},
]


def textos() -> list[str]:
    return [f"Comentário sintético de teste número {i:02d} sem conteúdo real." for i in range(len(LINHAS))]


def vetor(linha: dict[str, int]) -> list[int]:
    return [int(linha.get(c, 0) >= 2) for c in CLASSES]


def escrever_csvs(pasta: Path, rotacionar_vetor: bool = False) -> tuple[Path, Path]:
    """`rotacionar_vetor=True` simula um CSV cujo vetor segue OUTRA ordem de classes (como sugere o README original)."""
    pasta.mkdir(parents=True, exist_ok=True)
    b, m = pasta / "multidomain_yt_toxbr_binary_sintetico.csv", pasta / "multidomain_yt_toxbr_multilabel_sintetico.csv"
    with b.open("w", encoding="utf-8", newline="") as fb, m.open("w", encoding="utf-8", newline="") as fm:
        wb, wm = csv.writer(fb), csv.writer(fm)
        wb.writerow(["text", "label"])
        wm.writerow(["text", "label"])
        for t, l in zip(textos(), LINHAS):
            v = vetor(l)
            if rotacionar_vetor:
                v = v[1:] + v[:1]
            wb.writerow([t, int(any(v))])
            wm.writerow([t, json.dumps(v)])
    return b, m


def _celula(ref: str, valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, int):
        return f'<c r="{ref}"><v>{valor}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(str(valor))}</t></is></c>'


def escrever_xlsx(caminho: Path, linhas: list[list]) -> None:
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    corpo = []
    for r, linha in enumerate(linhas, start=1):
        celulas = "".join(_celula(f"{letras[c]}{r}", v) for c, v in enumerate(linha))
        corpo.append(f'<row r="{r}">{celulas}</row>')
    folha = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(corpo) + "</sheetData></worksheet>")
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Sheet1" sheetId="1"/></sheets></workbook>')
        z.writestr("xl/worksheets/sheet1.xml", folha)


def escrever_planilhas(pasta: Path) -> list[Path]:
    """Seis planilhas: 1-3 anotam as 6 primeiras linhas (grupo 1), 4-6 as 6 últimas (grupo 2)."""
    pasta.mkdir(parents=True, exist_ok=True)
    saidas = []
    ts = textos()
    for k in range(6):
        grupo, anot = divmod(k, 3)
        linhas = [list(CABECALHO_XLSX)]
        for i in range(grupo * 6, grupo * 6 + 6):
            votos = LINHAS[i]
            marc = [int(anot < votos.get(c, 0)) for c in CLASSES]
            linhas.append([ts[i]] + marc + [int(anot < votos.get("invalido", 0))])
        caminho = pasta / f"comentariosParaAnotacao{k + 1}.xlsx"
        escrever_xlsx(caminho, linhas)
        saidas.append(caminho)
    return saidas
