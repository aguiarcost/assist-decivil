# assistente.py (versão com Supabase)
import openai
import os
import json
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("SUPABASE_URL e SUPABASE_KEY devem estar definidos nas secrets ou variáveis de ambiente.")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Nome da tabela na Supabase
TABELA = "perguntas"

# Função para obter todas as perguntas e respostas

def obter_base_conhecimento():
    resposta = supabase_client.table(TABELA).select("*").execute()
    return resposta.data if resposta.data else []

# Função para guardar uma nova pergunta

def guardar_nova_pergunta(pergunta, resposta, email="", modelo_email=""):
    dados = {
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip(),
        "email": email.strip(),
        "modelo_email": modelo_email.strip()
    }
    supabase_client.table(TABELA).insert(dados).execute()

# Função para atualizar uma pergunta existente

def atualizar_pergunta(id_pergunta, novos_dados):
    supabase_client.table(TABELA).update(novos_dados).eq("id", id_pergunta).execute()

# Gerar embedding

def get_embedding(texto):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return np.array(response.data[0].embedding)

# Função principal para responder com base na base de conhecimento

def gerar_resposta(pergunta_utilizador, threshold=0.8):
    base = obter_base_conhecimento()
    if not base:
        return "❌ Base de conhecimento vazia."

    emb_utilizador = get_embedding(pergunta_utilizador).reshape(1, -1)
    emb_existentes = [get_embedding(item["pergunta"]) for item in base]
    emb_array = np.array(emb_existentes)

    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(emb_utilizador, emb_array)[0]
    idx = int(np.argmax(sims))
    if sims[idx] < threshold:
        return "❓ Não foi possível encontrar uma resposta adequada."

    item = base[idx]
    resposta = item["resposta"]
    if item.get("email"):
        resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
    if item.get("modelo_email"):
        resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email'].strip()}\n```"
    return resposta

# Função para obter ID de uma pergunta

def obter_id_por_pergunta(texto):
    base = obter_base_conhecimento()
    for item in base:
        if item["pergunta"].strip().lower() == texto.strip().lower():
            return item["id"], item
    return None, None
