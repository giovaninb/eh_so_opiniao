"""Gera os dados de TESTE da interface (e2e/.dados/), fora do banco real de revisão.

ATENÇÃO — isto NÃO é publicação. Usa um banco temporário descartável, aprova todos os casos com o revisor
fictício "fixture-e2e" e grava os JSON em e2e/.dados/ (ignorado pelo Git). Serve só para os testes de interface
exercitarem a biblioteca completa (345 casos) e a enquete com votos sintéticos. Nada daqui vai para site/data.
O banco real (datasets/_local/revisao) nunca é tocado, e a publicação real continua exigindo decisão humana.

Uso: ./.venv/bin/python tools/gerar_dados_e2e.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ.parent))

from eh_so_opiniao import casos, participacao, publicacao  # noqa: E402
from eh_so_opiniao.review import store  # noqa: E402

DESTINO = RAIZ / "e2e" / ".dados"
REVISOR_FICTICIO = "fixture-e2e"
# Votos SINTÉTICOS de teste: FR-01 passa do mínimo (aparece); EX-02 não passa (não pode aparecer).
VOTOS = ([("FR-01", "opiniao")] * 3 + [("FR-01", "discriminacao")] * 7 + [("FR-01", "contexto")] * 2 + [("EX-02", "opiniao")] * 3)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        conn = store.abrir(Path(tmp) / "fixture.sqlite3")
        casos.enfileirar(conn)
        for linha in store.listar(conn):
            store.aprovar(conn, linha["id"], REVISOR_FICTICIO, "fixture de teste de interface")
        csv = Path(tmp) / "votos.csv"
        csv.write_text("tipo,frase,avaliacao,frase_id,consentimento,site\n" + "".join(f"voto,,{a},{i},sim,\n" for i, a in VOTOS), encoding="utf-8")
        participacao.importar(conn, csv)
        if DESTINO.exists():
            shutil.rmtree(DESTINO)
        r = publicacao.construir_site(conn, destino=DESTINO, verificar_corpora=False)
        conn.close()
    print(f"dados de teste: {r['frases_publicadas']} frases em {DESTINO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
