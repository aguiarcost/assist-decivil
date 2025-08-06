import os
import openai
import numpy as np
from openai import OpenAIError
from supabase import create_client, Client
from sklearn.metrics.pairwise import cosine_similarity

# Carregar variáveis de ambiente
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not (SUPABASE_URL and SUPABASE_KEY and OPENAI_API_KEY):
    raise EnvironmentError("⚠️ É necessário definir SUPABASE_URL, SUPABASE_KEY e OPENAI_API_KEY.")

# Inicializar clientes
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

# ------------------------
# Funções principais
# ------------------------

def carregar_base_conhecimento():
    try:
        response = supabase_client.table("base_conhecimento").select("*").execute()
        data = response.data if hasattr(response, "data") else []
        perguntas_validas = [p for p in data if "pergunta" in p and "resposta" in p]
        return perguntas_validas
    except Exception as e:
        print(f"Erro ao carregar perguntas da base de conhecimento: {e}")
        return []

def gerar_resposta(pergunta):
    perguntas = carregar_base_conhecimento()
    pergunta_input = pergunta.strip().lower()
    for item in perguntas:
        if item["pergunta"].strip().lower() == pergunta_input:
            resposta = item.get("resposta", "").strip()
            email = item.get("email", "").strip()
            modelo = item.get("modelo_email", "").strip()

            if email:
                resposta += f"\n\n📫 **Email de contacto:** {email}"
            if modelo:
                resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"

            return resposta

    return "❓ Não foi possível encontrar uma resposta para essa pergunta."

def adicionar_pergunta_supabase(pergunta, resposta, email="", modelo_email=""):
    try:
        embedding = gerar_embedding(pergunta)
        data = {
            "pergunta": pergunta.strip(),
            "resposta": resposta.strip(),
            "email": email.strip(),
            "modelo_email": modelo_email.strip(),
            "embedding": embedding.tolist()
        }
        supabase_client.table("base_conhecimento").insert(data).execute()
        return True
    except Exception as e:
        print("Erro ao adicionar pergunta:", e)
        return False

def atualizar_pergunta_supabase(pergunta, nova_resposta, novo_email="", novo_modelo=""):
    try:
        embedding = gerar_embedding(pergunta)
        supabase_client.table("base_conhecimento").update({
            "resposta": nova_resposta.strip(),
            "email": novo_email.strip(),
            "modelo_email": novo_modelo.strip(),
            "embedding": embedding.tolist()
        }).eq("pergunta", pergunta).execute()
        return True
    except Exception as e:
        print("Erro ao atualizar pergunta:", e)
        return False

def gerar_embedding(texto):
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return np.array(response.data[0].embedding)
    except OpenAIError as e:
        print("Erro ao gerar embedding:", e)
        raise
