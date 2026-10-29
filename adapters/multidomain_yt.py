"""Adaptador do MultiDomainYT-ToxBR (PUCRS, 2026): 5.000 comentários do YouTube, nove categorias.

Fatos verificados nos arquivos reais (ver `datasets/registry.yaml`, `ficha_cientifica`):
- `multiDomainYtBinary.csv`: `text,label` com label 0/1 (1 = qualquer categoria com consenso).
- `multiDomainYtMultilabel.csv`: `text,label` com label = vetor de 9 inteiros, SEM nomes de classe.
- A ORDEM do vetor é a das planilhas dos anotadores (insulto, homofobia, racismo, misoginia, xenofobia,
  violência, intolerância religiosa, intolerância política, anticapacitismo) e NÃO a descrita no README
  (que cita "obsceno" e omite "anticapacitismo"). Com as seis planilhas, o adaptador reconstrói o consenso
  por maioria e CONFERE o vetor posição a posição; se não bater, recusa o arquivo em vez de rotular errado.
- Rótulos normalizados são todos `aproximado` (ver `label_mapping.yaml`).
- Concordância entre anotadores só existe nas planilhas (votos 0-3 por categoria, 3 anotadores por
  comentário, dois grupos independentes); fica em `annotation_metadata`.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterator, Sequence

from ..schema import NormalizedTextSample
from .base import AdapterBase, EsquemaInesperado, colunas_csv, ler_csv, sha256_arquivo
from .xlsx_leve import PlanilhaInvalida, ler_xlsx

# ORDEM VERIFICADA do vetor multirrótulo (não a do README). Não reordene sem refazer a verificação.
CLASSES_VETOR = (
    "insulto_de_baixo_calao", "homofobia", "racismo", "misoginia_machismo", "xenofobia",
    "violencia_extremismo", "intolerancia_religiosa", "intolerancia_politica", "anticapacitismo",
)
ORDEM_DO_README = ("insulto", "obsceno", "homofobia", "racismo", "misoginia", "xenofobia", "violencia",
                   "intolerancia_religiosa", "intolerancia_politica")  # documentada só para auditoria: NÃO usar
MODOS = ("binario", "multilabel", "ambos")
N_ANOTADORES_POR_GRUPO = 3
LIMIAR_CONSENSO = 2  # maioria de 3, regra dos autores (notebook 3_Tratamento)
TOLERANCIA_ORDEM = 0.98  # fração mínima de concordância por posição ao conferir o vetor com as planilhas
GRUPOS_ALVO = {
    "homofobia": "orientacao_sexual_identidade_genero", "racismo": "raca_etnia", "misoginia_machismo": "mulheres",
    "xenofobia": "origem_nacional_regional", "intolerancia_religiosa": "crenca_religiosa",
    "intolerancia_politica": "orientacao_politica", "anticapacitismo": "pessoas_com_deficiencia",
}
_ALIAS_COLUNAS = {
    "insulto de baixo calao": "insulto_de_baixo_calao", "homofobia": "homofobia", "racismo": "racismo",
    "misoginia/machismo": "misoginia_machismo", "xenofobia": "xenofobia", "violencia/extremismo": "violencia_extremismo",
    "intolerancia religiosa": "intolerancia_religiosa", "intolerancia politica": "intolerancia_politica",
    "anticapacitismo": "anticapacitismo", "invalido": "invalido", "comentario": "comentario",
}


def _chave_coluna(cabecalho: str | None) -> str:
    t = unicodedata.normalize("NFKD", cabecalho or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", re.sub(r"\s*/\s*", "/", t.replace("\n", " "))).strip()


def _para_voto(valor: str | None) -> int | None:
    if valor is None:
        return None
    t = str(valor).strip().lower()
    if t in ("0", "false"):
        return 0
    if t in ("1", "true"):
        return 1
    return None


def carregar_votos(arquivos: Sequence[Path]) -> list[dict[str, Any]]:
    """Lê as seis planilhas (3 por grupo) e devolve uma linha por comentário, na ordem do corpus.

    Cada item: {"grupo": 1|2, "texto": str, "votos": {classe: 0-3}, "invalido": 0-3,
    "votos_ausentes": n, "textos_divergentes_entre_anotadores": bool}. Sem identificar anotadores
    além do número de ordem da planilha.
    """
    arquivos = [Path(a) for a in arquivos]
    if len(arquivos) != 2 * N_ANOTADORES_POR_GRUPO:
        raise ValueError("esperadas 6 planilhas de anotadores (3 do grupo 1 e 3 do grupo 2), na ordem 1..6")
    saida: list[dict[str, Any]] = []
    for grupo in (1, 2):
        tabelas = []
        for caminho in arquivos[(grupo - 1) * 3: grupo * 3]:
            try:
                linhas = ler_xlsx(caminho)
            except PlanilhaInvalida as erro:
                raise EsquemaInesperado(str(erro)) from erro
            if not linhas:
                raise EsquemaInesperado(f"{caminho.name}: planilha vazia")
            chaves = [_ALIAS_COLUNAS.get(_chave_coluna(h)) for h in linhas[0]]
            faltando = [c for c in (*CLASSES_VETOR, "invalido", "comentario") if c not in chaves]
            if faltando:
                raise EsquemaInesperado(f"{caminho.name}: colunas ausentes {faltando}")
            tabelas.append((chaves, linhas[1:]))
        n = {len(corpo) for _, corpo in tabelas}
        if len(n) != 1:
            raise EsquemaInesperado(f"grupo {grupo}: planilhas com números de linhas diferentes {sorted(n)}")
        for i in range(n.pop()):
            votos = {c: 0 for c in CLASSES_VETOR}
            invalido = ausentes = 0
            textos = set()
            for chaves, corpo in tabelas:
                linha = corpo[i] + [None] * (len(chaves) - len(corpo[i]))
                por_coluna = dict(zip(chaves, linha))
                textos.add((por_coluna.get("comentario") or "").strip())
                for c in CLASSES_VETOR:
                    v = _para_voto(por_coluna.get(c))
                    if v is None:
                        ausentes += 1
                    else:
                        votos[c] += v
                iv = _para_voto(por_coluna.get("invalido"))
                invalido += iv or 0
            texto = sorted(textos, key=lambda t: (-len(t), t))[0]
            saida.append({"grupo": grupo, "texto": texto, "votos": votos, "invalido": invalido,
                          "votos_ausentes": ausentes, "textos_divergentes_entre_anotadores": len(textos) > 1})
    return saida


def _vetor(valor: str | None) -> list[int] | None:
    try:
        v = json.loads(valor or "")
    except (ValueError, TypeError):
        return None
    if isinstance(v, list) and all(x in (0, 1) and not isinstance(x, bool) for x in v):
        return [int(x) for x in v]
    return None


class MultiDomainYtToxBrAdapter(AdapterBase):
    dataset_id = "multidomain_yt_toxbr"

    def __init__(self, binario_csv: Path | None = None, multilabel_csv: Path | None = None,
                 anotacoes_xlsx: Sequence[Path] | None = None, modo: str = "ambos", calcular_hash: bool = True) -> None:
        super().__init__()
        if modo not in MODOS:
            raise ValueError(f"modo desconhecido: {modo} (use {list(MODOS)})")
        self.modo = modo
        self.binario_csv = Path(binario_csv) if binario_csv else None
        self.multilabel_csv = Path(multilabel_csv) if multilabel_csv else None
        self.anotacoes_xlsx = [Path(a) for a in anotacoes_xlsx] if anotacoes_xlsx else None
        if modo == "binario" and not self.binario_csv:
            raise ValueError("modo 'binario' exige binario_csv")
        if modo == "multilabel" and not self.multilabel_csv:
            raise ValueError("modo 'multilabel' exige multilabel_csv")
        if modo == "ambos" and not (self.binario_csv or self.multilabel_csv):
            raise ValueError("informe ao menos um dos CSVs")
        if self.anotacoes_xlsx is not None and len(self.anotacoes_xlsx) != 6:
            raise ValueError("anotacoes_xlsx deve ter as 6 planilhas (ou ser None)")
        principal = self.multilabel_csv or self.binario_csv
        self._sha = sha256_arquivo(principal) if calcular_hash and principal else None
        self.relatorio.update({
            "modo": modo, "binario_difere_de_qualquer_categoria": 0, "textos_diferentes_entre_csv": 0,
            "texto_xlsx_difere_do_csv": 0, "ordem_vetor": "nao_verificavel_sem_planilhas (ordem registrada usada)",
            "concordancia_ordem_por_classe": {}, "textos_duplicados_exatos": 0,
        })

    # ---------------------------------------------------------------- leitura
    def _ler_binario(self) -> list[tuple[str, int | None]]:
        if not self.binario_csv:
            return []
        faltando = [c for c in ("text", "label") if c not in colunas_csv(self.binario_csv)]
        if faltando:
            raise EsquemaInesperado(f"MultiDomainYT binário: colunas ausentes {faltando}")
        saida = []
        for linha in ler_csv(self.binario_csv):
            r = (linha.get("label") or "").strip()
            saida.append((linha.get("text") or "", int(r) if r in ("0", "1") else None))
        return saida

    def _ler_multilabel(self) -> list[tuple[str, list[int] | None]]:
        if not self.multilabel_csv:
            return []
        faltando = [c for c in ("text", "label") if c not in colunas_csv(self.multilabel_csv)]
        if faltando:
            raise EsquemaInesperado(f"MultiDomainYT multilabel: colunas ausentes {faltando}")
        linhas = [(linha.get("text") or "", _vetor(linha.get("label"))) for linha in ler_csv(self.multilabel_csv)]
        primeiro = next((v for _, v in linhas if v is not None), None)
        if primeiro is not None and len(primeiro) != len(CLASSES_VETOR):
            raise EsquemaInesperado(
                f"MultiDomainYT: vetor com {len(primeiro)} posições; o adaptador conhece {len(CLASSES_VETOR)} "
                "(ordem verificada em registry.yaml). Refaça a verificação da ordem antes de mapear.")
        return linhas

    def _conferir_ordem(self, vetores: list[list[int] | None], votos: list[dict[str, Any]]) -> None:
        total = {c: 0 for c in CLASSES_VETOR}
        iguais = {c: 0 for c in CLASSES_VETOR}
        for v, vt in zip(vetores, votos):
            if v is None:
                continue
            for pos, c in enumerate(CLASSES_VETOR):
                total[c] += 1
                iguais[c] += int(v[pos] == int(vt["votos"][c] >= LIMIAR_CONSENSO))
        frac = {c: round(iguais[c] / total[c], 4) if total[c] else 0.0 for c in CLASSES_VETOR}
        self.relatorio["concordancia_ordem_por_classe"] = frac
        ruins = {c: f for c, f in frac.items() if f < TOLERANCIA_ORDEM}
        if ruins:
            raise EsquemaInesperado(
                "a ordem registrada do vetor NÃO confere com o consenso das planilhas (fração por classe: "
                f"{ruins}). Não rotular: verifique a ordem real das categorias.")
        self.relatorio["ordem_vetor"] = "confirmada_pelas_planilhas"

    # ------------------------------------------------------------- amostras
    def amostras(self) -> Iterator[NormalizedTextSample]:
        multi = self._ler_multilabel() if self.modo in ("multilabel", "ambos") else []
        binario = self._ler_binario() if self.modo in ("binario", "ambos") else []
        n_linhas = len(multi) or len(binario)
        if multi and binario and len(multi) != len(binario):
            raise EsquemaInesperado(f"CSV binário ({len(binario)}) e multilabel ({len(multi)}) com números de linhas diferentes")
        votos: list[dict[str, Any]] = []
        if self.anotacoes_xlsx is not None:
            votos = carregar_votos(self.anotacoes_xlsx)
            if len(votos) != n_linhas:
                raise EsquemaInesperado(f"planilhas ({len(votos)} comentários) e CSV ({n_linhas}) não têm o mesmo tamanho")
            if multi:
                self._conferir_ordem([v for _, v in multi], votos)
        vistos: set[str] = set()
        for i in range(n_linhas):
            self.relatorio["lidas"] += 1
            texto = (multi[i][0] if multi else binario[i][0]).strip()
            if multi and binario and multi[i][0].strip() != binario[i][0].strip():
                self.relatorio["textos_diferentes_entre_csv"] += 1
            if not texto:
                self._descartar("texto_vazio")
                continue
            vetor = multi[i][1] if multi else None
            rotulo_bin = binario[i][1] if binario else None
            if multi and vetor is None:
                self._descartar("vetor_invalido")
                continue
            if binario and rotulo_bin is None:
                self._descartar("rotulo_binario_invalido")
                continue
            if vetor is not None and rotulo_bin is not None and int(any(vetor)) != rotulo_bin:
                self.relatorio["binario_difere_de_qualquer_categoria"] += 1
            if texto in vistos:
                self.relatorio["textos_duplicados_exatos"] += 1
            vistos.add(texto)
            a = self._nova(f"{self.dataset_id}:{i:05d}", texto, plataforma="youtube", arquivo=(self.multilabel_csv or self.binario_csv).name, linha=i, sha256=self._sha)
            a.original_labels = {}
            if rotulo_bin is not None:
                a.original_labels["label_binario"] = rotulo_bin
            if vetor is not None:
                a.original_labels["vetor_multirrotulo"] = list(vetor)
                a.original_labels["classes"] = {c: vetor[p] for p, c in enumerate(CLASSES_VETOR)}
                for c in CLASSES_VETOR:
                    self._normalizar(a, self.dataset_id, c, bool(a.original_labels["classes"][c]), "consenso_dos_autores (>=2 de 3 anotadores; vetor do CSV)")
                a.target_groups = [g for c, g in GRUPOS_ALVO.items() if a.original_labels["classes"][c]]
            toxico = bool(rotulo_bin) if rotulo_bin is not None else bool(any(vetor or []))
            fonte = "label_binario" if rotulo_bin is not None else "qualquer_categoria_do_vetor"
            self._normalizar(a, self.dataset_id, "toxico_qualquer_categoria", toxico,
                             f"consenso_dos_autores (qualquer categoria com >=2 de 3 anotadores; origem: {fonte})", list(CLASSES_VETOR))
            meta: dict[str, Any] = {
                "n_anotadores": N_ANOTADORES_POR_GRUPO, "politica_consenso": f"maioria (>={LIMIAR_CONSENSO} de {N_ANOTADORES_POR_GRUPO})",
                "dominio_tematico": "indisponivel_na_fonte", "id_do_video": "indisponivel_na_fonte",
                "severidade": "indisponivel_na_fonte", "ordem_vetor": self.relatorio["ordem_vetor"],
            }
            if votos:
                vt = votos[i]
                if vt["textos_divergentes_entre_anotadores"]:
                    self.relatorio.setdefault("textos_divergentes_entre_anotadores", 0)
                    self.relatorio["textos_divergentes_entre_anotadores"] += 1
                if vt["texto"].strip() != texto:
                    self.relatorio["texto_xlsx_difere_do_csv"] += 1
                meta.update({
                    "grupo_anotadores": vt["grupo"], "votos_por_classe": dict(vt["votos"]),
                    "classes_com_dissenso": [c for c, n in vt["votos"].items() if 0 < n < N_ANOTADORES_POR_GRUPO],
                    "votos_binarios_qualquer_categoria": sum(1 for c in CLASSES_VETOR if vt["votos"][c] > 0),
                    "votos_invalido": vt["invalido"], "votos_ausentes": vt["votos_ausentes"],
                    "unanime_em_todas_as_classes": all(n in (0, N_ANOTADORES_POR_GRUPO) for n in vt["votos"].values()),
                })
            else:
                meta["concordancia"] = "indisponivel_sem_planilhas_dos_anotadores"
            a.annotation_metadata = meta
            self.relatorio["emitidas"] += 1
            yield a.validar()
