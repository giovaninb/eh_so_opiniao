"""Adaptador do HateBR 2.0 e HateBRXplain (comentários do Instagram; binário ofensivo/não).

- Camadas de nível de ofensa e alvos de ódio existem apenas na versão 1.0 (sob pedido):
  ficam registradas como indisponíveis; não são inventadas.
- Rationales do HateBRXplain são trechos textuais (não offsets). Offsets são DERIVADOS por
  busca no texto e marcados como tais; trechos não localizados são contados, não descartados
  em silêncio.
- O nome da conta/político do arquivo original NÃO é carregado; a publicação vira um hash
  (`post_group`) usado só para evitar vazamento entre splits.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from ..schema import NormalizedTextSample
from ..textnorm import hash_curto
from .base import AdapterBase, EsquemaInesperado, colunas_csv, ler_csv, localizar_trechos, para_int, sha256_arquivo

COLUNAS_HATEBR = ("id", "comentario", "anotator1", "anotator2", "anotator3", "label_final", "links_post")
COLUNAS_XPLAIN = ("id", "comment", "offensive_label", "rationales_annotator1", "rationales_annotator2")


def _trechos(valor: str | None) -> list[str]:
    if valor is None:
        return []
    partes = [p.strip() for p in valor.split(";")]
    return [p for p in partes if p and p.lower() != "n/a"]


class HateBrAdapter(AdapterBase):
    dataset_id = "hatebr"

    def __init__(self, hatebr_csv: Path, xplain_csv: Path | None = None, calcular_hash: bool = True) -> None:
        super().__init__()
        self.hatebr_csv = Path(hatebr_csv)
        self.xplain_csv = Path(xplain_csv) if xplain_csv else None
        self._sha = sha256_arquivo(self.hatebr_csv) if calcular_hash else None
        self.relatorio.update({"xplain_unidas": 0, "xplain_sem_par": 0, "xplain_texto_diferente": 0,
                               "xplain_rotulo_diferente": 0, "rationales_total": 0, "rationales_nao_localizados": 0,
                               "label_final_difere_da_maioria": 0})

    def _carregar_xplain(self) -> dict[str, dict[str, str]]:
        if not self.xplain_csv:
            return {}
        presentes = colunas_csv(self.xplain_csv)
        faltando = [c for c in COLUNAS_XPLAIN if c not in presentes]
        if faltando:
            raise EsquemaInesperado(f"HateBRXplain: colunas ausentes {faltando}")
        return {linha["id"]: linha for linha in ler_csv(self.xplain_csv)}

    def amostras(self) -> Iterator[NormalizedTextSample]:
        presentes = colunas_csv(self.hatebr_csv)
        faltando = [c for c in COLUNAS_HATEBR if c not in presentes]
        if faltando:
            raise EsquemaInesperado(f"HateBR: colunas ausentes {faltando}")
        xplain = self._carregar_xplain()
        for i, linha in enumerate(ler_csv(self.hatebr_csv)):
            self.relatorio["lidas"] += 1
            texto = (linha.get("comentario") or "").strip()
            if not texto:
                self._descartar("texto_vazio")
                continue
            votos = [para_int(linha.get(f"anotator{k}")) for k in (1, 2, 3)]
            final = para_int(linha.get("label_final"))
            if final not in (0, 1) or any(v not in (0, 1) for v in votos):
                self._descartar("rotulos_invalidos")
                continue
            a = self._nova(f"hatebr:{linha['id']}", texto, plataforma="instagram", arquivo=self.hatebr_csv.name, linha=i, sha256=self._sha)
            a.original_labels = {"anotator1": votos[0], "anotator2": votos[1], "anotator3": votos[2], "label_final": final}
            self._normalizar(a, self.dataset_id, "offensive_label", final == 1, "label_final_original")
            maioria = 1 if sum(votos) >= 2 else 0
            if maioria != final:
                self.relatorio["label_final_difere_da_maioria"] += 1
            a.annotation_metadata = {
                "n_anotadores": 3,
                "unanime": len(set(votos)) == 1,
                "camadas_indisponiveis": ["nivel_ofensa", "alvos_de_odio"],
                "versao_com_camadas": "HateBR 1.0 (sob pedido aos autores)",
            }
            a.context = {"post_group": hash_curto(linha.get("links_post") or "sem_post", 10)}
            par = xplain.get(linha["id"])
            if self.xplain_csv and par is None:
                self.relatorio["xplain_sem_par"] += 1
            if par is not None:
                self._anexar_xplain(a, par, texto, final)
            self.relatorio["emitidas"] += 1
            yield a.validar()

    def _anexar_xplain(self, a: NormalizedTextSample, par: dict[str, str], texto: str, final: int) -> None:
        self.relatorio["xplain_unidas"] += 1
        if (par.get("comment") or "").strip() != texto:
            self.relatorio["xplain_texto_diferente"] += 1
        rotulo_x = para_int(par.get("offensive_label"))
        a.original_labels["offensive_label_xplain"] = rotulo_x
        if rotulo_x != final:
            self.relatorio["xplain_rotulo_diferente"] += 1
        r1, r2 = _trechos(par.get("rationales_annotator1")), _trechos(par.get("rationales_annotator2"))
        a.annotation_metadata["rationales"] = {"anotador_1": r1, "anotador_2": r2}
        intervalos, perdidos = localizar_trechos(texto, r1 + r2)
        self.relatorio["rationales_total"] += len(r1) + len(r2)
        self.relatorio["rationales_nao_localizados"] += len(perdidos)
        a.annotation_metadata["rationales_nao_localizados"] = len(perdidos)
        a.annotation_metadata["offsets_origem"] = "derivados_por_busca_textual_no_comentario"
        a.toxic_spans = [{"start": s, "end": e, "origin": "derivado_de_rationale"} for s, e in intervalos]
