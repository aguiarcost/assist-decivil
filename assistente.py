import openai
import os
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Carregar chave API
openai.api_key = os.getenv("OPENAI_API_KEY")

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

def carregar_dados():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            conhecimento = json.load(f)
    else:
        conhecimento = []

    if os.path.exists(CAMINHO_KNOWLEDGE_VECTOR):
        with open(CAMINHO_KNOWLEDGE_VECTOR, "r", encoding="utf-8") as f:
            knowledge_data = json.load(f)
    else:
        knowledge_data = []

    knowledge_embeddings = np.array([item["embedding"] for item in knowledge_data]) if knowledge_data else np.array([])
    return conhecimento, knowledge_data, knowledge_embeddings

conhecimento, knowledge_data, knowledge_embeddings = carregar_dados()

def get_embedding(text):
    response = openai.embeddings.create(model="text-embedding-3-small", input=text)
    return np.array(response.data[0].embedding).reshape(1, -1)

def gerar_resposta(pergunta, threshold=0.8):
    try:
        for item in conhecimento:
            if item["pergunta"].strip().lower() == pergunta.strip().lower():
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                if item.get("modelo_email"):
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
                return resposta

        pergunta_emb = get_embedding(pergunta)

        if len(knowledge_embeddings) > 0:
            sims = cosine_similarity(pergunta_emb, knowledge_embeddings)[0]
            idx = int(np.argmax(sims))
            if sims[idx] >= threshold:
                item = knowledge_data[idx]
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                if item.get("modelo_email"):
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
                return resposta + f"\n\n(Similaridade: {sims[idx]:.2f})"

        return "❓ Não foi possível encontrar uma resposta adequada."
    except Exception as e:
        return f"❌ Erro: {str(e)}"
