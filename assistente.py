
import json
import os
import openai
import numpy as np

# Caminhos
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_EMBEDDINGS = "base_vectorizada.json"

# Chave API
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Gerar embeddings com OpenAI
def gerar_embedding_openai(texto):
    try:
        resposta = openai.Embedding.create(
            input=texto,
            model="text-embedding-ada-002"
        )
        return resposta["data"][0]["embedding"]
    except Exception as e:
        return None

# Carregar base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Carregar embeddings gerados
def carregar_base_vectorizada():
    if os.path.exists(CAMINHO_EMBEDDINGS):
        with open(CAMINHO_EMBEDDINGS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Similaridade cosseno
def cosine_similarity(v1, v2):
    v1, v2 = np.array(v1), np.array(v2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# Gerar resposta
def gerar_resposta(pergunta):
    embedding_pergunta = gerar_embedding_openai(pergunta)
    if not embedding_pergunta:
        return "Erro ao gerar embedding da pergunta."

    base = carregar_base_vectorizada()
    if not base:
        return "Base de conhecimento com embeddings não encontrada."

    similaridades = []
    for item in base:
        sim = cosine_similarity(embedding_pergunta, item["embedding"])
        similaridades.append((sim, item))

    similaridades.sort(reverse=True, key=lambda x: x[0])
    melhor = similaridades[0][1] if similaridades else None

    if melhor:
        resposta = melhor.get("resposta", "")
        modelo = melhor.get("modelo", "")
        if modelo:
            return f"{resposta}

📧 Modelo de email sugerido:
```text
{modelo.strip()}
```"
        return resposta
    return "Não encontrei uma resposta adequada."
