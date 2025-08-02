import os
import json
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from supabase import create_client

# Configurações de API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Carregar dados da base de conhecimento ----------
def carregar_base_conhecimento():
    try:
        response = supabase.table("conhecimento").select("*").execute()
        if response.data:
            return response.data
    except Exception as e:
        print(f"❌ Erro ao carregar base de conhecimento: {e}")
    return []

def guardar_base_conhecimento(lista):
    try:
        # Limpa a tabela e reescreve tudo
        supabase.table("conhecimento").delete().neq("pergunta", "").execute()
        for item in lista:
            supabase.table("conhecimento").insert(item).execute()
    except Exception as e:
        print(f"❌ Erro ao guardar base de conhecimento: {e}")

# ---------- Embeddings ----------
def gerar_embedding(texto):
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Erro ao gerar embedding para: {texto}\n{e}")
        return None

def carregar_embeddings():
    try:
        response = supabase.table("conhecimento_vector").select("*").execute()
        data = response.data or []
        # Filtrar apenas os que têm embedding válido
        data = [d for d in data if "embedding" in d and "pergunta" in d]
        embeddings = np.array([d["embedding"] for d in data])
        perguntas = [d["pergunta"] for d in data]
        return data, perguntas, embeddings
    except Exception as e:
        print(f"❌ Erro a carregar embeddings: {e}")
        return [], [], np.array([])

def guardar_embeddings(lista):
    try:
        # Limpa e reinsere todos os embeddings
        supabase.table("conhecimento_vector").delete().neq("pergunta", "").execute()
        for item in lista:
            supabase.table("conhecimento_vector").insert(item).execute()
    except Exception as e:
        print(f"❌ Erro ao guardar embeddings: {e}")

# ---------- Gerar resposta ----------
def gerar_resposta(pergunta_utilizador, threshold=0.8):
    try:
        conhecimento = carregar_base_conhecimento()
        dados, perguntas, embeddings = carregar_embeddings()

        # Verificar correspondência exata
        for item in conhecimento:
            if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                modelo = item.get("modelo_email", "")
                if modelo:
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
                return resposta

        # Embedding da pergunta
        embedding_novo = gerar_embedding(pergunta_utilizador)
        if embedding_novo is None or len(embeddings) == 0:
            return "❓ Não foi possível encontrar uma resposta adequada."

        # Similaridade
        embedding_novo = np.array(embedding_novo).reshape(1, -1)
        sims = cosine_similarity(embedding_novo, embeddings)[0]
        idx = int(np.argmax(sims))
        if sims[idx] >= threshold:
            item = dados[idx]
            resposta = item["resposta"]
            if item.get("email"):
                resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
            modelo = item.get("modelo_email", "")
            if modelo:
                resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
            return resposta

        return "❓ Não foi possível encontrar uma resposta adequada."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {str(e)}"
