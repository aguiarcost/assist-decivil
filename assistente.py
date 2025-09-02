import json
import os

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

def _ler_json(caminho, default):
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def _escrever_json(caminho, conteudo):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)

def _normalizar_item(it):
    if not isinstance(it, dict):
        return None
    q = (it.get("pergunta") or "").strip()
    if not q:
        return None
    return {
        "pergunta": q,
        "resposta": (it.get("resposta") or "").strip(),
        "email": (it.get("email") or "").strip(),
        "modelo": (it.get("modelo") or it.get("modelo_email") or "").strip(),
    }

def _deduplicar(lista):
    by_q = {}
    for it in lista:
        norm = _normalizar_item(it)
        if not norm:
            continue
        by_q[norm["pergunta"].lower()] = norm
    return list(by_q.values())

def carregar_base():
    return _deduplicar(_ler_json(CAMINHO_CONHECIMENTO, []))

def guardar_base(nova_lista):
    _escrever_json(CAMINHO_CONHECIMENTO, _deduplicar(nova_lista))

def carregar_perguntas_frequentes():
    base = carregar_base()
    return sorted({it["pergunta"] for it in base if it["pergunta"]})

def gerar_resposta(pergunta):
    """Devolve (resposta, modelo_email)."""
    base = carregar_base()
    alvo = pergunta.strip().lower()
    for it in base:
        if it["pergunta"].strip().lower() == alvo:
            resposta = it.get("resposta", "")
            if it.get("email"):
                resposta += f"\n\n**📧 Contacto:** [{it['email']}](mailto:{it['email']})"
            modelo = it.get("modelo", "")
            return resposta, modelo
    return "Não encontrei resposta para essa pergunta.", ""
