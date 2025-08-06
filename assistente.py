import os
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

def carregar_base_conhecimento():
    try:
        response = supabase_client.table("base_conhecimento").select("*").execute()
        return response.data or []
    except Exception as e:
        print(f"Erro ao carregar base de conhecimento: {e}")
        return []

def guardar_base_conhecimento(perguntas):
    try:
        for pergunta in perguntas:
            supabase_client.table("base_conhecimento").insert(pergunta).execute()
    except Exception as e:
        print(f"Erro ao guardar pergunta: {e}")
        raise

def editar_base_conhecimento(pergunta_antiga, pergunta_nova):
    try:
        supabase_client.table("base_conhecimento").update(pergunta_nova).eq("pergunta", pergunta_antiga).execute()
    except Exception as e:
        print(f"Erro ao editar pergunta: {e}")
        raise

def gerar_embedding(texto):
    try:
        response = openai.embeddings.create(model="text-embedding-3-small", input=texto)
        return np.array(response.data[0].embedding).tolist()
    except Exception as e:
        print(f"Erro ao gerar embedding para: {texto}\n{e}")
        return []

def gerar_resposta(pergunta):
    perguntas = carregar_base_conhecimento()
    perguntas_dict = {p["pergunta"]: p for p in perguntas}

    if pergunta in perguntas_dict:
        item = perguntas_dict[pergunta]
        resposta = item.get("resposta", "")
        email = item.get("email", "")
        modelo = item.get("modelo_email", "")

        resposta_final = resposta
        if email:
            resposta_final += f"\n\n📫 **Email de contacto:** {email}"
        if modelo:
            resposta_final += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"

        return resposta_final

    return "❌ Pergunta não encontrada na base de conhecimento."
