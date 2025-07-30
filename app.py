import openai
import os
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Carregar chave API
openai.api_key = os.getenv("OPENAI_API_KEY")

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Carregar dados
def carregar_dados():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                knowledge_base = json.loads(content) if content else []
        except json.JSONDecodeError:
            knowledge_base = []
    else:
        knowledge_base = []

    if os.path.exists(CAMINHO_KNOWLEDGE_VECTOR):
        try:
            with open(CAMINHO_KNOWLEDGE_VECTOR, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                knowledge_data = json.loads(content) if content else []
        except json.JSONDecodeError:
            knowledge_data = []
    else:
        knowledge_data = []

    knowledge_embeddings = np.array([item["embedding"] for item in knowledge_data]) if knowledge_data else np.array([])
    knowledge_perguntas = [item["pergunta"] for item in knowledge_data]

    return knowledge_base, knowledge_data, knowledge_perguntas, knowledge_embeddings

knowledge_base, knowledge_data, knowledge_perguntas, knowledge_embeddings = carregar_dados()

def get_embedding(text):
    response = openai.embeddings.create(model="text-embedding-3-small", input=text)
    return np.array(response.data[0].embedding).reshape(1, -1)

def gerar_resposta(pergunta_utilizador, threshold=0.8):
    try:
        for item in knowledge_base:
            if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                modelo = item.get("modelo_email", "")
                if modelo and modelo.strip():
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo.strip()}\n```"
                return resposta + "\n\n(Fonte: Base de conhecimento, correspondência exata)"

        embedding_utilizador = get_embedding(pergunta_utilizador)

        if len(knowledge_embeddings) > 0:
            sims = cosine_similarity(embedding_utilizador, knowledge_embeddings)[0]
            max_sim = np.max(sims)
            if max_sim >= threshold:
                idx = int(np.argmax(sims))
                item = knowledge_data[idx]
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                modelo = item.get("modelo_email", "")
                if modelo and modelo.strip():
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo.strip()}\n```"
                return resposta + f"\n\n(Fonte: Base de conhecimento, similaridade: {max_sim:.2f})"

        return "❓ Não foi possível encontrar uma resposta adequada na base de conhecimento."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {str(e)}"
