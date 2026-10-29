"""Download reproduzível com cache local e validação de integridade.

Regras:
- `aberto`: baixa com urllib, confere sha256 do registry e só então move para o cache.
  Hash divergente => arquivo descartado (nunca entra no cache).
- `restrito_autorizacao`: só tenta com credencial fornecida pelo operador (variável HF_TOKEN
  ou parâmetro). Sem credencial, ou com 401/403, o dataset fica `pendente_autorizacao` e o
  pipeline segue com os demais. Nada é contornado.
- `pendente_fonte`: não existe fonte pública verificável; nada é baixado, procurado em espelhos nem inventado.
- Licença NÃO declarada (`condicoes_licenca.exige_reconhecimento_do_operador`): o download só acontece com
  reconhecimento explícito do operador (`aceito_licenca=True`, `--aceito-licenca` ou ESO_ACEITE_LICENCA=<ds_id>);
  o aceite fica registrado no manifest. As condições são lidas do registry ANTES de qualquer byte entrar no cache.
- Corpora ficam em `datasets/_local/` (ignorado pelo Git) ou em ESO_DATA_DIR.
"""

from __future__ import annotations

import hashlib
import json
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .. import paths, registry

USER_AGENT = "eh-so-opiniao/0.1 (pesquisa academica; contato do operador)"
Abridor = Callable[[urllib.request.Request], "object"]


@dataclass
class ResultadoArquivo:
    dataset_id: str
    arquivo: str
    status: str
    detalhe: str = ""
    sha256: str | None = None
    caminho: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _abridor_padrao() -> Abridor:
    """urlopen com verificação TLS ativa; usa certifi quando o Python não tem CAs do sistema."""
    contexto = ssl.create_default_context()
    try:
        import certifi

        contexto = ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover
        pass
    return lambda req: urllib.request.urlopen(req, timeout=120, context=contexto)  # noqa: S310


def pasta_dataset(ds_id: str) -> Path:
    return paths.cache_bruto() / ds_id


def _hashes(caminho: Path) -> tuple[str, str]:
    s, m = hashlib.sha256(), hashlib.md5()  # noqa: S324 - md5 só para conferir hashes publicados
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            s.update(bloco)
            m.update(bloco)
    return s.hexdigest(), m.hexdigest()


def _manifest(ds_id: str) -> dict:
    caminho = pasta_dataset(ds_id) / "manifest.json"
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {"arquivos": {}}


def _gravar_manifest(ds_id: str, manifest: dict) -> None:
    pasta = pasta_dataset(ds_id)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _confere(arq: dict, sha: str, md5: str) -> tuple[bool, str]:
    if arq.get("sha256"):
        return sha == arq["sha256"], "sha256"
    if arq.get("md5"):
        return md5 == arq["md5"], "md5"
    return True, "sem_hash_publicado"


def validar_integridade(ds_id: str, arq: dict) -> ResultadoArquivo:
    destino = pasta_dataset(ds_id) / arq["arquivo"]
    if not destino.exists():
        return ResultadoArquivo(ds_id, arq["arquivo"], "ausente")
    sha, md5 = _hashes(destino)
    ok, criterio = _confere(arq, sha, md5)
    if ok and criterio == "sem_hash_publicado":
        guardado = _manifest(ds_id)["arquivos"].get(arq["arquivo"], {}).get("sha256")
        ok = guardado is None or guardado == sha
        criterio = "manifest_local"
    return ResultadoArquivo(ds_id, arq["arquivo"], "integridade_ok" if ok else "falha_integridade",
                            criterio, sha, str(destino))


def licenca_reconhecida(ds_id: str, aceito: bool = False) -> bool:
    """O operador reconheceu as condições de licença (parâmetro ou variável ESO_ACEITE_LICENCA=ds1,ds2)."""
    if aceito:
        return True
    return ds_id in {x.strip() for x in os.environ.get("ESO_ACEITE_LICENCA", "").split(",") if x.strip()}


def resumo_condicoes(ds_id: str) -> str:
    return _resumo_condicoes(registry.dataset(ds_id))


def _resumo_condicoes(info: dict) -> str:
    c = info["condicoes_licenca"]
    return f"licença: {c['identificador']}; restrições: {'; '.join(c['restricoes'])}"


