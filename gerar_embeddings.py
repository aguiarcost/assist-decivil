import json
import numpy as np
from openai import OpenAI
import streamlit as st

CAMINHO_BASE = "base_conhecimento.json"
CAMINHO_SAIDA = "base_vectorizada.json"

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def gerar_embedding(pergunta):
    response = client.embeddings.create(
        input=pergunta,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

def main():
    with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
        conhecimento = json.load(f)

    vetor_final = []

    for item in conhecimento:
        pergunta = item["pergunta"]
        try:
            embedding = gerar_embedding(pergunta)
            vetor_final.append({
                "pergunta": pergunta,
                "embedding": embedding
            })
            print(f"✅ Embedding gerado para: {pergunta}")
        except Exception as e:
            print(f"❌ Erro ao gerar embedding para: {pergunta}\n{e}")

    with open(CAMINHO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(vetor_final, f, ensure_ascii=False, indent=2)

    print(f"✨ Embeddings guardados em {CAMINHO_SAIDA}")

if __name__ == "__main__":
    main()
