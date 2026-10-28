"""Baseline C — transformer em português (BERTimbau), SOMENTE como plano e extração de
atributos congelados. Não há fine-tuning pesado neste projeto antes de o baseline B estar
consolidado e reproduzível.

STATUS: não executado. `torch`/`transformers` não fazem parte de requirements.txt.
Nenhum resultado deste baseline é reportado.

Modelos candidatos (a avaliar em hardware adequado):
- neuralmind/bert-base-portuguese-cased (BERTimbau base)
- neuralmind/bert-large-portuguese-cased (BERTimbau large)
Protocolo proposto: embeddings congelados (média dos tokens) + regressão logística, nos
MESMOS splits e métricas do baseline B; só depois, se houver ganho claro e a licença/uso
dos corpora permitir, fine-tuning leve com semente fixa.
"""

from __future__ import annotations

from typing import Any, Sequence

CANDIDATOS = ("neuralmind/bert-base-portuguese-cased", "neuralmind/bert-large-portuguese-cased")


class DependenciaAusente(RuntimeError):
    pass


def disponivel() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return True


def plano() -> dict[str, Any]:
    return {
        "executado": False,
        "motivo": "torch/transformers ausentes do ambiente reprodutível; baseline B primeiro",
        "dependencias_disponiveis": disponivel(),
        "modelos_candidatos": list(CANDIDATOS),
        "protocolo": "embeddings congelados + regressão logística nos mesmos splits do baseline B",
        "fine_tuning": "adiado até consolidar baselines A e B",
    }


class EmbeddingsCongelados:
    """Extrator de embeddings (média) com BERTimbau. Requer torch e transformers."""

    def __init__(self, modelo: str = CANDIDATOS[0], lote: int = 32, max_tokens: int = 128) -> None:
        if not disponivel():
            raise DependenciaAusente("instale torch e transformers para usar o baseline C (não incluídos por padrão)")
        self.modelo, self.lote, self.max_tokens = modelo, lote, max_tokens

    def extrair(self, textos: Sequence[str]):  # pragma: no cover - requer dependências pesadas
        import torch
        from transformers import AutoModel, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(self.modelo)
        mod = AutoModel.from_pretrained(self.modelo).eval()
        saida = []
        with torch.no_grad():
            for i in range(0, len(textos), self.lote):
                enc = tok(list(textos[i:i + self.lote]), padding=True, truncation=True, max_length=self.max_tokens, return_tensors="pt")
                h = mod(**enc).last_hidden_state
                m = enc["attention_mask"].unsqueeze(-1)
                saida.append(((h * m).sum(1) / m.sum(1)).numpy())
        import numpy as np
        return np.vstack(saida)
