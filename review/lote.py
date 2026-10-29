"""Revisão em lote: planilha local para decidir vários itens, sem abrir mão da decisão por item.

- `exportar_folha` grava um CSV (local, fora do Git) com cada item Pendente e colunas em branco para a decisão.
- `aplicar_folha` lê as decisões e aplica uma a uma pelas MESMAS funções de `store`, então cada item mantém
  revisor, justificativa e histórico. Se qualquer linha for inválida, NADA é aplicado (tudo ou nada).
- `interativa` percorre os itens no terminal, um por vez.

Nenhuma função aqui aprova sozinha: toda aprovação precisa de uma decisão explícita de uma pessoa identificada.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Callable

from .. import registry
from . import store

SEM_DISCRIMINACAO = "sem_discriminacao"  # em rotulos_finais: a leitura final é "sem discriminação" (tipo nao_discriminatoria)
DECISOES = {"aprovar": store.aprovar, "rejeitar": store.rejeitar, "ambiguo": store.marcar_ambiguo, "corrigir": None}
COLUNAS_COMPACTAS = ["id", "tema", "tipo", "texto", "rotulos_propostos", "decisao", "rotulos_finais", "nota"]
NOTA_APROVACAO_EM_LOTE = "aprovada em lote pelo revisor após ler a folha compacta (sem decisão item a item)"
COLUNAS = ["id", "tema", "tipo", "texto", "contexto", "mecanismo", "razoes", "muda_se", "rotulos_propostos", "sugestao_ia",
           "decisao", "rotulos_finais", "nota"]


def _nomes(ids: list[str]) -> str:
    tax = registry.rotulos_taxonomia()
    return "; ".join(tax[i]["nome"] if i in tax else i for i in ids)


def exportar_folha(conn, caminho: Path, estado: str = "Pendente", compacta: bool = False) -> int:
    """Grava a folha de revisão. `compacta`: só o essencial (id, tema, tipo, texto, rótulos propostos), ordenada por
    tema, para ler rápido e marcar apenas o que NÃO deve ser aprovado (ver `aprovar_restantes` em `aplicar_folha`)."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linhas = store.listar(conn, estado)
    if compacta:
        linhas = sorted(linhas, key=lambda l: ((json.loads(l["editorial"]) if l["editorial"] else {}).get("tema", ""), l["id"]))
    colunas = COLUNAS_COMPACTAS if compacta else COLUNAS
    with caminho.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore")
        w.writeheader()
        for l in linhas:
            ed = json.loads(l["editorial"]) if l["editorial"] else {}
            w.writerow({
                "id": l["id"], "tema": ed.get("tema", ""), "tipo": l["tipo"], "texto": l["texto"], "contexto": ed.get("contexto", ""),
                "mecanismo": l["mecanismo"] or "", "razoes": " | ".join(ed.get("razoes", [])), "muda_se": ed.get("muda_se", ""),
                "rotulos_propostos": ", ".join(json.loads(l["rotulos_propostos"])),
                "sugestao_ia": _nomes(json.loads(l["ia_rotulos"])), "decisao": "", "rotulos_finais": "", "nota": "",
            })
    return len(linhas)


def _ler_decisoes(caminho: Path) -> list[dict[str, str]]:
    with Path(caminho).open(encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in linha.items() if k} for linha in csv.DictReader(f)]


def validar(conn, decisoes: list[dict[str, str]], reabrir: bool = False) -> tuple[list[dict[str, Any]], list[str]]:
    """Retorna (decisões válidas normalizadas, erros). Não altera nada."""
    erros: list[str] = []
    validas: list[dict[str, Any]] = []
    vistos: set[str] = set()
    tax = registry.rotulos_taxonomia()
    for n, d in enumerate(decisoes, start=2):  # linha 1 é o cabeçalho
        acao = d.get("decisao", "").lower()
        if not acao:
            continue  # linha não decidida: fica Pendente
        iid = d.get("id", "")
        onde = f"linha {n} ({iid or 'sem id'})"
        linha = conn.execute("SELECT estado, origem, tipo FROM itens WHERE id = ?", (iid,)).fetchone()
        if acao not in DECISOES:
            erros.append(f"{onde}: decisão inválida '{acao}' (use aprovar, rejeitar, ambiguo ou corrigir)")
        elif linha is None:
            erros.append(f"{onde}: item inexistente")
        elif iid in vistos:
            erros.append(f"{onde}: item repetido na planilha")
        elif linha["estado"] != "Pendente" and not reabrir:
            erros.append(f"{onde}: já está {linha['estado']} (use --reabrir para decidir de novo)")
        elif linha["origem"] == store.ORIGEM_VISITANTE and acao != "rejeitar":
            erros.append(f"{onde}: frase de visitante precisa de 'revisao anonimizar' antes de qualquer decisão além de rejeitar")
        elif acao != "aprovar" and not d.get("nota"):
            erros.append(f"{onde}: '{acao}' exige justificativa na coluna nota")
        else:
            rotulos = [r.strip() for r in d.get("rotulos_finais", "").replace(";", ",").split(",") if r.strip()]
            sem_disc = acao == "corrigir" and SEM_DISCRIMINACAO in rotulos
            if sem_disc:  # a leitura final é "sem discriminação": nenhum rótulo de discriminação
                if rotulos != [SEM_DISCRIMINACAO]:
                    erros.append(f"{onde}: '{SEM_DISCRIMINACAO}' não pode vir junto de outros rótulos")
                    vistos.add(iid)
                    continue
                rotulos = []
            invalidos = [r for r in rotulos if r not in tax]
            if acao == "corrigir" and not rotulos and not sem_disc:
                erros.append(f"{onde}: 'corrigir' exige rotulos_finais")
            elif invalidos:
                erros.append(f"{onde}: rótulos fora da taxonomia {invalidos}")
            else:
                tipo = None
                if sem_disc:
                    tipo = "nao_discriminatoria"
                elif acao == "corrigir" and linha["tipo"] == "ambigua" and any(tax[r]["tipo"] != "salvaguarda" for r in rotulos):
                    tipo = "exclusao"  # a pessoa fixou um rótulo de discriminação: a leitura deixa de ser ambígua
                validas.append({"id": iid, "decisao": acao, "rotulos": rotulos, "nota": d.get("nota") or None, "tipo": tipo})
        vistos.add(iid)
    return validas, erros


