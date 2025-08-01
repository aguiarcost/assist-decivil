import json
import os

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def guardar_base_conhecimento(lista_perguntas):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(lista_perguntas, f, ensure_ascii=False, indent=2)

def gerar_resposta(pergunta):
    base = carregar_base_conhecimento()
    for item in base:
        if item["pergunta"].strip().lower() == pergunta.strip().lower():
            resposta = item.get("resposta", "")
            if item.get("email"):
                resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
            if item.get("modelo_email"):
                resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
            return resposta + "\n\n(Fonte: Base de conhecimento)"
    return "❓ Não foi possível encontrar uma resposta correspondente."
