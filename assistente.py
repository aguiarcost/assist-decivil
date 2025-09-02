import json
import os

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

# ---------- Helpers JSON ----------
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

# ---------- API pública do módulo ----------
def carregar_base():
    base = _ler_json(CAMINHO_CONHECIMENTO, [])
    # normalizar estrutura
    normalizada = []
    for it in base:
        if isinstance(it, dict) and it.get("pergunta"):
            normalizada.append({
                "pergunta": it.get("pergunta", "").strip(),
                "resposta": (it.get("resposta") or "").strip(),
                "email": (it.get("email") or "").strip(),
                "modelo": (it.get("modelo") or it.get("modelo_email") or "").strip(),
            })
    return normalizada

def guardar_base(nova_lista):
    # deduplicar por pergunta (case-insensitive)
    by_q = {}
    for it in nova_lista:
        q = (it.get("pergunta") or "").strip()
        if not q:
            continue
        chave = q.lower()
        by_q[chave] = {
            "pergunta": q,
            "resposta": (it.get("resposta") or "").strip(),
            "email": (it.get("email") or "").strip(),
            "modelo": (it.get("modelo") or "").strip(),
        }
    _escrever_json(CAMINHO_CONHECIMENTO, list(by_q.values()))

def carregar_perguntas_frequentes():
    base = carregar_base()
    # ordenar alfabeticamente (podes trocar por outra ordem se quiseres)
    perguntas = sorted({it["pergunta"] for it in base if it["pergunta"]})
    return perguntas

def gerar_resposta(pergunta):
    """Devolve markdown pronto a mostrar, com resposta + email + modelo (se existirem)."""
    base = carregar_base()
    alvo = pergunta.strip().lower()
    for it in base:
        if it["pergunta"].strip().lower() == alvo:
            partes = []
            if it["resposta"]:
                partes.append(it["resposta"])
            if it["email"]:
                partes.append(f"**📧 Contacto:** [{it['email']}](mailto:{it['email']})")
            if it["modelo"]:
                partes.append("**📨 Modelo de email sugerido:**\n```\n" + it["modelo"] + "\n```")
            return "\n\n".join(partes) if partes else "Não há conteúdo definido para esta pergunta."
    return "Não encontrei resposta para essa pergunta."

def adicionar_pergunta(pergunta, resposta, email="", modelo=""):
    base = carregar_base()
    # bloquear duplicados (case-insensitive)
    if any(it["pergunta"].strip().lower() == pergunta.strip().lower() for it in base):
        return False, "Já existe uma pergunta com o mesmo texto."
    base.append({
        "pergunta": pergunta.strip(),
        "resposta": (resposta or "").strip(),
        "email": (email or "").strip(),
        "modelo": (modelo or "").strip(),
    })
    guardar_base(base)
    return True, "Pergunta adicionada com sucesso."

def editar_pergunta(pergunta_original, nova_pergunta, nova_resposta, novo_email="", novo_modelo=""):
    base = carregar_base()
    # se mudar o texto da pergunta, garantir que não duplica outra
    if (nova_pergunta.strip().lower() != pergunta_original.strip().lower() and
        any(it["pergunta"].strip().lower() == nova_pergunta.strip().lower() for it in base)):
        return False, "Já existe outra pergunta com esse texto."

    alterada = False
    for it in base:
        if it["pergunta"].strip().lower() == pergunta_original.strip().lower():
            it["pergunta"] = nova_pergunta.strip()
            it["resposta"] = (nova_resposta or "").strip()
            it["email"] = (novo_email or "").strip()
            it["modelo"] = (novo_modelo or "").strip()
            alterada = True
            break
    if not alterada:
        return False, "Não encontrei a pergunta a editar."

    guardar_base(base)
    return True, "Alterações guardadas."

def apagar_pergunta(pergunta):
    base = carregar_base()
    nova = [it for it in base if it["pergunta"].strip().lower() != pergunta.strip().lower()]
    if len(nova) == len(base):
        return False, "Não encontrei a pergunta para apagar."
    guardar_base(nova)
    return True, "Pergunta apagada."
