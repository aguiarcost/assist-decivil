import os
import openai
import supabase
from supabase import create_client
import numpy as np

# Configurações Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurar OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def listar_perguntas():
    try:
        res = supabase_client.table("perguntas").select("pergunta").execute()
        return [r["pergunta"] for r in res.data]
    except:
        return []

def obter_pergunta_por_texto(texto):
    res = supabase_client.table("perguntas").select("*").eq("pergunta", texto).execute()
    if res.data:
        return res.data[0]
    return None

def adicionar_ou_atualizar_pergunta(pergunta, resposta, email, modelo_email):
    existente = obter_pergunta_por_texto(pergunta)
    if existente:
        supabase_client.table("perguntas").update({
            "resposta": resposta,
            "email": email,
            "modelo_email": modelo_email
        }).eq("pergunta", pergunta).execute()
    else:
        supabase_client.table("perguntas").insert([{
            "pergunta": pergunta,
            "resposta": resposta,
            "email": email,
            "modelo_email": modelo_email
        }]).execute()

def gerar_resposta(pergunta_utilizador):
    item = obter_pergunta_por_texto(pergunta_utilizador)
    if item:
        resposta = item["resposta"]
        if item.get("email"):
            resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
        modelo = item.get("modelo_email")
        if modelo:
            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo.strip()}\n```"
        return resposta
    return "❓ Não encontrei resposta para essa pergunta."
