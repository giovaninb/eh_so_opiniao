"""Comandos adicionais: experimentos, mapeamento, casos, revisão, site e documentação."""

from __future__ import annotations

import argparse
import sys

from . import paths, registry


def cmd_experimentos(args: argparse.Namespace) -> int:
    from .evaluation import experiments, experiments_ampliados as amp

    quais = [q.strip().lower() for q in args.quais.split(",")] if args.quais else None
    classicos = [q for q in quais if q in experiments.EXPERIMENTOS] if quais else list(experiments.EXPERIMENTOS)
    ampliados = [q for q in quais if q in amp.EXPERIMENTOS] if quais else (list(amp.EXPERIMENTOS) if args.ampliados else [])
    desconhecidos = [q for q in (quais or []) if q not in experiments.EXPERIMENTOS and q not in amp.EXPERIMENTOS]
    if desconhecidos:
        print(f"experimento(s) desconhecido(s): {desconhecidos}", file=sys.stderr)
        return 2
    saida = {}
    if classicos:
        saida.update(experiments.executar(classicos))
    if ampliados:
        saida.update(amp.executar(ampliados))
    for chave, r in saida.items():
        estado = r.get("status") if isinstance(r, dict) else None
        print(f"experimento {chave.upper()} -> {paths.RELATORIOS / f'experimento_{chave}.json'}" + (f" [{estado}]" if estado else ""))
    return 0


def cmd_concordancia(args: argparse.Namespace) -> int:
    from .evaluation import concordancia

    r = concordancia.gerar()
    print(f"concordância recalculada -> {paths.RELATORIOS / 'concordancia_multidomain_yt_toxbr.json'} ({len(r)} blocos)")
    return 0


def cmd_sobreposicao(args: argparse.Namespace) -> int:
    from .evaluation import sobreposicao

    sobreposicao.gerar()
    print(f"sobreposição entre corpora -> {paths.RELATORIOS / 'sobreposicao_corpora.json'}")
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


def cmd_participacao(args: argparse.Namespace) -> int:
    from . import participacao
    from .review import store

    conn = store.abrir()
    r = participacao.importar(conn, args.arquivo)
    print(f"participação: {r['resumo']}")
    if r["dados_mascarados"]:
        print(f"dados identificáveis mascarados na importação: {r['dados_mascarados']}")
    print("Frases entram como Pendente e NÃO publicáveis até 'revisao anonimizar'. O CSV original pode ter dados pessoais: apague-o depois.")
    return 0


