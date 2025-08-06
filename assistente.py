import os
import openai
import numpy as np
from supabase import create_client, Client
from sklearn.metrics.pairwise import cosine_similarity

# Ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gerar embedding
def get_embedding(texto):
    try:
        resposta = openai.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return resposta.data[0].embedding
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return None

# Carregar todas as perguntas da base
def carregar_base_conhecimento():
    try:
        resposta = supabase_client.table("base_conhecimento").select("*").execute()
        dados = resposta.data
        return dados if dados else []
    except Exception as e:
        print(f"Erro ao carregar base: {e}")
        return []

# Guardar (ou atualizar) pergunta
def guardar_base_conhecimento(nova):
    try:
        perguntas_existentes = carregar_base_conhecimento()
        existente = next((p for p in perguntas_existentes if p["pergunta"].strip().lower() == nova["pergunta"].strip().lower()), None)
        novo_embedding = get_embedding(nova["pergunta"])
        if novo_embedding is None:
            print("❌ Falha ao gerar embedding.")
            return

        dados = {
            "pergunta": nova["pergunta"].strip(),
            "resposta": nova["resposta"].strip(),
            "email": nova.get("email", "").strip(),
            "modelo_email": nova.get("modelo_email", "").strip(),
            "embedding": novo_embedding
        }

        if existente:
            supabase_client.table("base_conhecimento").update(dados).eq("pergunta", existente["pergunta"]).execute()
        else:
            supabase_client.table("base_conhecimento").insert(dados).execute()

    except Exception as e:
        print(f"Erro ao guardar: {e}")

# Gerar resposta a partir do texto
def gerar_resposta(pergunta_utilizador, threshold=0.8):
    try:
        base = carregar_base_conhecimento()
        if not base:
            return "❌ Base de conhecimento vazia."

        embeddings = np.array([d["embedding"] for d in base if d.get("embedding")])
        perguntas = [d["pergunta"] for d in base]

        embedding_utilizador = get_embedding(pergunta_utilizador)
        if embedding_utilizador is None:
            return "❌ Erro ao gerar embedding para a pergunta."

        if len(embeddings) == 0:
            return "❌ Sem embeddings disponíveis."

        sims = cosine_similarity([embedding_utilizador], embeddings)[0]
        idx_mais_proximo = int(np.argmax(sims))
        sim = sims[idx_mais_proximo]

        if sim < threshold:
            return "❓ Não foi encontrada uma resposta suficientemente próxima."

        entrada = base[idx_mais_proximo]
        resposta = entrada["resposta"]

        if entrada.get("email"):
            resposta += f"\n\n📫 **Email de contacto:** {entrada['email']}"
        if entrada.get("modelo_email"):
            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{entrada['modelo_email']}\n```"

        return resposta

    except Exception as e:
        return f"❌ Erro a gerar resposta: {e}"
