"""Adaptador do RacismoBR (UFMG, PROPOR 2026) — CONTRATO validado só com fixtures sintéticas.

STATUS: `pendente_fonte`. O repositório citado no artigo devolve 404 e nenhuma fonte pública foi
encontrada (ver `datasets/registry.yaml`, `fontes_verificadas`). Este adaptador existe para que, quando
os autores liberarem os arquivos pelo protocolo de divulgação responsável, a integração seja trocar o
caminho do arquivo, sem inventar nada agora.

O que é CONHECIDO (artigo): rótulo binário 1 = racista / 0 = não racista, racismo contra pessoas
negras, anotação por pares de pesquisadores negros, corpus original (derivado: 429 racistas + 625 não
racistas = 1.054) e subconjunto experimental balanceado (858 = 429 + 429) que são objetos DISTINTOS.

O que NÃO é conhecido: os nomes reais das colunas e os valores reais do arquivo. O contrato abaixo é uma
suposição declarada, configurável por `mapa_colunas`/`mapa_rotulos`, e recusa o que não bater:

    text     (obrigatória)  texto do post
    label    (obrigatória)  1 = racista, 0 = não racista
    origin   (opcional)     coleta_nova | literatura
    subset   (opcional)     experimental_balanceado | reservatorio
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Mapping

from ..schema import NormalizedTextSample
from .base import AdapterBase, EsquemaInesperado, colunas_csv, ler_csv, sha256_arquivo

COLUNAS_PADRAO = {"text": "text", "label": "label", "origin": "origin", "subset": "subset"}
ROTULOS_PADRAO = {"1": 1, "0": 0}
ORIGENS_CONHECIDAS = ("coleta_nova", "literatura")
SUBCONJUNTOS_CONHECIDOS = ("experimental_balanceado", "reservatorio")
# Valores declarados no artigo (NÃO confirmados por leitura de arquivo).
ESPERADO_NO_ARTIGO = {
    "racista_total": 429, "nao_racista_total": 625, "corpus_original_derivado": 1054,
    "subconjunto_experimental": 858, "subconjunto_racista": 429, "subconjunto_nao_racista": 429,
}


class RacismoBrAdapter(AdapterBase):
    dataset_id = "racismobr"

    def __init__(self, caminho: Path, mapa_colunas: Mapping[str, str] | None = None,
                 mapa_rotulos: Mapping[str, int] | None = None, calcular_hash: bool = True) -> None:
        super().__init__()
        self.caminho = Path(caminho)
        self.colunas = {**COLUNAS_PADRAO, **(mapa_colunas or {})}
        self.rotulos = dict(mapa_rotulos or ROTULOS_PADRAO)
        if not set(self.rotulos.values()) <= {0, 1}:
            raise ValueError("mapa_rotulos deve levar para 0 (não racista) ou 1 (racista)")
        self._sha = sha256_arquivo(self.caminho) if calcular_hash else None
        self.relatorio.update({"contrato": "SUPOSTO (arquivo real não verificado)", "racista": 0, "nao_racista": 0,
                               "por_origem": {}, "por_subconjunto": {}, "subconjunto_experimental": {"racista": 0, "nao_racista": 0}})

    def _opcional(self, linha: dict[str, str], chave: str, validos: tuple[str, ...]) -> str | None:
        coluna = self.colunas[chave]
        if coluna not in linha:
            return None
        valor = (linha.get(coluna) or "").strip()
        if not valor:
            return None
        if valor not in validos:
            raise EsquemaInesperado(f"RacismoBR: valor inesperado em {coluna!r}: {valor!r} (esperado {list(validos)})")
        return valor

    def amostras(self) -> Iterator[NormalizedTextSample]:
        presentes = colunas_csv(self.caminho)
        faltando = [self.colunas[c] for c in ("text", "label") if self.colunas[c] not in presentes]
        if faltando:
            raise EsquemaInesperado(
                f"RacismoBR: colunas ausentes {faltando}; encontrei {presentes}. O contrato é suposto: ajuste mapa_colunas "
                "somente depois de inspecionar o arquivo real.")
        for i, linha in enumerate(ler_csv(self.caminho)):
            self.relatorio["lidas"] += 1
            texto = (linha.get(self.colunas["text"]) or "").strip()
            if not texto:
                self._descartar("texto_vazio")
                continue
            bruto = (linha.get(self.colunas["label"]) or "").strip()
            if bruto not in self.rotulos:
                raise EsquemaInesperado(f"RacismoBR: rótulo inesperado {bruto!r}; valores aceitos {sorted(self.rotulos)}")
            racista = self.rotulos[bruto]
            origem = self._opcional(linha, "origin", ORIGENS_CONHECIDAS)
            subconjunto = self._opcional(linha, "subset", SUBCONJUNTOS_CONHECIDOS)
            a = self._nova(f"racismobr:{i:05d}", texto, plataforma="twitter", arquivo=self.caminho.name, linha=i, sha256=self._sha)
            a.original_labels = {"racist": racista}
            self._normalizar(a, self.dataset_id, "racist", bool(racista), "label_binario_original (racista=1)")
            a.target_groups = ["raca_etnia_pessoas_negras"] if racista else []
            a.context = {"proveniencia": origem or "indisponivel", "subconjunto": subconjunto or "indisponivel"}
            a.annotation_metadata = {
                "n_anotadores": "pares independentes de pesquisadores negros (8 no total); terceiro avaliador nas divergências",
                "definicao": "racismo contra pessoas negras, explícito ou implícito (Almeida, 2019, adaptada)",
                "concordancia_por_item": "indisponivel_na_fonte", "severidade": "indisponivel_na_fonte",
                "contrato_verificado_contra_arquivo_real": False,
            }
            r = self.relatorio
            r["racista" if racista else "nao_racista"] += 1
            r["por_origem"][a.context["proveniencia"]] = r["por_origem"].get(a.context["proveniencia"], 0) + 1
            r["por_subconjunto"][a.context["subconjunto"]] = r["por_subconjunto"].get(a.context["subconjunto"], 0) + 1
            if subconjunto == "experimental_balanceado":
                r["subconjunto_experimental"]["racista" if racista else "nao_racista"] += 1
            r["emitidas"] += 1
            yield a.validar()

    def comparar_com_o_artigo(self) -> dict[str, object]:
        """Compara contagens lidas com as DECLARADAS no artigo. Divergência é informação, nunca é corrigida."""
        r = self.relatorio
        sub = r["subconjunto_experimental"]
        lidas = {"racista_total": r["racista"], "nao_racista_total": r["nao_racista"], "corpus_original_derivado": r["emitidas"],
                 "subconjunto_experimental": sub["racista"] + sub["nao_racista"], "subconjunto_racista": sub["racista"],
                 "subconjunto_nao_racista": sub["nao_racista"]}
        return {c: {"declarado": ESPERADO_NO_ARTIGO[c], "lido": lidas[c], "confere": lidas[c] == ESPERADO_NO_ARTIGO[c]} for c in ESPERADO_NO_ARTIGO}