def cmd_revisao(args: argparse.Namespace) -> int:
    from . import anonimizacao
    from .review import store

    conn = store.abrir()
    try:
        if args.acao == "listar":
            for l in store.listar(conn, args.estado):
                pub = "publicável" if store.publicavel(l) else "não publicável"
                print(f"{l['id']:13s} {l['estado']:9s} {pub:15s} {l['texto'][:80]}")
                if l["origem"] == store.ORIGEM_VISITANTE:
                    nomes = anonimizacao.alertas(l["texto"])
                    print(f"{'':13s} visitante: precisa de 'revisao anonimizar' antes de publicar"
                          + (f"; possíveis nomes: {', '.join(nomes)}" if nomes else ""))
        elif args.acao == "aprovar":
            store.aprovar(conn, args.id, args.revisor, args.nota)
        elif args.acao == "rejeitar":
            store.rejeitar(conn, args.id, args.revisor, args.nota)
        elif args.acao == "ambiguo":
            store.marcar_ambiguo(conn, args.id, args.revisor, args.nota)
        elif args.acao == "corrigir":
            store.corrigir(conn, args.id, args.revisor, [r.strip() for r in args.rotulos.split(",") if r.strip()], args.nota)
        elif args.acao == "anonimizar":
            if not args.texto:
                raise store.RevisaoInvalida("informe --texto com a frase reescrita sem nada que identifique alguém")
            rotulos = None if args.rotulos is None else [r.strip() for r in args.rotulos.split(",") if r.strip()]
            store.anonimizar(conn, args.id, args.revisor, args.texto, args.tipo, rotulos, args.nota)
            print("texto anonimizado. O item continua Pendente: aprove ou corrija para publicar.")
        elif args.acao == "folha":
            from .review import lote

            destino = args.arquivo or str(paths.pasta_revisao() / "folha_de_revisao.csv")
            n = lote.exportar_folha(conn, destino, args.estado or "Pendente", compacta=args.compacta)
            print(f"folha com {n} item(ns) em {destino}. Preencha 'decisao' (aprovar|rejeitar|ambiguo|corrigir) e 'nota'; depois use 'revisao lote'.")
        elif args.acao == "lote":
            from .review import lote

            if not args.arquivo:
                raise store.RevisaoInvalida("informe --arquivo com a folha preenchida")
            r = lote.aplicar_folha(conn, args.arquivo, args.revisor, simular=args.simular, reabrir=args.reabrir,
                                 aprovar_restantes=args.aprovar_restantes)
            if r["erros"]:
                print("NADA foi aplicado. Corrija e rode de novo:\n  " + "\n  ".join(r["erros"]), file=sys.stderr)
                return 2
            print(("SIMULAÇÃO, nada gravado. Previsto: " if r["simulado"] else f"{r['aplicadas']} decisão(ões) gravada(s). ") + str(r["previstas"]))
        elif args.acao == "interativa":
            from .review import lote

            print(lote.interativa(conn, args.revisor))
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
    destino = None
    if args.destino:
        from pathlib import Path

        destino = Path(args.destino)
    r = publicacao.construir_site(conn, destino=destino, incluir_rascunho=args.rascunho)
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
    e = sub.add_parser("experimentos", help="executa experimentos A-E e AMP-A..AMP-G (requer datasets normalizados)")
    e.add_argument("--quais", help="ex.: a,b,amp_g (padrão: A-E; use --ampliados para incluir amp_a..amp_g)")
    e.add_argument("--ampliados", action="store_true", help="sem --quais: roda também os protocolos amp_a..amp_g")
    e.set_defaults(func=cmd_experimentos)
    sub.add_parser("concordancia", help="recalcula a concordância entre anotadores do MultiDomainYT-ToxBR (requer planilhas no cache)").set_defaults(func=cmd_concordancia)
    sub.add_parser("sobreposicao", help="mede sobreposição de textos entre os corpora do cache").set_defaults(func=cmd_sobreposicao)
    sub.add_parser("mapeamento", help="imprime a tabela de correspondência de rótulos").set_defaults(func=cmd_mapeamento)
    c = sub.add_parser("casos", help="enfileira o estudo de caso como Pendente")
    c.add_argument("--com-modelo", action="store_true", help="inclui a sugestão do baseline B (requer corpora normalizados)")
    c.set_defaults(func=cmd_casos)
    p = sub.add_parser("participacao", help="importa o CSV exportado do formulário do site (frases e votos de visitantes)")
    p.add_argument("arquivo")
    p.set_defaults(func=cmd_participacao)
    r = sub.add_parser("revisao", help="revisão humana: listar, aprovar, rejeitar, ambiguo, corrigir, anonimizar, folha, lote, interativa, historico")
    r.add_argument("acao", choices=["listar", "aprovar", "rejeitar", "ambiguo", "corrigir", "anonimizar", "folha", "lote", "interativa", "historico"])
    r.add_argument("--arquivo", help="para folha (saída) e lote (entrada): CSV de revisão em lote")
    r.add_argument("--simular", action="store_true", help="para lote: valida e mostra o que seria feito, sem gravar")
    r.add_argument("--compacta", action="store_true", help="para folha: só id, tema, tipo, texto e rótulos propostos, ordenada por tema")
    r.add_argument("--aprovar-restantes", dest="aprovar_restantes", action="store_true",
                   help="para lote: aprova, em nome do --revisor, as linhas SEM decisão (nota registra 'aprovação em lote'); nunca vale para frases de visitantes")
    r.add_argument("--reabrir", action="store_true", help="para lote: permite decidir itens que já não estão Pendentes")
    r.add_argument("--texto", help="para 'anonimizar': a frase reescrita sem nada que identifique alguém")
    r.add_argument("--tipo", choices=["exclusao", "nao_discriminatoria", "ambigua"], help="para 'anonimizar': tipo editorial")
    r.add_argument("--id")
    r.add_argument("--revisor", default="")
    r.add_argument("--nota")
    r.add_argument("--estado")
    r.add_argument("--rotulos", help="para 'corrigir': ids da taxonomia separados por vírgula")
    r.set_defaults(func=cmd_revisao)
    s = sub.add_parser("site", help="gera os dados do site a partir do que foi revisado")
    s.add_argument("--rascunho", action="store_true", help="gera também rascunho LOCAL com itens ainda não revisados")
    s.add_argument("--destino", help="pasta de saída dos JSON (padrão: site/data)")
    s.set_defaults(func=cmd_site)
    sub.add_parser("docs", help="regenera tabelas e resultados em docs/").set_defaults(func=cmd_docs)
