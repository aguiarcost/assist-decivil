import openai
import json
import os

# API key
if "OPENAI_API_KEY" in os.environ:
    openai.api_key = os.environ["OPENAI_API_KEY"]

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_EMBEDDINGS = "base_embeddings.json"

def gerar_embeddings():
    with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
        base = json.load(f)

    dados_emb = []

    for item in base:
        pergunta = item["pergunta"]
        try:
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=pergunta
            )
            embedding = response.data[0].embedding
            dados_emb.append({"pergunta": pergunta, "embedding": embedding})
            print(f"✅ Embedding gerado: {pergunta}")
        except Exception as e:
            print(f"Erro ao gerar embedding para: {pergunta}\n{e}")

    with open(CAMINHO_EMBEDDINGS, "w", encoding="utf-8") as f:
        json.dump(dados_emb, f)

if __name__ == "__main__":
    gerar_embeddings()
