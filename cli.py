"""Linha de comando: `python -m eh_so_opiniao <comando>`."""

from __future__ import annotations

import argparse
import json
import sys

from . import paths, registry
from .pipeline import download, normalize


def _imprimir(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_datasets(args: argparse.Namespace) -> int:
    registry.validar_mapeamento()
    estado = download.estado_geral()
    for ds_id in registry.listar_datasets():
        info = registry.dataset(ds_id)
        print(f"{ds_id:10s} | {info['licenca'][:18]:18s} | acesso={info['acesso']:21s} | catálogo={info['status_acesso']:24s} | "
              f"cache={'sim' if estado[ds_id]['no_cache'] else 'não'} | registros={info['registros_confirmados']}")
    return 0


def cmd_baixar(args: argparse.Namespace) -> int:
    alvos = [args.dataset] if args.dataset else registry.listar_datasets()
    codigo = 0
    for ds_id in alvos:
        for r in download.baixar(ds_id, forcar=args.forcar):
            print(f"[{ds_id}] {r.arquivo}: {r.status} {r.detalhe}")
            if r.status in ("falha_integridade", "falha_rede"):
                codigo = 1
    return codigo


def cmd_normalizar(args: argparse.Namespace) -> int:
    relatorio = normalize.normalizar_todos() if not args.dataset else {args.dataset: normalize.normalizar_dataset(args.dataset)}
    for ds_id, r in relatorio.items():
        print(f"[{ds_id}] {r['status']}: {r['amostras']} amostras")
    if args.json:
        _imprimir(relatorio)
    return 0


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eh_so_opiniao", description="É Só Opinião? — observatório de pesquisa")
    p.add_argument("--dados", help="diretório de dados locais (sobrescreve ESO_DATA_DIR)")
    sub = p.add_subparsers(dest="comando", required=True)
    sub.add_parser("datasets", help="lista o catálogo e o estado no cache").set_defaults(func=cmd_datasets)
    b = sub.add_parser("baixar", help="baixa datasets abertos (cache + integridade)")
    b.add_argument("--dataset")
    b.add_argument("--forcar", action="store_true")
    b.set_defaults(func=cmd_baixar)
    n = sub.add_parser("normalizar", help="gera JSONL normalizado a partir do cache")
    n.add_argument("--dataset")
    n.add_argument("--json", action="store_true")
    n.set_defaults(func=cmd_normalizar)
    from . import cli_extra  # comandos adicionais (experimentos, revisão, site)

    cli_extra.registrar(sub)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.dados:
        import os
        os.environ["ESO_DATA_DIR"] = args.dados
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
