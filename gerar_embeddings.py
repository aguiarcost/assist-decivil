import os
from dotenv import load_dotenv
from assistente import supabase_client, gerar_embedding  # Reutiliza funções de assistente.py

# Carrega variáveis de ambiente do arquivo .env (se estiver rodando localmente)
load_dotenv()

# Atualiza os embeddings de todas as perguntas na tabela 'base_conhecimento' no Supabase
def atualizar_todos_embeddings():
    dados = supabase_client.table("base_conhecimento").select("*").execute().data
    for item in dados:
        if item.get("pergunta"):
            embedding = gerar_embedding(item["pergunta"])
            supabase_client.table("base_conhecimento").update({"embedding": embedding.tolist()}).eq("id", item["id"]).execute()
            print(f"Embedding atualizado para: {item['pergunta']}")

if __name__ == "__main__":
    atualizar_todos_embeddings()
