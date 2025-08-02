import openai
import os
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Função para obter todos os dados da base de conhecimento
def carregar_base_conhecimento():
    response = supabase_client.table("base_conhecimento").select("*").execute()
    if response.data:
        return response.data
    return []

# Função para guardar nova pergunta
def guardar_nova_pergunta(pergunta, resposta, email=None, modelo_email=None):
    supabase_client.table("base_conhecimento").insert({
        "pergunta": pergunta,
        "resposta": resposta,
        "email": email,
        "modelo_email": modelo_email
    }).execute()

# Função para editar pergunta existente
def atualizar_pergunta(id_pergunta, novos_dados):
    supabase_client.table("base_conhecimento").update(novos_dados).eq("id", id_pergunta).execute()

# Função para calcular a similaridade cosseno manualmente
def cosine_similarity_manual(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

# Gerar embedding com OpenAI
def gerar_embedding(texto):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return response.data[0].embedding

# Gerar resposta com base na base de conhecimento
def gerar_resposta(pergunta_utilizador, threshold=0.80):
    base = carregar_base_conhecimento()
    if not base:
        return "Base de conhecimento vazia."

    embedding_utilizador = gerar_embedding(pergunta_utilizador)

    melhor_match = None
    melhor_sim = 0.0

    for item in base:
        if item.get("embedding"):
            similaridade = cosine_similarity_manual(embedding_utilizador, item["embedding"])
            if similaridade > melhor_sim:
                melhor_sim = similaridade
                melhor_match = item

    if melhor_match and melhor_sim >= threshold:
        resposta = melhor_match["resposta"]
        email = melhor_match.get("email", "")
        modelo = melhor_match.get("modelo_email", "")

        if email:
            resposta += f"\n\n📫 **Email de contacto:** {email}"
        if modelo:
            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"

        return resposta
    else:
        return "❓ Não foi possível encontrar uma resposta adequada."
