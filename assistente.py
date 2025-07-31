import openai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Chave da API OpenAI (ler do ambiente)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Carregar dados de conhecimento e embeddings
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

    # Embeddings (vetores da base de conhecimento)
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

# Carregar na inicialização
knowledge_base, knowledge_data, knowledge_embeddings = carregar_dados()

# Função para obter embedding de uma string (consulta à API OpenAI)
def get_embedding(texto):
    response = openai.embeddings.create(model="text-embedding-3-small", input=texto)
    return np.array(response.data[0].embedding).reshape(1, -1)

# Gerar resposta com base na base de conhecimento
def gerar_resposta(pergunta_utilizador, threshold=0.8):
    try:
        pergunta_clean = pergunta_utilizador.strip().lower()

        # 1. Procurar correspondência exata na base de conhecimento
        for item in knowledge_base:
            if item["pergunta"].strip().lower() == pergunta_clean:
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                modelo = item.get("modelo_email", "").strip()
                if modelo:
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
                return resposta + "\n\n(Fonte: Base de conhecimento, correspondência exata)"

        # 2. Procurar pergunta similar via embeddings (se disponíveis)
        if len(knowledge_embeddings) > 0:
            embedding_utilizador = get_embedding(pergunta_utilizador)
            sims = cosine_similarity(embedding_utilizador, knowledge_embeddings)[0]
            max_sim = float(np.max(sims))
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

        # 3. Caso não encontre resposta
        return "❓ Não foi possível encontrar uma resposta adequada na base de conhecimento."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {str(e)}"
