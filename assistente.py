import os
import json
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Caminho da base de conhecimento
CAMINHO_CONHECIMENTO = "base_conhecimento.json"

# API Key via variável de ambiente
openai.api_key = os.getenv("OPENAI_API_KEY")

# ----- Funções utilitárias -----

def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def guardar_base_conhecimento(base):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

def get_embedding(texto):
    try:
        response = openai.embeddings.create(
            input=texto,
            model="text-embedding-3-small"
        )
        return np.array(response.data[0].embedding).reshape(1, -1)
    except Exception as e:
        print(f"Erro ao gerar embedding para: {texto}")
        print(str(e))
        return None

# ----- Função principal de resposta -----

def gerar_resposta(pergunta_utilizador, threshold=0.8):
    knowledge_base = carregar_base_conhecimento()

    for item in knowledge_base:
        if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
            resposta = item["resposta"]
            if item.get("email"):
                resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
            if item.get("modelo_email"):
                resposta += f"\n\n📧 <strong>Modelo de email sugerido:</strong><br><pre>{modelo}</pre>"
            return resposta

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
        return resposta

    return "❓ Não foi possível encontrar uma resposta relevante na base de conhecimento."

# ----- Edição e remoção -----

def editar_pergunta(pergunta_antiga, nova_pergunta, nova_resposta, novo_email=None, novo_modelo=None):
    base = carregar_base_conhecimento()
    nova_base = []
    for item in base:
        if item["pergunta"] == pergunta_antiga:
            nova_base.append({
                "pergunta": nova_pergunta,
                "resposta": nova_resposta,
                "email": novo_email,
                "modelo_email": novo_modelo
            })
        else:
            nova_base.append(item)
    guardar_base_conhecimento(nova_base)

def apagar_pergunta(pergunta_a_apagar):
    base = carregar_base_conhecimento()
    nova_base = [item for item in base if item["pergunta"] != pergunta_a_apagar]
    guardar_base_conhecimento(nova_base)
