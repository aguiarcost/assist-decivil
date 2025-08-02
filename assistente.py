import openai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Carregar chave da API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Carregar base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Guardar base de conhecimento
def guardar_base_conhecimento(base):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

# Gerar embedding via OpenAI
def get_embedding(texto):
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return np.array(response.data[0].embedding)
    except Exception as e:
        print(f"❌ Erro a gerar embedding para: {texto}")
        print(e)
        return None

# Recalcular embeddings e guardar
def gerar_embeddings():
    base = carregar_base_conhecimento()
    vetores = []
    for item in base:
        emb = get_embedding(item["pergunta"])
        if emb is not None:
            vetores.append({
                "pergunta": item["pergunta"],
                "embedding": emb.tolist()
            })
    with open(CAMINHO_KNOWLEDGE_VECTOR, "w", encoding="utf-8") as f:
        json.dump(vetores, f, ensure_ascii=False, indent=2)

# Gerar resposta
def gerar_resposta(pergunta_utilizador, threshold=0.8):
    base = carregar_base_conhecimento()

    if os.path.exists(CAMINHO_KNOWLEDGE_VECTOR):
        try:
            with open(CAMINHO_KNOWLEDGE_VECTOR, "r", encoding="utf-8") as f:
                embeddings = json.load(f)
        except json.JSONDecodeError:
            embeddings = []
    else:
        embeddings = []

    # Verificar correspondência exata
    for item in base:
        if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
            resposta = item["resposta"]
            if item.get("email"):
                resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
            if item.get("modelo_email"):
                resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
            return resposta

    # Se não houver correspondência exata, procurar por similaridade
    if embeddings:
        embedding_user = get_embedding(pergunta_utilizador)
        if embedding_user is not None:
            matriz = np.array([np.array(item["embedding"]) for item in embeddings])
            sims = cosine_similarity([embedding_user], matriz)[0]
            idx = int(np.argmax(sims))
            if sims[idx] >= threshold:
                pergunta_mais_proxima = embeddings[idx]["pergunta"]
                for item in base:
                    if item["pergunta"] == pergunta_mais_proxima:
                        resposta = item["resposta"]
                        if item.get("email"):
                            resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                        if item.get("modelo_email"):
                            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
                        return resposta

    return "❓ Não foi possível encontrar uma resposta na base de conhecimento."
