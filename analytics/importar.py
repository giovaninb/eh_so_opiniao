"""Importa submissões legitimamente acessíveis (CSV, JSON, .eml, fixtures).

Não fala com a API do Formspree. Não pede senha de e-mail. Duplicata operacional
= mesmo conteúdo já importado (hash da linha), não fingerprint de pessoa.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import anonimizacao, casos, participacao, participacao_esquema as esq
from ..paths import dados_locais
from ..review import store
from ..textnorm import hash_chave
from . import eml

_ID = re.compile(r"^[A-Z]{1,3}-\d{1,4}$")


def pasta_arquivo() -> Path:
    p = dados_locais() / "participacoes"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _chave(s: str) -> str:
    n = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", n).strip("_")


def _linhas_csv(caminho: Path) -> list[dict[str, str]]:
    with Path(caminho).open(encoding="utf-8-sig", newline="") as f:
        return [{_chave(k): (v or "").strip() for k, v in linha.items() if k} for linha in csv.DictReader(f)]


def _ler_json(caminho: Path) -> list[dict[str, Any]]:
    bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if isinstance(bruto, list):
        return [x for x in bruto if isinstance(x, dict)]
    if isinstance(bruto, dict):
        if "evaluations" in bruto or "contestations" in bruto or "suggestions" in bruto:
            from .d1 import registros_de_d1
            return registros_de_d1(bruto)
        for k in ("submissions", "registros"):
            if isinstance(bruto.get(k), list):
                return [x for x in bruto[k] if isinstance(x, dict)]
        return [bruto]
    raise ValueError("JSON de submissões precisa ser um objeto, uma lista ou {submissions|registros}")


def ler_arquivo(caminho: Path) -> list[dict[str, Any]]:
    suf = Path(caminho).suffix.lower()
    if suf == ".csv":
        return _linhas_csv(caminho)
    if suf == ".jsonl":
        return [json.loads(l) for l in Path(caminho).read_text(encoding="utf-8").splitlines() if l.strip()]
    if suf == ".json":
        return _ler_json(caminho)
    if suf == ".eml":
        return eml.ler_eml(caminho)
    raise ValueError(f"formato não suportado: {suf or '(sem extensão)'}")


def _tem_proibido(linha: dict[str, Any]) -> str | None:
    mapa = {_chave(str(k)): str(v).strip() for k, v in linha.items()}
    for p in esq.CAMPOS_PROIBIDOS:
        if mapa.get(_chave(p)):
            return p
    return None


def _avaliacoes_de(linha: dict[str, Any]) -> list[dict[str, str]]:
    bruto = linha.get("avaliacoes")
    itens: list[Any] = []
    if isinstance(bruto, str) and bruto.strip():
        try:
            itens = json.loads(bruto)
        except json.JSONDecodeError:
            return []
    elif isinstance(bruto, list):
        itens = bruto
    elif linha.get("frase_id"):
        itens = [linha]
    saida = []
    for it in itens:
        if not isinstance(it, dict):
            continue
        fid = str(it.get("frase_id") or "")
        av = participacao._avaliacao(str(it.get("avaliacao") or ""))
        if not _ID.match(fid) or av is None:
            continue
        saida.append({
            "frase_id": fid,
            "conteudo_versao": str(it.get("conteudo_versao") or "legado"),
            "tema_id": str(it.get("tema_id") or ""),
            "modo": str(it.get("modo") or "desconhecido"),
            "avaliacao": av,
            "contexto_exibido": esq.sim_nao(it.get("contexto_exibido")),
            "analise_revelada": esq.sim_nao(it.get("analise_revelada")),
        })
    return saida


def normalizar(linha: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    tipo = esq.tipo_canonico(str(linha.get("tipo") or ""))
    if not tipo:
        return None, "tipo_ausente"
    if tipo not in esq.TIPOS_V2:
        return None, "tipo_desconhecido"
    if str(linha.get("site") or "").strip():
        return None, "armadilha_preenchida"
    if not esq.consentiu(str(linha.get("consentimento") or "")):
        return None, "sem_consentimento"
    proibido = _tem_proibido(linha)
    if proibido:
        return None, f"campo_proibido_{proibido}"
    schema = str(linha.get("schema_version") or linha.get("schema") or "1").strip() or "1"
    rec: dict[str, Any] = {
        "schema_version": schema,
        "tipo": tipo,
        "consentimento": "sim",
        "aviso_versao": str(linha.get("aviso_versao") or ""),
        "recebido_em": str(linha.get("submitted_at") or linha.get("recebido_em") or linha.get("_date") or ""),
    }
    if tipo == "avaliacoes_voluntarias":
        itens = _avaliacoes_de(linha)
        if not itens:
            return None, "avaliacoes_vazias" if not linha.get("frase_id") else "frase_id_invalido"
        if len(itens) > esq.MAX_AVALIACOES_LOTE:
            return None, "lote_maior_que_cinco"
        rec["avaliacoes"] = itens
        rec["n"] = len(itens)
        return rec, None
    if tipo == "sugestao_frase":
        texto, _ = anonimizacao.mascarar(str(linha.get("frase") or linha.get("texto") or ""))
        if not anonimizacao.tamanho_valido(texto):
            return None, "tamanho_invalido"
        av = participacao._avaliacao(str(linha.get("avaliacao") or linha.get("interpretacao") or linha.get("interpretacao_sugerida") or ""))
        if av is None:
            return None, "avaliacao_invalida"
        ctx, _ = anonimizacao.mascarar(str(linha.get("contexto") or "")[: esq.MAX_CONTEXTO])
        rec.update({"frase": texto, "avaliacao": av, "contexto": ctx})
        return rec, None
    frase_id = str(linha.get("frase_id") or "")
    if not _ID.match(frase_id):
        return None, "frase_id_invalido"
    comentario, _ = anonimizacao.mascarar(str(linha.get("comentario") or linha.get("frase") or "")[: esq.MAX_COMENTARIO])
    motivo = _chave(str(linha.get("motivo") or ""))
    motivo = getattr(esq, "MOTIVO_CANONICO", {}).get(motivo, motivo)
    if motivo and motivo not in esq.MOTIVOS_CONTESTACAO:
        motivo = "outro"
    rec.update({
        "frase_id": frase_id,
        "conteudo_versao": str(linha.get("conteudo_versao") or "legado"),
        "avaliacao_contestada": participacao._avaliacao(str(linha.get("avaliacao_contestada") or linha.get("avaliacao") or "")) or "",
        "motivo": motivo,
        "comentario": comentario,
    })
    return rec, None


def _hash_registro(rec: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _gravar_arquivo(rec: dict[str, Any]) -> None:
    destino = pasta_arquivo() / "submissoes.jsonl"
    with destino.open("a", encoding="utf-8") as f:
        f.write(json.dumps({**rec, "importado_em": _agora()}, ensure_ascii=False) + "\n")


def _garantir_coluna_versao(conn) -> None:
    cols = {c["name"] for c in conn.execute("PRAGMA table_info(votos)")}
    if "conteudo_versao" not in cols:
        conn.execute("ALTER TABLE votos ADD COLUMN conteudo_versao TEXT")
        conn.commit()


def _aplicar_banco(conn, rec: dict[str, Any], chave: str) -> tuple[str, int]:
    tipo = rec["tipo"]
    if tipo == "avaliacoes_voluntarias":
        n = 0
        for i, it in enumerate(rec["avaliacoes"], start=1):
            ck = f"{chave}#{i}"
            if conn.execute("SELECT 1 FROM importadas WHERE chave = ?", (ck,)).fetchone():
                continue
            conn.execute("INSERT INTO votos (frase_id, avaliacao, chave, conteudo_versao) VALUES (?,?,?,?)",
                         (it["frase_id"], it["avaliacao"], ck, it["conteudo_versao"]))
            conn.execute("INSERT INTO importadas (chave, tipo, descartada, quando) VALUES (?,?,?,?)",
                         (ck, "voto", None, _agora()))
            n += 1
        return ("votos", n) if n else ("ja_importadas", 1)
    if tipo == "sugestao_frase":
        if conn.execute("SELECT 1 FROM importadas WHERE chave = ?", (chave,)).fetchone():
            return "ja_importadas", 1
        texto = rec["frase"]
        item_id = "VS-" + hash_chave(texto)[:10]
        rotulos, metodo = casos.sugestao_ia(texto, None)
        novo = store.adicionar(conn, {
            "id": item_id, "origem": store.ORIGEM_VISITANTE, "tipo": participacao.TIPO_SUGERIDO[rec["avaliacao"]],
            "texto": texto, "mecanismo": rec.get("contexto") or None, "ia_rotulos": rotulos, "ia_metodo": metodo,
            "ia_versao": casos.RegrasBaseline.versao, "rotulos_propostos": [],
        })
        conn.execute("INSERT INTO importadas (chave, tipo, descartada, quando) VALUES (?,?,?,?)",
                     (chave, "frase", None, _agora()))
        return ("frases_novas" if novo else "frases_repetidas"), 1
    if conn.execute("SELECT 1 FROM importadas WHERE chave = ?", (chave,)).fetchone():
        return "ja_importadas", 1
    conn.execute("INSERT INTO importadas (chave, tipo, descartada, quando) VALUES (?,?,?,?)",
                 (chave, "contestacao", None, _agora()))
    return "contestacoes", 1


def importar(conn, caminho: Path, modelo_ofensivo=None) -> dict[str, Any]:
    _garantir_coluna_versao(conn)
    resumo: Counter[str] = Counter()
    mascarados: Counter[str] = Counter()
    origem = Path(caminho)
    try:
        linhas = ler_arquivo(origem)
        file_id = hashlib.sha256(origem.read_bytes()).hexdigest()[:12]
    except (ValueError, OSError) as e:
        return {"resumo": {"arquivo_invalido": 1}, "dados_mascarados": {}, "detalhe": str(e)}
    vistas: Counter[str] = Counter()
    for linha in linhas:
        if not isinstance(linha, dict):
            resumo["descartada_json_malformado"] += 1
            continue
        rec, motivo = normalizar(linha)
        if motivo:
            base = hashlib.sha256(json.dumps(linha, sort_keys=True, default=str).encode()).hexdigest()
            vistas[base] += 1
            ck = f"{file_id}#{base}#{vistas[base]}#desc"
            if conn.execute("SELECT 1 FROM importadas WHERE chave = ?", (ck,)).fetchone():
                resumo["ja_importadas"] += 1
                continue
            conn.execute("INSERT INTO importadas (chave, tipo, descartada, quando) VALUES (?,?,?,?)",
                         (ck, str(linha.get("tipo") or "?"), motivo, _agora()))
            resumo[f"descartada_{motivo}"] += 1
            continue
        chave_base = _hash_registro(rec)
        vistas[chave_base] += 1
        chave = f"{file_id}#{chave_base}#{vistas[chave_base]}"
        rec_arq = {k: v for k, v in rec.items()}
        rec_arq["_origem_arquivo"] = origem.name
        rotulo, n = _aplicar_banco(conn, rec, chave)
        if rotulo != "ja_importadas":
            _gravar_arquivo(rec_arq)
            if rec["tipo"] == "avaliacoes_voluntarias" and rec.get("n", 1) > 1:
                resumo["submissoes_lote"] += 1
        resumo[rotulo] += n
        if rec["tipo"] == "sugestao_frase":
            _, achados = anonimizacao.mascarar(str(linha.get("frase") or ""))
            for a in achados:
                mascarados[a] += 1
    conn.commit()
    return {"resumo": dict(resumo), "dados_mascarados": dict(mascarados)}


def ler_arquivo_local() -> list[dict[str, Any]]:
    arq = pasta_arquivo() / "submissoes.jsonl"
    if not arq.exists():
        return []
    saida = []
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            rec = json.loads(linha)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            saida.append(rec)
    return saida
