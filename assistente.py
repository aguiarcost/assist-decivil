import json
import streamlit as st
import numpy as np
from openai import OpenAI

CAMINHO_BASE = "base_conhecimento.json"
CAMINHO_VETORES = "base_vectorizada.json"

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def carregar_dados():
    with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
        conhecimento = json.load(f)

    with open(CAMINHO_VETORES, "r", encoding="utf-8") as f:
        dados = json.load(f)

    perguntas = [item["pergunta"] for item in dados]
    embeddings = [item["embedding"] for item in dados]

    return conhecimento, perguntas, np.array(embeddings)

def carregar_perguntas_frequentes():
    with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
        return [item["pergunta"] for item in json.load(f)]

def gerar_embedding(pergunta):
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=pergunta
        )
        return response.data[0].embedding
    except Exception as e:
        return f"❌ Erro ao gerar embedding da pergunta:\n\n{e}"

def cosine_similarity(vec1, vec2):
    vec1, vec2 = np.array(vec1), np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def gerar_resposta(pergunta, usar_embedding=False):
    conhecimento, perguntas_emb, embeddings = carregar_dados()

    if not usar_embedding:
        for entrada in conhecimento:
            if entrada["pergunta"].strip().lower() == pergunta.strip().lower():
                return entrada["resposta"], entrada.get("modelo_email", "")
        return "Não encontrei uma resposta exata.", ""

    embedding_pergunta = gerar_embedding(pergunta)
    if isinstance(embedding_pergunta, str):  # mensagem de erro
        return embedding_pergunta, ""

    similaridades = [cosine_similarity(embedding_pergunta, emb) for emb in embeddings]
    top_index = int(np.argmax(similaridades))
    pergunta_mais_similar = perguntas_emb[top_index]

    for entrada in conhecimento:
        if entrada["pergunta"] == pergunta_mais_similar:
            return entrada["resposta"], entrada.get("modelo_email", "")

    return "Não encontrei uma resposta adequada.", ""
