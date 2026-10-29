"""Gera `casos/catalogo_anterior_nx001_247.jsonl`: PROPOSTA de metadados para os exemplos NX-001..NX-247.

Esses 247 exemplos vieram só no CSV consolidado (id, leitura, tema, texto), sem subtema, justificativa, origem nem
estado. Este script não altera `id`, `leitura`, `tema` nem `texto`: lê o CSV e ACRESCENTA metadados por faixas de ID.
Tudo é proposta editorial, tudo entra Pendente e `pode_publicar=false`. Quem decide é a pessoa revisora.

Uso: ./.venv/bin/python tools/gerar_metadados_catalogo_anterior.py CAMINHO/catalogo_completo_atualizado.csv
(o JSONL gerado é versionado; o script existe para que a regra seja revisável e a geração, reproduzível.)
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "casos" / "catalogo_anterior_nx001_247.jsonl"
COLECAO = "catalogo_anterior_nx001_247"
ORIGEM = "catalogo_consolidado_sem_metadados_documentados"
PROPOSTA = "Metadados (subtema, mecanismo, grupo, gravidade, justificativa) propostos em 2026-10 por quem integrou o catálogo; pendentes de revisão humana."

R, I = "raca_e_povos_indigenas", "pessoas_com_deficiencia"
LGB, TR, M, N = "pessoas_lgbt", "pessoas_trans", "mulheres", "relacoes_nao_monogamicas"


def faixa(a: int, b: int | None = None) -> list[int]:
    return list(range(a, (b or a) + 1))


# (ids, subtema, mecanismo, grupo, justificativa)
BLOCOS: list[tuple[list[int], str, str, str | None, str]] = [
    # --- racismo
    (faixa(1, 6), "pertencimento_negado", "negacao_de_pertencimento", R, "Presume, pela aparência, que pessoa negra não é brasileira ou não representa o país."),
    (faixa(7, 14), "cabelo_e_aparencia", "desvalorizacao_de_aparencia", R, "Trata cabelo crespo, tranças ou penteados afro como inadequados, feios ou pouco profissionais."),
    (faixa(15, 19), "falso_elogio_racial", "falso_elogio", R, "Elogio que pressupõe que a característica elogiada seria improvável para pessoas negras."),
    (faixa(20), "nega_o_proprio_preconceito", "negacao_do_proprio_preconceito", R, "Usa “tenho amigos negros” para justificar uma rejeição."),
    (faixa(21, 25), "vigilancia_e_exclusao", "exclusao_de_espaco_ou_servico", R, "Atribui suspeita, “perfil” ou risco a pessoas negras e as exclui de emprego, compra, moradia ou atendimento."),
    (faixa(26), "denuncia_deslegitimada", "deslegitimacao_da_denuncia", R, "Descredita quem fala de racismo, sugerindo que busca vantagem."),
    (faixa(27, 30), "autenticidade_indigena_negada", "negacao_de_identidade", R, "Nega identidade, capacidade ou lugar de pessoas indígenas na sociedade atual."),
    # --- bifobia, homofobia e transfobia (tema lgbtfobia no catálogo)
    (faixa(31, 37) + faixa(44, 47), "bissexualidade_invalidada", "negacao_de_identidade", LGB, "Nega ou condiciona a identidade bissexual (fase, indecisão, parceria atual)."),
    (faixa(38, 43), "bifobia_estereotipo", "estereotipo_de_grupo", LGB, "Associa bissexualidade a infidelidade, promiscuidade ou desconfiança."),
    (faixa(48), "bifobia_exclusao", "exclusao_de_espaco_ou_servico", LGB, "Propõe silêncio sobre bissexualidade em espaço escolar."),
    (faixa(49, 53), "homofobia_cotidiana", "policiamento_de_expressao", LGB, "Aceita a pessoa LGBT só se discreta ou afastada de crianças, famílias e funções de referência."),
    (faixa(54, 58), "transfobia_cotidiana", "negacao_de_identidade", TR, "Nega nome social, atendimento, convívio ou respeito profissional a pessoas trans (o catálogo registrou o tema como lgbtfobia)."),
    # --- misoginia
    (faixa(59, 64), "merito_e_lideranca", "desqualificacao_de_merito", M, "Questiona a competência ou a posição de mulheres em liderança e negociação."),
    (faixa(65, 68), "lugar_da_mulher", "imposicao_de_papel", M, "Atribui à mulher um “lugar” (casa, silêncio, família) ou salário menor."),
    (faixa(69, 71), "emocao_e_ciclo", "patologizacao_emocional", M, "Explica opinião ou reação de mulher por ciclo menstrual ou emoção."),
    (faixa(72, 77), "assedio_culpabilizacao", "culpabilizacao_da_vitima", M, "Desloca a responsabilidade do assédio para roupa, simpatia, bebida ou suposta vingança."),
    (faixa(78, 82), "papeis_e_dupla_moral", "imposicao_de_papel", M, "Julga escolhas de mulheres (filhos, carreira, separação) com padrão diferente do aplicado a homens."),
    (faixa(83, 85), "area_e_espaco", "desqualificacao_de_merito", M, "Duvida do interesse ou do saber de mulheres em esporte, robótica ou mecânica."),
    # --- capacitismo
    (faixa(86, 91) + faixa(159, 163), "deficiencia_visual_invalidada", "invalidacao_de_deficiencia", I, "Duvida da deficiência visual (inclusive visão monocular) por “parecer normal” ou exige prova pública."),
    (faixa(92) + faixa(109) + faixa(118), "tutela_e_infantilizacao", "infantilizacao_e_tutela", I, "Fala ou decide no lugar da pessoa com deficiência."),
    (faixa(93, 98), "acessibilidade_negada", "exclusao_de_espaco_ou_servico", I, "Trata acessibilidade como despesa ou exagero e exclui pessoas com mobilidade reduzida."),
    (faixa(99, 103) + faixa(173, 175), "surdez_e_acessibilidade", "exclusao_de_espaco_ou_servico", I, "Nega intérprete, legenda ou transcrição a pessoas surdas ou com perda auditiva."),
    (faixa(104, 108) + faixa(170, 172) + faixa(185), "neurodivergencia_e_deficiencia_intelectual", "exclusao_de_espaco_ou_servico", I, "Exclui ou desconfia de pessoas autistas ou com deficiência intelectual em seleção, liderança ou decisões."),
    (faixa(110, 114) + faixa(164, 166), "deficiencia_nao_aparente_invalidada", "invalidacao_de_deficiencia", I, "Exige que a deficiência seja visível ou provada para valer direito ou adaptação."),
    (faixa(115, 117) + faixa(119), "voz_e_trabalho", "exclusao_de_espaco_ou_servico", I, "Retira voz, prioridade ou condições de trabalho de pessoas com deficiência."),
    (faixa(169, 169) + faixa(176, 180) + faixa(187, 188) + faixa(190, 192), "condicao_nao_visivel_invalidada", "invalidacao_de_deficiencia", I, "Trata dor crônica, cansaço, luz ou adaptação como desculpa, drama ou privilégio."),
    (faixa(181, 184) + faixa(186), "saude_mental_epilepsia_e_trabalho", "exclusao_de_espaco_ou_servico", I, "Presume incapacidade ou risco de pessoas com epilepsia ou em tratamento de saúde mental."),
    (faixa(189), "exigencia_de_diagnostico", "invasao_de_privacidade", I, "Exige que a pessoa exponha o diagnóstico para ter a adaptação reconhecida."),
    (faixa(193), "autonomia_e_acessibilidade", "invalidacao_de_deficiencia", I, "Usa a autonomia da pessoa para negar o direito à acessibilidade."),
    (faixa(167, 168), "cordao_de_girassol", "invalidacao_de_deficiencia", I, "Desconfia do símbolo de deficiência oculta ou exige seu uso constante."),
    # --- estigma contra relações não monogâmicas consensuais
    (faixa(206, 208) + faixa(217, 218) + faixa(231), "desqualificacao_moral", "desqualificacao_moral", N, "Atribui falta de caráter, honestidade ou princípios a quem vive relações não monogâmicas consensuais."),
    (faixa(209, 214) + faixa(223, 224) + faixa(227, 228) + faixa(232, 234), "vinculo_invalidado", "invalidacao_do_vinculo", N, "Nega ou reduz o afeto e o compromisso de relações não monogâmicas consensuais."),
    (faixa(215, 216) + faixa(225, 226), "sexualizacao_e_curiosidade", "invasao_de_privacidade", N, "Sexualiza a relação ou trata a pessoa como disponível."),
    (faixa(219, 222) + faixa(229, 230), "exclusao_social_e_trabalho", "exclusao_de_espaco_ou_servico", N, "Exclui de convívio, trabalho ou criação de filhos por causa do formato da relação."),
    # --- ambíguas (depende do contexto / ironia), controles
    (faixa(120, 122), "raca_ambiguidade", "depende_de_tom_e_uso", R, "Pergunta que pode ser curiosidade ou estranhamento; depende de quem pergunta, de como e de por quê."),
    (faixa(123, 125), "mulheres_ambiguidade", "depende_de_tom_e_uso", M, "Avaliação de perfil que pode ser critério neutro ou viés; depende do contexto e dos fatos."),
    (faixa(126, 127), "bissexualidade_ambiguidade", "depende_de_tom_e_uso", LGB, "Pergunta ou dúvida sobre bissexualidade; pode ser curiosidade respeitosa ou invalidação."),
    (faixa(128), "trans_ambiguidade", "depende_de_tom_e_uso", TR, "Pergunta sobre nome; pode ser respeito ou intrusão."),
    (faixa(129, 131) + faixa(194, 199), "deficiencia_ambiguidade", "depende_de_tom_e_uso", I, "Pergunta ou oferta de ajuda que pode ser cuidado ou presunção de incapacidade."),
    (faixa(132, 135), "ironia_ambiguidade", "depende_de_tom_e_uso", None, "Ironia: pode criticar um preconceito (quem ironiza o estereótipo) ou reproduzi-lo (quem o diz de verdade)."),
    (faixa(136, 137), "avaliacao_pessoal_ambigua", "depende_de_tom_e_uso", None, "Rejeição pessoal sem informar motivo; só o contexto diz se há preconceito."),
    (faixa(235, 240), "nao_monogamia_ambiguidade", "depende_de_tom_e_uso", N, "Pergunta ou preferência sobre relacionamentos; pode ser interesse legítimo ou julgamento."),
    (faixa(138, 144), "raca_controle", "sem_mecanismo_discriminatorio", R, "Afirma respeito, nomeia o racismo ou descreve medida antirracista."),
    (faixa(145, 146), "bissexualidade_controle", "sem_mecanismo_discriminatorio", LGB, "Reconhece a bissexualidade sem invalidá-la."),
    (faixa(147), "trans_controle", "sem_mecanismo_discriminatorio", TR, "Pergunta e respeita pronomes."),
    (faixa(148), "lgbt_controle", "sem_mecanismo_discriminatorio", LGB, "Discorda de política pública sem desrespeitar pessoas LGBTQIA+."),
    (faixa(149, 152), "mulheres_controle", "sem_mecanismo_discriminatorio", M, "Avalia com critérios iguais, apura denúncia ou respeita escolha."),
    (faixa(153, 158) + faixa(200, 205), "deficiencia_controle", "sem_mecanismo_discriminatorio", I, "Pergunta à pessoa, oferece adaptação ou reconhece que nem toda deficiência é visível."),
    (faixa(241, 247), "nao_monogamia_controle", "sem_mecanismo_discriminatorio", N, "Expressa preferência pessoal com respeito, ou pede informação, sem desqualificar."),
]

# Gravidade proposta (só discriminação). O que não estiver aqui é "estereotipo". Nenhum item é "incitacao_violencia".
OFENSA = {7, 8, 10, 13, 16, 54, 66, 81, 119, 207, 208, 225, 231}
EXCLUSAO_MATERIAL = (set(faixa(6)) | set(faixa(11)) | set(faixa(21, 23)) | {25, 28} | set(faixa(48, 53)) | set(faixa(55, 57))
                     | {61, 63, 65, 84} | {88, 89, 90, 92} | set(faixa(93, 109)) | {111, 112, 114} | set(faixa(115, 118))
                     | {163, 164, 165, 166, 168, 172, 173, 174, 179} | set(faixa(181, 186)) | {188, 189, 193}
                     | {219, 220, 221, 222, 229, 230, 233})
# Termos pejorativos explícitos (aviso de conteúdo; não é rótulo)
AVISO = {7, 8, 10, 13, 16, 207, 208}

TEMA_TIPO_OK = {"discriminação": {"racismo", "lgbtfobia", "misoginia", "capacitismo", "estigma_nao_monogamia"},
                "ambígua": {"depende_contexto", "ironia"}, "sem discriminação": {"sem_discriminacao"}}


def main(csv_path: Path) -> int:
    linhas = list(csv.DictReader(csv_path.open(encoding="utf-8-sig", newline="")))
    antigos = [r for r in linhas if r["id"].startswith("NX-") and int(r["id"][3:]) <= 247]
    por_id: dict[int, tuple] = {}
    for bloco in BLOCOS:
        for n in bloco[0]:
            if n in por_id:
                raise SystemExit(f"NX-{n:03d} aparece em mais de um bloco ({por_id[n][1]} e {bloco[1]})")
            por_id[n] = bloco
    faltam = {int(r["id"][3:]) for r in antigos} - set(por_id)
    if faltam:
        raise SystemExit(f"sem metadados: {sorted(faltam)}")
    saida = []
    for r in antigos:
        n = int(r["id"][3:])
        _, subtema, mecanismo, grupo, justificativa = por_id[n]
        if r["tema"] not in TEMA_TIPO_OK[r["leitura"]]:
            raise SystemExit(f"{r['id']}: tema {r['tema']} incompatível com leitura {r['leitura']}")
        discrimina = r["leitura"] == "discriminação"
        gravidade = ("exclusao_material" if n in EXCLUSAO_MATERIAL else "ofensa" if n in OFENSA else "estereotipo") if discrimina else "nao_se_aplica"
        saida.append({
            "id": r["id"], "leitura": r["leitura"], "tema": r["tema"], "texto": r["texto"], "subtema": subtema,
            "grupo": grupo, "mecanismo": mecanismo, "gravidade": gravidade, "justificativa_editorial": justificativa,
            "contexto": "Exemplo do catálogo anterior, sem origem documentada; tratar como ilustrativo até a revisão confirmar. Analisar contexto, alvo e possível citação.",
            "origem": ORIGEM, "estado_revisao": "Pendente", "pode_publicar": False, "colecao": COLECAO,
            "alerta_de_contexto": n in AVISO, "metadados_propostos": PROPOSTA,
        })
    SAIDA.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in saida), encoding="utf-8")
    print(f"{len(saida)} registros em {SAIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
