"""Participação de visitantes: importa o que chegou pelo formulário e prepara agregados públicos.

Fluxo (nada é publicado automaticamente):
1. O site envia a frase/voto a um formulário externo (privado). Nada fica em repositório público.
2. A pessoa operadora exporta o CSV e roda `participacao importar arquivo.csv`.
3. Frases entram como Pendente, de origem `enviada_por_visitante` (NÃO publicável), já mascaradas;
   o texto original não é guardado. Votos viram só contagem por frase.
4. Revisão humana: `revisao anonimizar` reescreve a frase sem nada identificável; só então ela
   pode ser aprovada. Quem enviou nunca é identificado nem procurado.
5. `site` publica contagens de votos só de frases já publicadas e só com no mínimo `MINIMO_PARA_EXIBIR` votos.
"""

from __future__ import annotations

import csv
import hashlib
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import anonimizacao, casos
from .review import store
from .textnorm import hash_chave

MINIMO_PARA_EXIBIR = 10
AVALIACOES = ("opiniao", "discriminacao", "contexto")
TIPO_SUGERIDO = {"opiniao": "nao_discriminatoria", "discriminacao": "exclusao", "contexto": "ambigua"}
_ID_FRASE = re.compile(r"^[A-Z]{1,3}-\d{1,4}$")
_CONSENTIU = {"sim", "true", "on", "1", "yes", "aceito"}


def _chave_coluna(nome: str) -> str:
    n = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]+", "_", n).strip("_")


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _linhas(caminho: Path) -> list[dict[str, str]]:
    with Path(caminho).open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        return [{_chave_coluna(k): (v or "").strip() for k, v in linha.items() if k} for linha in leitor]


def _avaliacao(valor: str) -> str | None:
    v = _chave_coluna(valor)
    for a, trecho in (("discriminacao", "discrimina"), ("opiniao", "opiniao"), ("contexto", "contexto"), ("contexto", "depende")):
        if trecho in v:
            return a
    return None


def _registrar(conn, chave: str, tipo: str, descartada: str | None = None) -> bool:
    """False se a linha já tinha sido importada."""
    if conn.execute("SELECT 1 FROM importadas WHERE chave = ?", (chave,)).fetchone():
        return False
    conn.execute("INSERT INTO importadas (chave, tipo, descartada, quando) VALUES (?,?,?,?)", (chave, tipo, descartada, _agora()))
    return True


def importar(conn, caminho: Path, modelo_ofensivo=None) -> dict[str, Any]:
    """Importa um CSV de envios. Colunas: tipo (frase|voto), frase, avaliacao, frase_id, consentimento, site (armadilha)."""
    resumo: Counter[str] = Counter()
    mascarados: Counter[str] = Counter()
    vistas: Counter[str] = Counter()
    for linha in _linhas(caminho):
        base = hashlib.sha256("|".join(f"{k}={v}" for k, v in sorted(linha.items())).encode("utf-8")).hexdigest()
        vistas[base] += 1
        chave = f"{base}#{vistas[base]}"  # linhas iguais e legítimas (dois votos iguais) não se fundem
        tipo = _chave_coluna(linha.get("tipo", ""))
        if conn.execute("SELECT 1 FROM importadas WHERE chave = ?", (chave,)).fetchone():
            resumo["ja_importadas"] += 1
            continue
        motivo = None
        if linha.get("site"):
            motivo = "armadilha_preenchida"
        elif _chave_coluna(linha.get("consentimento", "")) not in _CONSENTIU:
            motivo = "sem_consentimento"
        elif tipo not in ("frase", "voto"):
            motivo = "tipo_desconhecido"
        elif _avaliacao(linha.get("avaliacao", "")) is None:
            motivo = "avaliacao_invalida"
        if motivo is None and tipo == "frase":
            texto, achados = anonimizacao.mascarar(linha.get("frase", ""))
            if not anonimizacao.tamanho_valido(texto):
                motivo = "tamanho_invalido"
        elif motivo is None and tipo == "voto" and not _ID_FRASE.match(linha.get("frase_id", "")):
            motivo = "frase_id_invalido"
        if motivo:
            _registrar(conn, chave, tipo or "?", motivo)
            resumo[f"descartada_{motivo}"] += 1
            continue
        avaliacao = _avaliacao(linha["avaliacao"])
        if tipo == "voto":
            conn.execute("INSERT INTO votos (frase_id, avaliacao, chave) VALUES (?,?,?)", (linha["frase_id"], avaliacao, chave))
            _registrar(conn, chave, "voto")
            resumo["votos"] += 1
            continue
        item_id = "VS-" + hash_chave(texto)[:10]
        rotulos, metodo = casos.sugestao_ia(texto, modelo_ofensivo)
        novo = store.adicionar(conn, {
            "id": item_id, "origem": store.ORIGEM_VISITANTE, "tipo": TIPO_SUGERIDO[avaliacao], "texto": texto,
            "mecanismo": None, "ia_rotulos": rotulos, "ia_metodo": metodo, "ia_versao": casos.RegrasBaseline.versao,
            "rotulos_propostos": [],
        })
        _registrar(conn, chave, "frase")
        conn.commit()
        resumo["frases_novas" if novo else "frases_repetidas"] += 1
        for a in achados:
            mascarados[a] += 1
    conn.commit()
    return {"resumo": dict(resumo), "dados_mascarados": dict(mascarados)}


def resultados_publicos(conn, ids_publicados: set[str], minimo: int = MINIMO_PARA_EXIBIR) -> dict[str, Any]:
    """Contagens de votos só de frases já publicadas e só quando n >= minimo (evita expor poucos votos)."""
    por_frase: dict[str, Counter[str]] = {}
    for linha in conn.execute("SELECT frase_id, avaliacao FROM votos"):
        if linha["frase_id"] in ids_publicados:
            por_frase.setdefault(linha["frase_id"], Counter())[linha["avaliacao"]] += 1
    resultados = {}
    for fid, c in sorted(por_frase.items()):
        n = sum(c.values())
        if n >= minimo:
            resultados[fid] = {"n": n, **{a: c.get(a, 0) for a in AVALIACOES}}
    recebidas = conn.execute("SELECT COUNT(*) FROM itens WHERE origem IN (?,?)",
                             (store.ORIGEM_VISITANTE, store.ORIGEM_VISITANTE_ANONIMIZADA)).fetchone()[0]
    return {
        "minimo_para_exibir": minimo,
        "aviso": "Enquete informal e voluntária: não representa a população nem prova nada. Frases de visitantes só aparecem aqui depois de anonimizadas e revisadas por uma pessoa.",
        "frases_recebidas": recebidas,
        "resultados": resultados,
    }
