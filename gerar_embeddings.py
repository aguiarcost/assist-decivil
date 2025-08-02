import os
import openai
import numpy as np
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

def gerar_embedding(texto):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return response.data[0].embedding

def atualizar_todos_embeddings():
    dados = supabase.table("base_conhecimento").select("*").execute().data

    for item in dados:
        if item.get("pergunta"):
            embedding = gerar_embedding(item["pergunta"])
            supabase.table("base_conhecimento").update({
                "embedding": embedding
            }).eq("id", item["id"]).execute()
            print(f"Embedding atualizado para: {item['pergunta']}")

if __name__ == "__main__":
    atualizar_todos_embeddings()