def aplicar_folha(conn, caminho: Path, revisor: str, simular: bool = False, reabrir: bool = False,
                  aprovar_restantes: bool = False) -> dict[str, Any]:
    """Aplica a folha. Com `aprovar_restantes`, as linhas SEM decisão que ainda estão Pendentes (e não vieram de visitante)
    são aprovadas em nome do revisor, com uma nota que registra que foi aprovação em lote. É uma decisão humana e
    explícita: sem a flag, linha vazia continua Pendente. Frases de visitante nunca entram nisso."""
    if not (revisor or "").strip():
        raise store.RevisaoInvalida("informe o revisor: decisões anônimas não são aceitas")
    linhas = _ler_decisoes(caminho)
    validas, erros = validar(conn, linhas, reabrir)
    if erros:
        return {"aplicadas": 0, "erros": erros, "simulado": simular}
    ja = {d["id"] for d in validas}
    restantes: list[str] = []
    if aprovar_restantes:
        for l in linhas:
            iid = l.get("id", "")
            if not iid or l.get("decisao") or iid in ja:
                continue
            linha = conn.execute("SELECT estado, origem FROM itens WHERE id = ?", (iid,)).fetchone()
            if linha and linha["estado"] == "Pendente" and linha["origem"] != store.ORIGEM_VISITANTE:
                restantes.append(iid)
    if not simular:
        for d in validas:
            if d["decisao"] == "corrigir":
                store.corrigir(conn, d["id"], revisor, d["rotulos"], d["nota"], d.get("tipo"))
            else:
                DECISOES[d["decisao"]](conn, d["id"], revisor, d["nota"])
        for iid in restantes:
            store.aprovar(conn, iid, revisor, NOTA_APROVACAO_EM_LOTE)
    resumo: dict[str, int] = {}
    for d in validas:
        resumo[d["decisao"]] = resumo.get(d["decisao"], 0) + 1
    if restantes:
        resumo["aprovar"] = resumo.get("aprovar", 0) + len(restantes)
    return {"aplicadas": 0 if simular else len(validas) + len(restantes), "previstas": resumo, "erros": [], "simulado": simular,
            "aprovadas_em_lote": len(restantes)}


def interativa(conn, revisor: str, entrada: Callable[[str], str] = input, saida: Callable[[str], None] = print) -> dict[str, int]:
    """Percorre os itens Pendente. a=aprovar r=rejeitar m=ambíguo c=corrigir p=pular s=sair."""
    if not (revisor or "").strip():
        raise store.RevisaoInvalida("informe o revisor: decisões anônimas não são aceitas")
    pendentes = [l for l in store.listar(conn, "Pendente") if l["origem"] != store.ORIGEM_VISITANTE]
    feitos = {"aprovar": 0, "rejeitar": 0, "ambiguo": 0, "corrigir": 0, "pular": 0}
    for i, l in enumerate(pendentes, start=1):
        ed = json.loads(l["editorial"]) if l["editorial"] else {}
        saida(f"\n[{i}/{len(pendentes)}] {l['id']} · tipo={l['tipo']} · tema={ed.get('tema', '-')}\n  “{l['texto']}”")
        for rot, chave in (("Contexto", "contexto"), ("Mecanismo", None), ("Muda se", "muda_se")):
            valor = l["mecanismo"] if chave is None else ed.get(chave)
            if valor:
                saida(f"  {rot}: {valor}")
        if ed.get("razoes"):
            saida("  Razões: " + " | ".join(ed["razoes"]))
        saida(f"  Rótulos propostos: {_nomes(json.loads(l['rotulos_propostos'])) or '-'}")
        while True:
            r = entrada("  [a]provar [r]ejeitar a[m]bíguo [c]orrigir [p]ular [s]air > ").strip().lower()[:1]
            if r == "s":
                return feitos
            if r in ("p", ""):
                feitos["pular"] += 1
                break
            if r not in ("a", "r", "m", "c"):
                continue
            nota = entrada("  justificativa" + (" (opcional)" if r == "a" else " (obrigatória)") + " > ").strip() or None
            if r != "a" and not nota:
                saida("  justificativa obrigatória.")
                continue
            try:
                if r == "a":
                    store.aprovar(conn, l["id"], revisor, nota)
                    feitos["aprovar"] += 1
                elif r == "r":
                    store.rejeitar(conn, l["id"], revisor, nota)
                    feitos["rejeitar"] += 1
                elif r == "m":
                    store.marcar_ambiguo(conn, l["id"], revisor, nota)
                    feitos["ambiguo"] += 1
                else:
                    rotulos = [x.strip() for x in entrada("  rótulos finais (ids separados por vírgula) > ").split(",") if x.strip()]
                    store.corrigir(conn, l["id"], revisor, rotulos, nota)
                    feitos["corrigir"] += 1
            except store.RevisaoInvalida as e:
                saida(f"  erro: {e}")
                continue
            break
    return feitos
