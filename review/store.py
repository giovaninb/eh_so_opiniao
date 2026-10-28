"""Revisão humana: fila de itens, estados e trilha de auditoria (SQLite local, não versionado).

Estados: Pendente, Aprovado, Rejeitado, Ambíguo, Corrigido.
Regras:
- Todo item entra como Pendente. Resultado de IA nunca é publicado sem decisão humana.
- Só publica: Aprovado e Corrigido (e Ambíguo apenas se o item permite expor 'ambígua').
- Origem restrita: só textos de origens permitidas são publicáveis. Texto de corpora
  científicos NUNCA é publicável (nem se aprovado).
- Toda mudança de estado exige nome do revisor e fica registrada no histórico.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import paths, registry

ESTADOS = ("Pendente", "Aprovado", "Rejeitado", "Ambíguo", "Corrigido")
ORIGENS_PUBLICAVEIS = ("sintetica_ilustrativa", "fornecida_pelo_operador")
PUBLICAVEIS = ("Aprovado", "Corrigido")


class RevisaoInvalida(ValueError):
    pass


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def caminho_padrao() -> Path:
    return paths.pasta_revisao() / "revisao.sqlite3"


def abrir(caminho: Path | None = None) -> sqlite3.Connection:
    caminho = caminho or caminho_padrao()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS itens (
            id TEXT PRIMARY KEY, origem TEXT NOT NULL, tipo TEXT, texto TEXT NOT NULL,
            mecanismo TEXT, par_espelho TEXT, pode_publicar_ambigua INTEGER NOT NULL DEFAULT 0,
            ia_rotulos TEXT NOT NULL DEFAULT '[]', ia_metodo TEXT, ia_versao TEXT,
            rotulos_propostos TEXT NOT NULL DEFAULT '[]', rotulos_humanos TEXT,
            estado TEXT NOT NULL DEFAULT 'Pendente', nota TEXT, revisor TEXT,
            taxonomia_versao TEXT, criado_em TEXT NOT NULL, atualizado_em TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item_id TEXT NOT NULL, de_estado TEXT, para_estado TEXT NOT NULL,
            revisor TEXT NOT NULL, nota TEXT, quando TEXT NOT NULL
        );
        """
    )
    return conn


def adicionar(conn: sqlite3.Connection, item: dict[str, Any]) -> bool:
    """Insere item como Pendente. Retorna False se já existe (idempotente, não sobrescreve decisões)."""
    if item["origem"] in registry.listar_datasets():
        raise RevisaoInvalida("textos de corpora científicos não entram na fila de publicação")
    if conn.execute("SELECT 1 FROM itens WHERE id = ?", (item["id"],)).fetchone():
        return False
    agora = _agora()
    conn.execute(
        """INSERT INTO itens (id, origem, tipo, texto, mecanismo, par_espelho, pode_publicar_ambigua, ia_rotulos,
           ia_metodo, ia_versao, rotulos_propostos, estado, taxonomia_versao, criado_em, atualizado_em)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,'Pendente',?,?,?)""",
        (item["id"], item["origem"], item.get("tipo"), item["texto"], item.get("mecanismo"), item.get("par_espelho"),
         int(bool(item.get("pode_publicar_ambigua"))), json.dumps(item.get("ia_rotulos", []), ensure_ascii=False),
         item.get("ia_metodo"), item.get("ia_versao"), json.dumps(item.get("rotulos_propostos", []), ensure_ascii=False),
         registry.versao_taxonomia(), agora, agora),
    )
    conn.commit()
    return True


def _mudar(conn: sqlite3.Connection, item_id: str, novo: str, revisor: str, nota: str | None, rotulos: list[str] | None = None) -> None:
    if novo not in ESTADOS:
        raise RevisaoInvalida(f"estado inválido: {novo}")
    if not (revisor or "").strip():
        raise RevisaoInvalida("informe o revisor: decisões anônimas não são aceitas")
    linha = conn.execute("SELECT estado, rotulos_propostos FROM itens WHERE id = ?", (item_id,)).fetchone()
    if linha is None:
        raise RevisaoInvalida(f"item inexistente: {item_id}")
    if rotulos is not None:
        invalidos = [r for r in rotulos if r not in registry.rotulos_taxonomia()]
        if invalidos:
            raise RevisaoInvalida(f"rótulos fora da taxonomia: {invalidos}")
    final = rotulos if novo == "Corrigido" else (json.loads(linha["rotulos_propostos"]) if novo == "Aprovado" else None)
    agora = _agora()
    conn.execute("UPDATE itens SET estado=?, revisor=?, nota=?, rotulos_humanos=?, atualizado_em=? WHERE id=?",
                 (novo, revisor.strip(), nota, None if final is None else json.dumps(final, ensure_ascii=False), agora, item_id))
    conn.execute("INSERT INTO historico (item_id, de_estado, para_estado, revisor, nota, quando) VALUES (?,?,?,?,?,?)",
                 (item_id, linha["estado"], novo, revisor.strip(), nota, agora))
    conn.commit()


def aprovar(conn, item_id: str, revisor: str, nota: str | None = None) -> None:
    _mudar(conn, item_id, "Aprovado", revisor, nota)


def rejeitar(conn, item_id: str, revisor: str, nota: str | None = None) -> None:
    _mudar(conn, item_id, "Rejeitado", revisor, nota)


def marcar_ambiguo(conn, item_id: str, revisor: str, nota: str | None = None) -> None:
    _mudar(conn, item_id, "Ambíguo", revisor, nota)


def corrigir(conn, item_id: str, revisor: str, rotulos: list[str], nota: str | None = None) -> None:
    _mudar(conn, item_id, "Corrigido", revisor, nota, rotulos)


def listar(conn: sqlite3.Connection, estado: str | None = None) -> list[sqlite3.Row]:
    if estado:
        return conn.execute("SELECT * FROM itens WHERE estado = ? ORDER BY id", (estado,)).fetchall()
    return conn.execute("SELECT * FROM itens ORDER BY id").fetchall()


def publicavel(linha: sqlite3.Row) -> bool:
    if linha["origem"] not in ORIGENS_PUBLICAVEIS:
        return False
    if linha["estado"] in PUBLICAVEIS:
        return True
    return linha["estado"] == "Ambíguo" and bool(linha["pode_publicar_ambigua"])


def historico(conn: sqlite3.Connection, item_id: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM historico WHERE item_id = ? ORDER BY id", (item_id,)).fetchall()
