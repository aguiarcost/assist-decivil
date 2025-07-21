
import json
import os
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Caminho para a base de conhecimento e embeddings
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_EMBEDDINGS = "perguntas_embeddings.json"

# Configurar a API key da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Carregar a base de conhecimento
def carregar_base_conhecimento():
    with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
        return json.load(f)

# Carregar embeddings
def carregar_embeddings():
    with open(CAMINHO_EMBEDDINGS, "r", encoding="utf-8") as f:
        return json.load(f)

# Gerar embedding da pergunta do utilizador
def gerar_embedding_pergunta(pergunta):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=pergunta
    )
    return response.data[0].embedding

# Calcular similaridade e obter a melhor resposta
def gerar_resposta(pergunta_utilizador):
    try:
        conhecimento = carregar_base_conhecimento()
        embeddings = carregar_embeddings()
        embedding_utilizador = np.array(gerar_embedding_pergunta(pergunta_utilizador)).reshape(1, -1)

        perguntas_embeddings = np.array([p["embedding"] for p in embeddings])
        perguntas_texto = [p["pergunta"] for p in embeddings]

        similaridades = cosine_similarity(embedding_utilizador, perguntas_embeddings)[0]
        indice_mais_proximo = int(np.argmax(similaridades))
        pergunta_mais_proxima = perguntas_texto[indice_mais_proximo]

        for item in conhecimento:
            if item["pergunta"] == pergunta_mais_proxima:
                resposta_final = item.get("resposta", "")
                modelo_email = item.get("modelo", "")
                if modelo_email:
                    resposta_final += "\n\n📧 Modelo de email sugerido:\n" + modelo_email
                return resposta_final

        return "❌ Não encontrei uma resposta adequada. Por favor reformule a pergunta."

    except Exception as e:
        return f"Erro ao gerar resposta: {e}"
