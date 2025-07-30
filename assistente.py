import openai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Chave da API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Carregar dados
def carregar_dados():
    # Base de conhecimento
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                knowledge_base = json.loads(content) if content else []
        except json.JSONDecodeError:
            knowledge_base = []
    else:
        knowledge_base = []

    # Embeddings
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
    return knowledge_base, knowledge_data, knowledge_embeddings

knowledge_base, knowledge_data, knowledge_embeddings = carregar_dados()

# Gerar embedding
def get_embedding(texto):
    response = openai.embeddings.create(model="text-embedding-3-small", input=texto)
    return np.array(response.data[0].embedding).reshape(1, -1)

# Gerar resposta
def gerar_resposta(pergunta_utilizador, threshold=0.8, use_documents=False):  # use_documents mantido por compatibilidade
    try:
        pergunta_clean = pergunta_utilizador.strip().lower()

        # Correspondência exata
        for item in knowledge_base:
            if item["pergunta"].strip().lower() == pergunta_clean:
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                modelo = item.get("modelo_email", "").strip()
                if modelo:
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
                return resposta + "\n\n(Fonte: Base de conhecimento, correspondência exata)"

        # Similaridade com embeddings
        if len(knowledge_embeddings) > 0:
            embedding_utilizador = get_embedding(pergunta_utilizador)
            sims = cosine_similarity(embedding_utilizador, knowledge_embeddings)[0]
            max_sim = np.max(sims)
            if max_sim >= threshold:
                idx = int(np.argmax(sims))
                item = knowledge_data[idx]
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                modelo = item.get("modelo_email", "").strip()
                if modelo:
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
                return resposta + f"\n\n(Fonte: Base de conhecimento, similaridade: {max_sim:.2f})"

        return "❓ Não foi possível encontrar uma resposta adequada na base de conhecimento."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {str(e)}"
