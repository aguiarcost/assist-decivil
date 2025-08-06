import os
import openai
import numpy as np
from openai import OpenAIError
from supabase import create_client, Client
from sklearn.metrics.pairwise import cosine_similarity

# Carregar variáveis de ambiente
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "decivil2024")  # Password admin (default "decivil2024")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not (SUPABASE_URL and SUPABASE_KEY and OPENAI_API_KEY):
    raise EnvironmentError("⚠️ É necessário definir SUPABASE_URL, SUPABASE_KEY e OPENAI_API_KEY.")

# Inicializar clientes (Supabase e OpenAI)
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

# ------------------------
# Funções principais
# ------------------------

def carregar_base_conhecimento():
    """Carrega todas as perguntas da tabela 'base_conhecimento' do Supabase."""
    try:
        response = supabase_client.table("base_conhecimento").select("*").execute()
        return response.data  # retorna uma lista de registros (dicionários)
    except Exception as e:
        print("Erro ao carregar base de conhecimento:", e)
        return []

def gerar_resposta(pergunta):
    """
    Encontra a pergunta correspondente (ignorando maiúsculas/minúsculas) e retorna a resposta formatada,
    incluindo email de contacto e modelo de email se disponíveis.
    """
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

def gerar_embedding(texto):
    """Gera o embedding (vetor) para um dado texto usando o modelo de embedding da OpenAI."""
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return np.array(response.data[0]["embedding"])
    except OpenAIError as e:
        # Log de erro para debug
        print(f"Erro ao gerar embedding para '{texto}':", e)
        # Poderíamos retornar None ou um vetor vazio em caso de erro
        return np.array([])

def adicionar_pergunta_supabase(pergunta, resposta, email="", modelo_email=""):
    """Adiciona uma nova pergunta/resposta (e campos opcionais) na tabela Supabase. Retorna True/False conforme sucesso."""
    try:
        embedding = gerar_embedding(pergunta)
        data = {
            "pergunta": pergunta.strip(),
            "resposta": resposta.strip(),
            "email": email.strip(),
            "modelo_email": modelo_email.strip(),
            "embedding": embedding.tolist()  # converter numpy array para lista para armazenar (JSON)
        }
        supabase_client.table("base_conhecimento").insert(data).execute()
        return True
    except Exception as e:
        print("Erro ao adicionar pergunta:", e)
        return False

def atualizar_pergunta_supabase(pergunta, nova_resposta, novo_email="", novo_modelo=""):
    """Atualiza os campos de uma pergunta existente na tabela Supabase. Retorna True/False conforme sucesso."""
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
