import openai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

openai.api_key = os.getenv("OPENAI_API_KEY")

def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def guardar_base_conhecimento(dados):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def carregar_knowledge_vector():
    if os.path.exists(CAMINHO_KNOWLEDGE_VECTOR):
        try:
            with open(CAMINHO_KNOWLEDGE_VECTOR, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except json.JSONDecodeError:
            pass
    return []

def guardar_knowledge_vector(dados):
    with open(CAMINHO_KNOWLEDGE_VECTOR, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def get_embedding(text):
    response = openai.embeddings.create(model="text-embedding-3-small", input=text)
    return np.array(response.data[0].embedding).reshape(1, -1)

def gerar_resposta(pergunta_utilizador, threshold=0.8):
    base = carregar_base_conhecimento()
    vectors = carregar_knowledge_vector()

    for item in base:
        if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
            resposta = item["resposta"]
            if item.get("email"):
                resposta += f"\n\n📫 <strong>Email de contacto:</strong> {item['email']}"
            if item.get("modelo_email"):
                modelo = item["modelo_email"]
                resposta += f"<br><br>📧 <strong>Modelo de email sugerido:</strong><br><pre>{modelo}</pre>"
            return resposta

    # Se não for correspondência exata, tenta similaridade
    if not vectors:
        return "ℹ️ A base de conhecimento está vazia ou sem embeddings."

    perguntas = [item["pergunta"] for item in vectors]
    embeddings = np.array([item["embedding"] for item in vectors])
    pergunta_vec = get_embedding(pergunta_utilizador)

    sims = cosine_similarity(pergunta_vec, embeddings)[0]
    max_sim = np.max(sims)
    if max_sim >= threshold:
        idx = int(np.argmax(sims))
        item = vectors[idx]
        resposta = item["resposta"]
        if item.get("email"):
            resposta += f"\n\n📫 <strong>Email de contacto:</strong> {item['email']}"
        if item.get("modelo_email"):
            modelo = item["modelo_email"]
            resposta += f"<br><br>📧 <strong>Modelo de email sugerido:</strong><br><pre>{modelo}</pre>"
        return resposta

    return "❓ Não foi possível encontrar uma resposta adequada na base de conhecimento."
