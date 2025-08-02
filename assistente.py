import openai
import os
from supabase import create_client, Client
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Chave e URL Supabase a partir do ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Função auxiliar para obter embeddings
def get_embedding(texto):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return response.data[0].embedding

# Carregar todas as perguntas
def carregar_perguntas():
    resposta = supabase_client.table("perguntas").select("*").execute()
    return resposta.data if resposta.data else []

# Gerar resposta com base em correspondência exata ou similaridade
def gerar_resposta(pergunta_utilizador):
    data = carregar_perguntas()
    perguntas = [d["pergunta"] for d in data]
    respostas = {d["pergunta"]: d for d in data}

    # Correspondência exata
    if pergunta_utilizador in respostas:
        item = respostas[pergunta_utilizador]
        resposta = item["resposta"]
        email = item.get("email")
        modelo = item.get("modelo_email")

        if email:
            resposta += f"\n\n📫 **Email de contacto:** {email}"
        if modelo:
            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
        return resposta

    # Similaridade por embedding
    try:
        pergunta_embedding = np.array(get_embedding(pergunta_utilizador)).reshape(1, -1)
        base_embeddings = np.array([d["embedding"] for d in data])
        if base_embeddings.size == 0:
            return "❓ Sem dados suficientes para encontrar uma resposta."
        sims = cosine_similarity(pergunta_embedding, base_embeddings)[0]
        idx = np.argmax(sims)
        item = data[idx]
        resposta = item["resposta"]
        email = item.get("email")
        modelo = item.get("modelo_email")

        if email:
            resposta += f"\n\n📫 **Email de contacto:** {email}"
        if modelo:
            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
        return resposta
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {e}"

# Adicionar nova pergunta (se não existir)
def adicionar_pergunta(pergunta, resposta, email=None, modelo_email=None):
    existente = supabase_client.table("perguntas").select("id").eq("pergunta", pergunta).execute()
    if existente.data:
        return False

    embedding = get_embedding(pergunta)
    supabase_client.table("perguntas").insert([{
        "pergunta": pergunta,
        "resposta": resposta,
        "email": email,
        "modelo_email": modelo_email,
        "embedding": embedding
    }]).execute()
    return True

# Atualizar pergunta existente
def atualizar_pergunta(pergunta, nova_resposta, novo_email=None, novo_modelo_email=None):
    supabase_client.table("perguntas").update({
        "resposta": nova_resposta,
        "email": novo_email,
        "modelo_email": novo_modelo_email
    }).eq("pergunta", pergunta).execute()
    return True