def baixar(ds_id: str, *, token: str | None = None, forcar: bool = False, abrir: Abridor | None = None,
           aceito_licenca: bool = False) -> list[ResultadoArquivo]:
    info = registry.dataset(ds_id)
    if info["integracao"] == "pendente_fonte":
        return [ResultadoArquivo(ds_id, "-", "pendente_fonte",
                                 "sem fonte pública verificável (ver registry.yaml: fontes_verificadas e pendencia); nada foi tentado")]
    abrir = abrir or _abridor_padrao()
    aceite = licenca_reconhecida(ds_id, aceito_licenca)
    resultados: list[ResultadoArquivo] = []
    for arq in info["url_arquivos"]:
        resultados.append(_baixar_arquivo(ds_id, info, arq, token, forcar, abrir, aceite))
    return resultados


def _baixar_arquivo(ds_id: str, info: dict, arq: dict, token: str | None, forcar: bool, abrir: Abridor,
                    aceite_licenca: bool = True) -> ResultadoArquivo:
    nome = arq["arquivo"]
    exige = registry.exige_reconhecimento_de_licenca(ds_id)
    credencial = None
    if info["acesso"] == "restrito_autorizacao":
        credencial = token or os.environ.get("HF_TOKEN")
        if not credencial:
            return ResultadoArquivo(ds_id, nome, "pendente_autorizacao",
                                    "dataset restrito: aceite os termos no site e informe HF_TOKEN; nada foi tentado")

    destino = pasta_dataset(ds_id) / nome
    if destino.exists() and not forcar:
        v = validar_integridade(ds_id, arq)
        if v.status == "integridade_ok":
            return ResultadoArquivo(ds_id, nome, "em_cache", v.detalhe, v.sha256, str(destino))
        destino.unlink()  # cache corrompido: baixa de novo

    if exige and not aceite_licenca:
        return ResultadoArquivo(ds_id, nome, "pendente_licenca",
                                "reconhecimento das condições de licença pendente (--aceito-licenca); nada foi tentado")

    req = urllib.request.Request(arq["url"], headers={"User-Agent": USER_AGENT})
    if credencial:
        req.add_header("Authorization", f"Bearer {credencial}")
    pasta_dataset(ds_id).mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + ".parte")
    try:
        with abrir(req) as resp, temporario.open("wb") as f:  # type: ignore[attr-defined]
            while bloco := resp.read(1 << 20):
                f.write(bloco)
    except urllib.error.HTTPError as erro:
        temporario.unlink(missing_ok=True)
        if erro.code in (401, 403):
            return ResultadoArquivo(ds_id, nome, "pendente_autorizacao", f"HTTP {erro.code}: acesso não autorizado")
        return ResultadoArquivo(ds_id, nome, "falha_rede", f"HTTP {erro.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        temporario.unlink(missing_ok=True)
        return ResultadoArquivo(ds_id, nome, "falha_rede", str(erro))

    sha, md5 = _hashes(temporario)
    ok, criterio = _confere(arq, sha, md5)
    if not ok:
        temporario.unlink(missing_ok=True)
        return ResultadoArquivo(ds_id, nome, "falha_integridade", f"{criterio} divergente do registry", sha)
    temporario.replace(destino)
    manifest = _manifest(ds_id)
    manifest["arquivos"][nome] = {
        "sha256": sha, "md5": md5, "bytes": destino.stat().st_size, "url": arq["url"],
        "baixado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "criterio": criterio if criterio != "sem_hash_publicado" else "primeiro_uso_registrado",
    }
    if exige:
        manifest["aceite_de_licenca"] = {
            "reconhecido_pelo_operador": True, "condicoes": info["condicoes_licenca"]["identificador"],
            "restricoes": info["condicoes_licenca"]["restricoes"],
            "em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    _gravar_manifest(ds_id, manifest)
    return ResultadoArquivo(ds_id, nome, "baixado", criterio, sha, str(destino))


def estado_geral() -> dict[str, dict]:
    """Estado de cada dataset no cache local, sem rede."""
    saida: dict[str, dict] = {}
    for ds_id in registry.listar_datasets():
        info = registry.dataset(ds_id)
        arquivos = [validar_integridade(ds_id, a) for a in info["url_arquivos"] if not a.get("uso", "").startswith("NÃO ingerido")]
        presentes = bool(arquivos) and all(r.status == "integridade_ok" for r in arquivos)
        saida[ds_id] = {
            "acesso": info["acesso"],
            "status_catalogo": info["status_acesso"],
            "no_cache": presentes,
            "arquivos": [r.to_dict() for r in arquivos],
        }
    return saida
