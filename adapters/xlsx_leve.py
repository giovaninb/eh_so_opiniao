"""Leitor mínimo de planilhas .xlsx (somente biblioteca padrão; sem pandas/openpyxl).

Lê a primeira planilha como uma tabela de texto/números. Não interpreta fórmulas, estilos nem
várias abas: o suficiente para as planilhas de anotadores do MultiDomainYT-ToxBR.
Células vazias viram `None`. Arquivos que não sejam .xlsx válidos levantam `PlanilhaInvalida`.
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_T = "{%s}t" % _NS["m"]


class PlanilhaInvalida(ValueError):
    pass


def _coluna(ref: str) -> int:
    letras = re.match(r"[A-Z]+", ref or "")
    if not letras:
        raise PlanilhaInvalida(f"referência de célula inválida: {ref!r}")
    n = 0
    for ch in letras.group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def _strings_compartilhadas(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    raiz = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(_T)) for si in raiz.findall("m:si", _NS)]


def _primeira_planilha(z: zipfile.ZipFile) -> str:
    candidatas = sorted(n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))
    if not candidatas:
        raise PlanilhaInvalida("nenhuma planilha encontrada em xl/worksheets")
    return "xl/worksheets/sheet1.xml" if "xl/worksheets/sheet1.xml" in candidatas else candidatas[0]


def ler_xlsx(caminho: Path) -> list[list[str | None]]:
    """Retorna as linhas da primeira planilha (a primeira linha é o cabeçalho)."""
    try:
        z = zipfile.ZipFile(caminho)
    except (zipfile.BadZipFile, OSError) as erro:
        raise PlanilhaInvalida(f"{caminho}: não é um .xlsx válido ({erro})") from erro
    with z:
        compartilhadas = _strings_compartilhadas(z)
        raiz = ET.fromstring(z.read(_primeira_planilha(z)))
    dados = raiz.find("m:sheetData", _NS)
    linhas: list[list[str | None]] = []
    if dados is None:
        return linhas
    for linha in dados:
        celulas: dict[int, str | None] = {}
        for c in linha:
            valor = c.find("m:v", _NS)
            tipo = c.get("t")
            if tipo == "inlineStr":
                texto: str | None = "".join(t.text or "" for t in c.iter(_T))
            elif valor is None or valor.text is None:
                texto = None
            elif tipo == "s":
                texto = compartilhadas[int(valor.text)]
            elif tipo == "b":
                texto = "1" if valor.text == "1" else "0"
            else:
                texto = valor.text
                if texto and re.fullmatch(r"-?\d+\.0+", texto):
                    texto = texto.split(".")[0]
            celulas[_coluna(c.get("r", ""))] = texto
        if celulas:
            largura = max(celulas) + 1
            linhas.append([celulas.get(i) for i in range(largura)])
        else:
            linhas.append([])
    return linhas
