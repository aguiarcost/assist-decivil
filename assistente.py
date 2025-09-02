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

# ---------- API pública ----------
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

def adicionar_pergunta(pergunta, resposta, email="", modelo=""):
    base = carregar_base()
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
    if (nova_pergunta.strip().lower() != pergunta_original.strip().lower() and
        any(it["pergunta"].strip().lower() == nova_pergunta.strip().lower() for it in base)):
        return False, "Já existe outra pergunta com esse texto."

    for it in base:
        if it["pergunta"].strip().lower() == pergunta_original.strip().lower():
            it["pergunta"] = nova_pergunta.strip()
            it["resposta"] = (nova_resposta or "").strip()
            it["email"] = (novo_email or "").strip()
            it["modelo"] = (novo_modelo or "").strip()
            guardar_base(base)
            return True, "Alterações guardadas."
    return False, "Não encontrei a pergunta a editar."

def apagar_pergunta(pergunta):
    base = carregar_base()
    nova = [it for it in base if it["pergunta"].strip().lower() != pergunta.strip().lower()]
    if len(nova) == len(base):
        return False, "Não encontrei a pergunta para apagar."
    guardar_base(nova)
    return True, "Pergunta apagada."

# ---------- Import/Export ----------
def exportar_base_bytes():
    base = carregar_base()
    return json.dumps(base, ensure_ascii=False, indent=2).encode("utf-8")

def importar_base_de_bytes(file_bytes):
    try:
        data = json.loads(file_bytes.decode("utf-8"))
        if not isinstance(data, list):
            return False, "O JSON deve ser uma lista de objetos."
        nova = _deduplicar(data)
        if not nova:
            return False, "O ficheiro não contém entradas válidas."
        guardar_base(nova)
        return True, "Base importada e guardada com sucesso."
    except Exception as e:
        return False, f"Erro a ler JSON: {e}"
