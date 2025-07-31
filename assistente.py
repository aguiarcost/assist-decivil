import json
import os

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

def gerar_resposta(pergunta):
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            base = json.load(f)
            for item in base:
                if item["pergunta"].strip().lower() == pergunta.strip().lower():
                    resposta = item["resposta"].strip()
                    detalhes = ""
                    if item.get("email"):
                        detalhes += f"\n\n📫 **Email de contacto:** {item['email'].strip()}"
                    if item.get("modelo_email"):
                        detalhes += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email'].strip()}\n```"
                    return resposta + detalhes
    return "❓ Não foi possível encontrar uma resposta para a pergunta selecionada."

def guardar_nova_pergunta(pergunta, resposta, email="", modelo_email=""):
    base = []
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            try:
                base = json.load(f)
            except json.JSONDecodeError:
                base = []

    base.append({
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip(),
        "email": email.strip(),
        "modelo_email": modelo_email.strip()
    })

    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)
