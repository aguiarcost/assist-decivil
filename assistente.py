import os
import hashlib
import numpy as np
from openai import OpenAI
from supabase import create_client, Client
from sklearn.metrics.pairwise import cosine_similarity

# Carregar variáveis de ambiente
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not (SUPABASE_URL and SUPABASE_KEY and OPENAI_API_KEY):
    raise EnvironmentError("⚠️ É necessário definir SUPABASE_URL, SUPABASE_KEY e OPENAI_API_KEY.")

# Inicializar clientes
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def gerar_embedding(texto: str) -> np.ndarray:
    """Gera embedding com OpenAI."""
    try:
        response = openai_client.embeddings.create(model="text-embedding-3-small", input=texto)
        return np.array(response.data[0].embedding)
    except Exception as e:
        raise RuntimeError(f"Erro ao gerar embedding: {e}")

def carregar_base_conhecimento():
    """Carrega base de conhecimento do Supabase."""
    try:
        response = supabase_client.table("base_conhecimento").select("*").execute()
        return response.data
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar base de conhecimento: {e}")

def gerar_resposta(pergunta: str) -> str:
    """Gera resposta: exata ou semântica via embeddings."""
    perguntas = carregar_base_conhecimento()
    pergunta_input = pergunta.strip().lower()
    embedding_input = gerar_embedding(pergunta_input)
    
    # Busca exata primeiro
    for item in perguntas:
        if item["pergunta"].strip().lower() == pergunta_input:
            return formatar_resposta(item)
    
    # Busca semântica se não exata
    max_sim = 0
    best_item = None
    for item in perguntas:
        emb_db = np.array(item.get("embedding"))
        if emb_db.size > 0:
            sim = cosine_similarity([embedding_input], [emb_db])[0][0]
            if sim > max_sim:
                max_sim = sim
                best_item = item
    
    if max_sim > 0.8:  # Threshold para match aproximado
        return formatar_resposta(best_item) + f"\n\n(Resposta baseada em similaridade: {max_sim:.2f})"
    
    return "❓ Não foi possível encontrar uma resposta para essa pergunta."

def formatar_resposta(item: dict) -> str:
    """Formata resposta com email e modelo."""
    resposta = item.get("resposta", "").strip()
    email = item.get("email", "").strip()
    modelo = item.get("modelo_email", "").strip()
    if email:
        resposta += f"\n\n📫 **Email de contacto:** {email}"
    if modelo:
        resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
    return resposta

def adicionar_pergunta_supabase(pergunta: str, resposta: str, email: str = "", modelo_email: str = "") -> bool:
    """Adiciona pergunta ao Supabase."""
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
        print(f"Erro ao adicionar pergunta: {e}")
        return False

def atualizar_pergunta_supabase(pergunta: str, nova_resposta: str, novo_email: str = "", novo_modelo: str = "") -> bool:
    """Atualiza pergunta no Supabase."""
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
        print(f"Erro ao atualizar pergunta: {e}")
        return False
