import os
import openai
from supabase import create_client, Client
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# API Keys via variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validar credenciais
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("⚠️ SUPABASE_URL e SUPABASE_KEY não estão definidas.")
if not OPENAI_API_KEY:
    raise ValueError("⚠️ OPENAI_API_KEY não está definida.")

# Inicializar clientes
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

# Carregar perguntas
def carregar_base_conhecimento():
    try:
        response = supabase_client.table("base_conhecimento").select("*").execute()
        data = response.data if hasattr(response, "data") else []
        perguntas_validas = [p for p in data if "pergunta" in p and "resposta" in p]
        return perguntas_validas
    except Exception as e:
        print(f"Erro ao carregar perguntas da base de conhecimento: {e}")
        return []

# Guardar nova ou atualizar
def guardar_base_conhecimento(pergunta_dict):
    try:
        pergunta = pergunta_dict["pergunta"]
        existente = supabase_client.table("base_conhecimento").select("*").eq("pergunta", pergunta).execute()
        if existente.data:
            supabase_client.table("base_conhecimento").update(pergunta_dict).eq("pergunta", pergunta).execute()
        else:
            supabase_client.table("base_conhecimento").insert(pergunta_dict).execute()
    except Exception as e:
        print(f"Erro ao guardar pergunta: {e}")

# Gerar resposta com email e modelo
def gerar_resposta(pergunta_texto):
    try:
        base = carregar_base_conhecimento()
        for item in base:
            if item["pergunta"].strip().lower() == pergunta_texto.strip().lower():
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                if item.get("modelo_email"):
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
                return resposta
        return "❓ Não encontrei uma resposta para essa pergunta."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {e}"
        return np.array(response.data[0].embedding)
    except OpenAIError as e:
        print("Erro ao gerar embedding:", e)
        raise
