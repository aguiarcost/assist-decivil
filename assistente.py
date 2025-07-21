import openai
import os
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Carregar a chave da API a partir do ambiente ou secrets
if "OPENAI_API_KEY" in os.environ:
    openai.api_key = os.environ["OPENAI_API_KEY"]

# Caminho para os embeddings e a base de conhecimento
CAMINHO_EMBEDDINGS = "base_embeddings.json"
CAMINHO_CONHECIMENTO = "base_conhecimento.json"

# Carregar embeddings e base de conhecimento
def carregar_dados():
    with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
        conhecimento = json.load(f)
    with open(CAMINHO_EMBEDDINGS, "r", encoding="utf-8") as f:
        dados_emb = json.load(f)
    embeddings = np.array([item["embedding"] for item in dados_emb])
    perguntas = [item["pergunta"] for item in dados_emb]
    return conhecimento, perguntas, embeddings

conhecimento, perguntas_emb, embeddings = carregar_dados()

# Função principal para gerar resposta
def gerar_resposta(pergunta_utilizador):
    try:
        # Gerar embedding da pergunta com nova API
        resposta = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=pergunta_utilizador
        )
        embedding_utilizador = np.array(resposta.data[0].embedding).reshape(1, -1)
        sims = cosine_similarity(embedding_utilizador, embeddings)[0]
        idx_mais_proxima = int(np.argmax(sims))
        pergunta_correspondente = perguntas_emb[idx_mais_proxima]

        # Procurar a resposta correspondente
        for item in conhecimento:
            if item["pergunta"] == pergunta_correspondente:
                resposta = item["resposta"]
                modelo = item.get("modelo", "")
                if modelo:
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
                return resposta
        return "❓ Não foi possível encontrar uma resposta adequada."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {str(e)}"
