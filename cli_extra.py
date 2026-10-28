"""Comandos adicionais: experimentos, mapeamento, casos, revisão, site e documentação."""

from __future__ import annotations

import argparse
import sys

from . import paths, registry


def cmd_experimentos(args: argparse.Namespace) -> int:
    from .evaluation import experiments

    quais = [q.strip().lower() for q in args.quais.split(",")] if args.quais else None
    saida = experiments.executar(quais)
    for chave in saida:
        print(f"experimento {chave.upper()} -> {paths.RELATORIOS / f'experimento_{chave}.json'}")
    return 0


def cmd_mapeamento(args: argparse.Namespace) -> int:
    from .docsgen import tabela_mapeamento

    registry.validar_mapeamento()
    print(tabela_mapeamento())
    return 0


def cmd_casos(args: argparse.Namespace) -> int:
    from . import casos
    from .review import store

    modelo = casos.modelo_ofensivo_local() if args.com_modelo else None
    if args.com_modelo and modelo is None:
        print("aviso: corpora não normalizados; seguindo só com o baseline A (regras).", file=sys.stderr)
    conn = store.abrir()
    r = casos.enfileirar(conn, modelo_ofensivo=modelo)
    print(f"casos: {r['total']} no arquivo, {r['novos']} novos na fila (todos como Pendente).")
    return 0


def cmd_revisao(args: argparse.Namespace) -> int:
    from .review import store

    conn = store.abrir()
    try:
        if args.acao == "listar":
            for l in store.listar(conn, args.estado):
                pub = "publicável" if store.publicavel(l) else "não publicável"
                print(f"{l['id']:7s} {l['estado']:9s} {pub:15s} {l['texto'][:80]}")
        elif args.acao == "aprovar":
            store.aprovar(conn, args.id, args.revisor, args.nota)
        elif args.acao == "rejeitar":
            store.rejeitar(conn, args.id, args.revisor, args.nota)
        elif args.acao == "ambiguo":
            store.marcar_ambiguo(conn, args.id, args.revisor, args.nota)
        elif args.acao == "corrigir":
            store.corrigir(conn, args.id, args.revisor, [r.strip() for r in args.rotulos.split(",") if r.strip()], args.nota)
        elif args.acao == "historico":
            for h in store.historico(conn, args.id):
                print(f"{h['quando']} {h['de_estado']} -> {h['para_estado']} por {h['revisor']}: {h['nota'] or ''}")
    except store.RevisaoInvalida as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 2
    return 0


def cmd_site(args: argparse.Namespace) -> int:
    from . import publicacao
    from .review import store

    conn = store.abrir()
    r = publicacao.construir_site(conn, incluir_rascunho=args.rascunho)
    print(f"site: {r['frases_publicadas']} frase(s) revisada(s) publicada(s) em {r['destino']}")
    if args.rascunho:
        print(f"      {r['frases_rascunho_local']} frase(s) em rascunho LOCAL (data/_rascunho, não versionado). Abra com ?rascunho=1")
    return 0


def cmd_docs(args: argparse.Namespace) -> int:
    from . import docsgen

    for arq in docsgen.gerar_documentos():
        print(f"documento atualizado: {arq}")
    return 0


def registrar(sub: argparse._SubParsersAction) -> None:
    e = sub.add_parser("experimentos", help="executa experimentos A-E (requer datasets normalizados)")
    e.add_argument("--quais", help="ex.: a,b,c (padrão: todos)")
    e.set_defaults(func=cmd_experimentos)
    sub.add_parser("mapeamento", help="imprime a tabela de correspondência de rótulos").set_defaults(func=cmd_mapeamento)
    c = sub.add_parser("casos", help="enfileira o estudo de caso como Pendente")
    c.add_argument("--com-modelo", action="store_true", help="inclui a sugestão do baseline B (requer corpora normalizados)")
    c.set_defaults(func=cmd_casos)
    r = sub.add_parser("revisao", help="revisão humana: listar, aprovar, rejeitar, ambiguo, corrigir, historico")
    r.add_argument("acao", choices=["listar", "aprovar", "rejeitar", "ambiguo", "corrigir", "historico"])
    r.add_argument("--id")
    r.add_argument("--revisor", default="")
    r.add_argument("--nota")
    r.add_argument("--estado")
    r.add_argument("--rotulos", help="para 'corrigir': ids da taxonomia separados por vírgula")
    r.set_defaults(func=cmd_revisao)
    s = sub.add_parser("site", help="gera os dados do site a partir do que foi revisado")
    s.add_argument("--rascunho", action="store_true", help="gera também rascunho LOCAL com itens ainda não revisados")
    s.set_defaults(func=cmd_site)
    sub.add_parser("docs", help="regenera tabelas e resultados em docs/").set_defaults(func=cmd_docs)
