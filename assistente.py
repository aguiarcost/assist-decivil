import openai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Carregar chave API
openai.api_key = os.getenv("OPENAI_API_KEY")

def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def guardar_base_conhecimento(base):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

def carregar_embeddings():
    if os.path.exists(CAMINHO_KNOWLEDGE_VECTOR):
        try:
            with open(CAMINHO_KNOWLEDGE_VECTOR, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = []
    else:
        data = []
    perguntas = [item["pergunta"] for item in data]
    embeddings = np.array([item["embedding"] for item in data]) if data else np.array([])
    return data, perguntas, embeddings

def gerar_embedding(texto):
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Erro a gerar embedding para: {texto}\n{e}")
        return None

def gerar_resposta(pergunta_utilizador, threshold=0.8):
    base = carregar_base_conhecimento()
    data, perguntas, embeddings = carregar_embeddings()

    # Correspondência exata
    for item in base:
        if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
            resposta = item["resposta"]
            if item.get("email"):
                resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
            if item.get("modelo_email"):
                resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
            return resposta

    # Similaridade
    emb = gerar_embedding(pergunta_utilizador)
    if emb is None or len(embeddings) == 0:
        return "❓ Não foi possível gerar uma resposta adequada."

    sims = cosine_similarity([emb], embeddings)[0]
    idx = int(np.argmax(sims))
    if sims[idx] >= threshold:
        item = data[idx]
        resposta = item["resposta"]
        if item.get("email"):
            resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
        if item.get("modelo_email"):
            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
        return resposta

    return "❓ Não foi possível encontrar uma resposta relevante na base de conhecimento."
