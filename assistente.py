import json
import os

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

def gerar_resposta(pergunta):
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            base = json.load(f)
            for item in base:
                if item["pergunta"].strip().lower() == pergunta.strip().lower():
                    return item["resposta"]
    return "❓ Não foi possível encontrar uma resposta para a pergunta selecionada."

def guardar_nova_pergunta(pergunta, resposta):
    base = []
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            try:
                base = json.load(f)
            except json.JSONDecodeError:
                base = []
    base.append({
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip()
    })
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)
