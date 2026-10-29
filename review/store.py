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

from .. import anonimizacao, paths, registry

ESTADOS = ("Pendente", "Aprovado", "Rejeitado", "Ambíguo", "Corrigido")
ORIGEM_VISITANTE = "enviada_por_visitante"  # texto só mascarado por máquina: NUNCA publicável
ORIGEM_VISITANTE_ANONIMIZADA = "visitante_anonimizada"  # só `anonimizar` (pessoa) chega aqui
ORIGENS_PUBLICAVEIS = ("sintetica_ilustrativa", "fornecida_pelo_operador", ORIGEM_VISITANTE_ANONIMIZADA)
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
        -- Participação: só contagem por frase publicada; nada identifica quem votou.
        CREATE TABLE IF NOT EXISTS votos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, frase_id TEXT NOT NULL, avaliacao TEXT NOT NULL,
            chave TEXT NOT NULL UNIQUE
        );
        -- Linhas já importadas (hash + ordem), para reimportar o mesmo arquivo sem duplicar.
        CREATE TABLE IF NOT EXISTS importadas (chave TEXT PRIMARY KEY, tipo TEXT NOT NULL, descartada TEXT, quando TEXT NOT NULL);
        """
    )
    # Migração leve: metadados editoriais (tema, contexto, razões, o que mudaria a leitura), em JSON.
    if "editorial" not in {c["name"] for c in conn.execute("PRAGMA table_info(itens)")}:
        conn.execute("ALTER TABLE itens ADD COLUMN editorial TEXT")
        conn.commit()
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
           ia_metodo, ia_versao, rotulos_propostos, estado, taxonomia_versao, criado_em, atualizado_em, editorial)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,'Pendente',?,?,?,?)""",
        (item["id"], item["origem"], item.get("tipo"), item["texto"], item.get("mecanismo"), item.get("par_espelho"),
         int(bool(item.get("pode_publicar_ambigua"))), json.dumps(item.get("ia_rotulos", []), ensure_ascii=False),
         item.get("ia_metodo"), item.get("ia_versao"), json.dumps(item.get("rotulos_propostos", []), ensure_ascii=False),
         registry.versao_taxonomia(), agora, agora,
         json.dumps(item["editorial"], ensure_ascii=False) if item.get("editorial") else None),
    )
    conn.commit()
    return True


TIPOS_LEITURA = ("exclusao", "nao_discriminatoria", "ambigua")


def _mudar(conn: sqlite3.Connection, item_id: str, novo: str, revisor: str, nota: str | None, rotulos: list[str] | None = None,
           tipo: str | None = None) -> None:
    if novo not in ESTADOS:
        raise RevisaoInvalida(f"estado inválido: {novo}")
    if not (revisor or "").strip():
        raise RevisaoInvalida("informe o revisor: decisões anônimas não são aceitas")
    linha = conn.execute("SELECT estado, rotulos_propostos, tipo FROM itens WHERE id = ?", (item_id,)).fetchone()
    if linha is None:
        raise RevisaoInvalida(f"item inexistente: {item_id}")
    if tipo is not None and tipo not in TIPOS_LEITURA:
        raise RevisaoInvalida(f"tipo inválido: {tipo}")
    if tipo is not None and novo != "Corrigido":
        raise RevisaoInvalida("só uma correção pode mudar a leitura (tipo) do item")
    if tipo is not None and tipo != linha["tipo"]:
        nota = f"{nota or ''} [leitura alterada pelo revisor: {linha['tipo']} -> {tipo}]".strip()
    origem = conn.execute("SELECT origem FROM itens WHERE id = ?", (item_id,)).fetchone()["origem"]
    if origem == ORIGEM_VISITANTE and novo != "Rejeitado" and novo != "Pendente":
        raise RevisaoInvalida("frase de visitante: anonimize manualmente (revisao anonimizar) antes de aprovar, corrigir ou marcar como ambígua")
    if rotulos is not None:
        invalidos = [r for r in rotulos if r not in registry.rotulos_taxonomia()]
        if invalidos:
            raise RevisaoInvalida(f"rótulos fora da taxonomia: {invalidos}")
    final = rotulos if novo == "Corrigido" else (json.loads(linha["rotulos_propostos"]) if novo == "Aprovado" else None)
    agora = _agora()
    conn.execute("UPDATE itens SET estado=?, revisor=?, nota=?, rotulos_humanos=?, atualizado_em=?, tipo=COALESCE(?, tipo) WHERE id=?",
                 (novo, revisor.strip(), nota, None if final is None else json.dumps(final, ensure_ascii=False), agora, tipo, item_id))
    conn.execute("INSERT INTO historico (item_id, de_estado, para_estado, revisor, nota, quando) VALUES (?,?,?,?,?,?)",
                 (item_id, linha["estado"], novo, revisor.strip(), nota, agora))
    conn.commit()


