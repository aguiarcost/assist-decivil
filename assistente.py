import os
from supabase import create_client, Client
from openai import OpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Secretos
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PASSWORD_CORRETA = os.getenv("ADMIN_PASSWORD", "decivil2024")  # Fallback

# Supabase e OpenAI clients
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------
# Funções auxiliares
# ------------------------

def listar_perguntas():
    try:
        data = supabase_client.table("perguntas").select("pergunta").execute().data
        return sorted([item["pergunta"] for item in data])
    except Exception:
        return []

def obter_pergunta_por_texto(pergunta_texto):
    try:
        data = supabase_client.table("perguntas").select("*").eq("pergunta", pergunta_texto).execute().data
        return data[0] if data else {}
    except Exception:
        return {}

def get_embedding(texto):
    try:
        response = openai_client.embeddings.create(
            input=texto,
            model="text-embedding-3-small"
        )
        return np.array(response.data[0].embedding).tolist()
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return []

def gerar_resposta(pergunta_usuario):
    try:
        # Busca correspondência exata
        dados = obter_pergunta_por_texto(pergunta_usuario)
        if dados:
            resposta = dados["resposta"]
            if dados.get("email"):
                resposta += f"\n\n📫 **Email de contacto:** {dados['email']}"
            if dados.get("modelo_email"):
                resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{dados['modelo_email']}\n```"
            return resposta

        # Caso não encontre, busca por similaridade
        embedding_pergunta = np.array(get_embedding(pergunta_usuario)).reshape(1, -1)
        base = supabase_client.table("perguntas").select("*").execute().data

        if not base:
            return "❌ Não existem dados na base de conhecimento."

        embeddings_base = np.array([item["embedding"] for item in base])
        similaridades = cosine_similarity(embedding_pergunta, embeddings_base)[0]
        idx_mais_prox = int(np.argmax(similaridades))

        item = base[idx_mais_prox]
        resposta = item["resposta"]
        if item.get("email"):
            resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
        if item.get("modelo_email"):
            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"

        return resposta
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {e}"

def inserir_ou_atualizar_pergunta(pergunta, resposta, email="", modelo_email=""):
    try:
        embedding = get_embedding(pergunta)
        existente = obter_pergunta_por_texto(pergunta)

        dados = {
            "pergunta": pergunta,
            "resposta": resposta,
            "email": email,
            "modelo_email": modelo_email,
            "embedding": embedding
        }

        if existente:
            supabase_client.table("perguntas").update(dados).eq("pergunta", pergunta).execute()
        else:
            supabase_client.table("perguntas").insert(dados).execute()

    except Exception as e:
        print(f"Erro ao guardar pergunta: {e}")
