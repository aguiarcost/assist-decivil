import openai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Chave da API da OpenAI (via variável de ambiente)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Carregar a base de conhecimento do ficheiro
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Guardar a base de conhecimento atualizada no ficheiro
def guardar_base_conhecimento(base):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

# Gerar embedding a partir do texto
def get_embedding(text):
    try:
        response = openai.embeddings.create(model="text-embedding-3-small", input=text)
        return np.array(response.data[0].embedding).reshape(1, -1)
    except Exception as e:
        print(f"❌ Erro a gerar embedding para: {text}\n{e}")
        return None

# Gerar resposta a partir da pergunta do utilizador
def gerar_resposta(pergunta_utilizador, threshold=0.8):
    knowledge_base = carregar_base_conhecimento()

    for item in knowledge_base:
        if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
            resposta = item["resposta"]
            if item.get("email"):
                resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
            if item.get("modelo_email"):
                resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
            return resposta + "\n\n(Fonte: Base de conhecimento - correspondência exata)"

    # Se não encontrou exata, tenta por similaridade
    embeddings_existentes = []
    perguntas_existentes = []
    for item in knowledge_base:
        emb = get_embedding(item["pergunta"])
        if emb is not None:
            embeddings_existentes.append(emb)
            perguntas_existentes.append(item)

    if not embeddings_existentes:
        return "❓ A base de conhecimento não tem dados processáveis."

    user_embedding = get_embedding(pergunta_utilizador)
    if user_embedding is None:
        return "❌ Erro ao gerar embedding para a sua pergunta."

    matriz = np.vstack(embeddings_existentes)
    sims = cosine_similarity(user_embedding, matriz)[0]
    idx_mais_similar = int(np.argmax(sims))
    score = sims[idx_mais_similar]

    if score >= threshold:
        item = perguntas_existentes[idx_mais_similar]
        resposta = item["resposta"]
        if item.get("email"):
            resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
        if item.get("modelo_email"):
            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
        return resposta + f"\n\n(Fonte: Base de conhecimento - similaridade {score:.2f})"

    return "❓ Não foi possível encontrar uma resposta relevante na base de conhecimento."
