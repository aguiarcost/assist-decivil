import openai
import json
import os
import streamlit as st

CAMINHO_BASE_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_BASE_VECTOR = "base_vectorizada.json"

# Autenticar com a API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Função para gerar embeddings com API nova
def gerar_embedding(texto):
    try:
        response = openai.embeddings.create(
            input=texto,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Erro ao gerar embedding para: {texto}\n{e}")
        return None

# Carregar base de conhecimento
with open(CAMINHO_BASE_CONHECIMENTO, "r", encoding="utf-8") as f:
    base = json.load(f)

base_vector = []

for item in base:
    pergunta = item["pergunta"]
    resposta = item["resposta"]
    modelo_email = item.get("modelo_email", "")

    embedding = gerar_embedding(pergunta)
    if embedding:
        base_vector.append({
            "pergunta": pergunta,
            "resposta": resposta,
            "modelo_email": modelo_email,
            "embedding": embedding
        })

# Guardar embeddings
with open(CAMINHO_BASE_VECTOR, "w", encoding="utf-8") as f:
    json.dump(base_vector, f, ensure_ascii=False, indent=2)

print("✅ Embeddings gerados e guardados em base_vectorizada.json")
