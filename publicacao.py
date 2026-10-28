"""Geração dos dados do site estático.

Só sai daqui: (1) frases com decisão humana (Aprovado/Corrigido/Ambíguo permitido) de origens
publicáveis; (2) taxonomia; (3) catálogo e referências (metadados, nunca texto de corpus);
(4) achados agregados dos experimentos (números, nunca exemplos).
A classificação por IA NÃO roda no site: o site só lê JSON já revisado.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import SCHEMA_VERSION, paths, registry
from .review import store
from .textnorm import hash_chave

AVISO = ("Conteúdo educativo e experimental. Uma classificação de IA é uma hipótese, não uma prova: "
         "não conclui crime, intenção nem identidade, e só é exibida depois de revisão humana.")


class VazamentoDetectado(RuntimeError):
    pass


def _nomes(rotulos: list[str]) -> list[dict[str, str]]:
    tax = registry.rotulos_taxonomia()
    return [{"id": r, "nome": tax[r]["nome"], "tipo": tax[r]["tipo"]} for r in rotulos if r in tax]


def exportar_frases(conn, incluir_rascunho: bool = False) -> dict[str, Any]:
    itens = []
    for linha in store.listar(conn):
        publicavel = store.publicavel(linha)
        rascunho_ok = incluir_rascunho and linha["origem"] in store.ORIGENS_PUBLICAVEIS and linha["estado"] != "Rejeitado"
        if not publicavel and not rascunho_ok:
            continue
        if linha["estado"] == "Ambíguo":
            finais = ["ambigua"]
        elif linha["rotulos_humanos"] is not None:
            finais = json.loads(linha["rotulos_humanos"])
        else:
            finais = json.loads(linha["rotulos_propostos"])
        ia = json.loads(linha["ia_rotulos"])
        itens.append({
            "id": linha["id"], "texto": linha["texto"], "tipo": linha["tipo"],
            "rotulos": _nomes(finais), "mecanismo": linha["mecanismo"], "par_espelho": linha["par_espelho"],
            "ia": {"sinalizou": _nomes(ia), "metodo": linha["ia_metodo"], "concorda_com_revisao": sorted(ia) == sorted(finais)},
            "revisao": {"estado": linha["estado"] if publicavel else "RASCUNHO", "por_humano": publicavel},
            "origem": linha["origem"],
        })
    return {"schema": f"eso-site-{SCHEMA_VERSION}", "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "taxonomia_versao": registry.versao_taxonomia(), "aviso": AVISO, "frases": itens}


def taxonomia_publica() -> dict[str, Any]:
    return {"versao": registry.versao_taxonomia(), "rotulos": [
        {"id": rid, "nome": r["nome"], "tipo": r["tipo"], "definicao": r["definicao"], "nao_e": r.get("nao_e", ""),
         "observacao": r.get("observacao", "")} for rid, r in registry.rotulos_taxonomia().items()]}


def catalogo_publico() -> list[dict[str, Any]]:
    saida = []
    for ds_id in registry.listar_datasets():
        i = registry.dataset(ds_id)
        saida.append({"id": ds_id, "nome": i["nome"], "licenca": i["licenca"] if len(i["licenca"]) < 40 else "não declarada",
                      "plataforma": i["plataforma"], "acesso": i["acesso"], "status": i["status_acesso"],
                      "registros": i["registros_confirmados"], "referencia": i["referencia"], "url": i["url_origem"],
                      "limitacoes": i["limitacoes_vieses"]})
    return saida


def _ler(nome: str, pasta: Path) -> dict[str, Any] | None:
    caminho = pasta / f"experimento_{nome}.json"
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else None


def achados_dos_relatorios(pasta: Path | None = None) -> list[dict[str, Any]]:
    """Achados agregados (números dos relatórios reais). Sem texto de corpora."""
    pasta = pasta or paths.RELATORIOS
    achados: list[dict[str, Any]] = []
    b, c, d, e, a = (_ler(x, pasta) for x in "bcdea")
    pct = lambda v: f"{round(v * 100)}%"  # noqa: E731
    if b:
        t = b["teste_hatebr"]
        lr, lex = t["B_lr_val_f1"], t["A_lexico"]
        achados.append({"id": "fp_fn", "titulo": "Mesmo o melhor modelo simples erra",
                        "texto": f"No teste do HateBR, o modelo TF-IDF acerta a maior parte, mas deixa passar cerca de {pct(1 - lr['recall']['media'])} dos comentários ofensivos "
                                 f"e marca como ofensivos cerca de {pct(1 - lr['precision']['media'])} dos que sinalizou sem serem. "
                                 f"Já a lista de palavras ofensivas quase não erra ao apontar (precisão {pct(lex['precision']['media'])}), mas só encontra {pct(lex['recall']['media'])} dos casos.",
                        "experimento": "B"})
        tr = b["transferencia_para_told"]
        achados.append({"id": "fora_do_dominio", "titulo": "Fora do domínio, o resultado muda",
                        "texto": f"Treinado em comentários sobre políticos (HateBR) e testado no ToLD-Br, o modelo obteve macro-F1 {tr['B_lr_val_f1']['macro_f1']['media']:.2f} "
                                 f"(média das duas classes), contra {tr['trivial']['macro_f1']['media']:.2f} de simplesmente marcar tudo como ofensivo e {tr['A_lexico']['macro_f1']['media']:.2f} da lista de palavras. "
                                 f"No ToLD-Br, {pct(tr['prevalencia_told'])} dos textos contam como ofensivos pelo critério de votos usado aqui, que é só aproximado ao do HateBR. "
                                 "Comparar com o chute e com outro domínio é essencial para não se enganar.",
                        "experimento": "B"})
    if a:
        raras = [k for k, v in a["por_classe"].items() if v["suporte_insuficiente_dominio"]]
        achados.append({"id": "classes_raras", "titulo": "Classes raras quase não têm exemplos",
                        "texto": "Para as classes " + ", ".join(registry.rotulos_taxonomia()[k]["nome"].lower() for k in raras) +
                                 " há poucos exemplos positivos no teste. As métricas dessas classes oscilam muito e não permitem concluir que o modelo funciona.",
                        "experimento": "A"})
    if c:
        piores = [g for g in c["efeito_de_combinar_em_dominio"] if g["delta"] < 0]
        if piores:
            achados.append({"id": "combinar_dados", "titulo": "Juntar bases diferentes nem sempre ajuda",
                            "texto": f"Em {len(piores)} de {len(c['efeito_de_combinar_em_dominio'])} comparações, treinar com mais de uma base (cujas definições de 'ofensivo' são só aproximadas) "
                                     "piorou o F1 no teste da própria base. Misturar rótulos parecidos não é o mesmo que ter o mesmo rótulo.",
                            "experimento": "C"})
    if d:
        cf = d["contrafactual"]["hatebr"]["ofensivos"]["esquerda_para_direita"]
        achados.append({"id": "neutralidade", "titulo": "O modelo pode tratar lados políticos de modo diferente",
                        "texto": f"Ao trocar apenas termos de um lado político pelo equivalente do outro nos mesmos textos ofensivos (n={cf['n']}), "
                                 f"a pontuação média mudou {cf['delta_medio_assinado']:+.2f} (IC95% {cf['ic95_bootstrap'][0]:+.2f} a {cf['ic95_bootstrap'][1]:+.2f}). "
                                 "O mesmo ato deveria receber o mesmo tratamento. Por isso o modelo não pode ser usado para priorizar casos sem revisão e controle de neutralidade.",
                        "experimento": "D"})
    if e:
        m, tudo = e["hatebr_teste"]["B_coeficientes_tfidf"], e["hatebr_teste"]["tudo"]
        achados.append({"id": "destaque_trechos", "titulo": "Destacar o trecho ofensivo é difícil",
                        "texto": f"Ao tentar marcar quais palavras tornam um texto ofensivo, o baseline teve F1 {m['f1']:.2f}, {'abaixo' if m['f1'] < tudo['f1'] else 'acima'} dos {tudo['f1']:.2f} de simplesmente marcar tudo (a maior parte das palavras desses comentários já está dentro do trecho ofensivo). "
                                 "O destaque ajuda a revisão humana, mas não é uma explicação confiável.",
                        "experimento": "E"})
    return achados


def varrer_vazamento(conteudo: Any, textos_corpora: list[str], minimo: int = 25) -> list[str]:
    """Retorna textos de corpora que aparecem no conteúdo publicado (deve ser vazio)."""
    bruto = json.dumps(conteudo, ensure_ascii=False)
    chaves_publicadas = {hash_chave(f["texto"]) for f in conteudo.get("frases", [])} if isinstance(conteudo, dict) else set()
    achados = [t for t in textos_corpora if len(t) >= minimo and t in bruto]
    achados += [t for t in textos_corpora if hash_chave(t) in chaves_publicadas]
    return achados


def _textos_dos_corpora_locais() -> list[str]:
    textos: list[str] = []
    pasta = paths.normalizados()
    if not pasta.exists():
        return textos
    for arq in pasta.glob("*.jsonl"):
        with arq.open(encoding="utf-8") as f:
            textos += [json.loads(l)["text"] for l in f if l.strip()]
    return textos


def construir_site(conn, destino: Path | None = None, incluir_rascunho: bool = False, verificar_corpora: bool = True) -> dict[str, Any]:
    destino = destino or paths.SITE / "data"
    frases = exportar_frases(conn, incluir_rascunho=False)
    if verificar_corpora:
        achados = varrer_vazamento(frases, _textos_dos_corpora_locais())
        if achados:
            raise VazamentoDetectado(f"{len(achados)} texto(s) de corpora científicos encontrados no conteúdo público")
    destino.mkdir(parents=True, exist_ok=True)
    arquivos = {
        "frases.json": frases, "taxonomia.json": taxonomia_publica(), "catalogo.json": catalogo_publico(),
        "achados.json": {"gerado_dos_relatorios": achados_dos_relatorios(), "aviso": AVISO},
    }
    for nome, conteudo in arquivos.items():
        (destino / nome).write_text(json.dumps(conteudo, indent=2, ensure_ascii=False), encoding="utf-8")
    rascunho = 0
    if incluir_rascunho:
        pasta = destino / "_rascunho"
        pasta.mkdir(exist_ok=True)
        r = exportar_frases(conn, incluir_rascunho=True)
        (pasta / "frases.json").write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
        rascunho = len(r["frases"])
    return {"frases_publicadas": len(frases["frases"]), "frases_rascunho_local": rascunho, "destino": str(destino)}