def aprovar(conn, item_id: str, revisor: str, nota: str | None = None) -> None:
    _mudar(conn, item_id, "Aprovado", revisor, nota)


def rejeitar(conn, item_id: str, revisor: str, nota: str | None = None) -> None:
    _mudar(conn, item_id, "Rejeitado", revisor, nota)


def marcar_ambiguo(conn, item_id: str, revisor: str, nota: str | None = None) -> None:
    _mudar(conn, item_id, "Ambíguo", revisor, nota)


def corrigir(conn, item_id: str, revisor: str, rotulos: list[str], nota: str | None = None, tipo: str | None = None) -> None:
    """Corrige os rótulos e, se `tipo` for informado, a leitura (exclusao | nao_discriminatoria | ambigua). Fica no histórico."""
    _mudar(conn, item_id, "Corrigido", revisor, nota, rotulos, tipo)


def anonimizar(conn, item_id: str, revisor: str, texto: str, tipo: str | None = None,
               rotulos: list[str] | None = None, nota: str | None = None) -> None:
    """Pessoa reescreve a frase de visitante sem nada que identifique alguém. Só depois ela pode ser aprovada.

    O item continua Pendente: anonimizar não aprova. Recusa texto vazio, igual ao atual ou com dado
    identificável mecânico (link, @, telefone...). Nomes próprios só a pessoa revisora consegue julgar.
    """
    if not (revisor or "").strip():
        raise RevisaoInvalida("informe o revisor: decisões anônimas não são aceitas")
    linha = conn.execute("SELECT origem, texto, estado FROM itens WHERE id = ?", (item_id,)).fetchone()
    if linha is None:
        raise RevisaoInvalida(f"item inexistente: {item_id}")
    if linha["origem"] != ORIGEM_VISITANTE:
        raise RevisaoInvalida("só frases de visitantes passam por anonimização manual")
    if linha["estado"] == "Rejeitado":
        raise RevisaoInvalida("item rejeitado: não há o que anonimizar")
    novo = anonimizacao.normalizar_espacos(texto)
    if not anonimizacao.tamanho_valido(novo):
        raise RevisaoInvalida(f"texto deve ter de {anonimizacao.LIMITE_MIN} a {anonimizacao.LIMITE_MAX} caracteres")
    restos = anonimizacao.identificaveis(novo)
    if restos:
        raise RevisaoInvalida(f"o texto ainda contém dado identificável ({', '.join(restos)})")
    if tipo is not None and tipo not in ("exclusao", "nao_discriminatoria", "ambigua"):
        raise RevisaoInvalida(f"tipo inválido: {tipo}")
    if rotulos is not None:
        invalidos = [r for r in rotulos if r not in registry.rotulos_taxonomia()]
        if invalidos:
            raise RevisaoInvalida(f"rótulos fora da taxonomia: {invalidos}")
    agora = _agora()
    conn.execute("UPDATE itens SET texto=?, origem=?, tipo=COALESCE(?, tipo), rotulos_propostos=COALESCE(?, rotulos_propostos), "
                 "revisor=?, atualizado_em=? WHERE id=?",
                 (novo, ORIGEM_VISITANTE_ANONIMIZADA, tipo, None if rotulos is None else json.dumps(rotulos, ensure_ascii=False),
                  revisor.strip(), agora, item_id))
    conn.execute("INSERT INTO historico (item_id, de_estado, para_estado, revisor, nota, quando) VALUES (?,?,?,?,?,?)",
                 (item_id, linha["estado"], linha["estado"], revisor.strip(), nota or "texto anonimizado manualmente", agora))
    conn.commit()


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
