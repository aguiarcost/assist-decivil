import json
import openai
import streamlit as st
import numpy as np
from openai import OpenAI

# Caminhos para os ficheiros
CAMINHO_BASE = "base_conhecimento.json"
CAMINHO_VETORES = "base_vectorizada.json"

# API Key segura via Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI()

# Carregar base de conhecimento e embeddings
def carregar_dados():
    with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
        conhecimento = json.load(f)

    with open(CAMINHO_VETORES, "r", encoding="utf-8") as f:
        dados = json.load(f)

    perguntas = [item["pergunta"] for item in dados]
    embeddings = [item["embedding"] for item in dados]

    return conhecimento, perguntas, np.array(embeddings)

# Carregar perguntas frequentes diretamente da base de conhecimento
def carregar_perguntas_frequentes():
    with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
        conhecimento = json.load(f)
    return [item["pergunta"] for item in conhecimento]

# Gerar embedding da pergunta usando a API OpenAI
def gerar_embedding(pergunta):
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=pergunta
        )
        return response.data[0].embedding
    except Exception as e:
        return f"❌ Erro ao gerar embedding da pergunta:\n\n{e}"

# Similaridade cosseno entre dois vetores
def cosine_similarity(vec1, vec2):
    vec1, vec2 = np.array(vec1), np.array(vec2)
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot / (norm1 * norm2)

# Geração de resposta principal
def gerar_resposta(pergunta, usar_embedding=False, top_k=1):
    conhecimento, perguntas_emb, embeddings = carregar_dados()

    if usar_embedding:
        embedding_pergunta = gerar_embedding(pergunta)
        if isinstance(embedding_pergunta, str):  # Caso de erro (mensagem de erro)
            return embedding_pergunta, ""

        similaridades = [cosine_similarity(embedding_pergunta, emb) for emb in embeddings]
        top_indices = np.argsort(similaridades)[-top_k:][::-1]
        melhores = [perguntas_emb[i] for i in top_indices]
    else:
        melhores = [pergunta]

    for entrada in conhecimento:
        if entrada["pergunta"] == melhores[0]:
            resposta = entrada["resposta"]
            modelo_email = entrada.get("modelo_email", "")
            return resposta, modelo_email

    return "Não encontrei uma resposta adequada.", ""
