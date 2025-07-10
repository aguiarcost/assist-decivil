import json
import os
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

# Caminhos de ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_DOCS = "base_vectorizada.json"

# Chave da API
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
elif os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY"])
else:
    st.warning("⚠️ A chave da API não está definida.")

# Gerar embedding para texto
def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

# Carregar base manual
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Carregar base vetorial
def carregar_base_docs():
    if os.path.exists(CAMINHO_DOCS):
        try:
            with open(CAMINHO_DOCS, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Procurar blocos mais relevantes
def procurar_blocos_relevantes(embedding_pergunta, base_docs, top_n=3):
    if not base_docs:
        return []

    docs_embeddings = np.array([bloco["embedding"] for bloco in base_docs])
    pergunta_vector = np.array(embedding_pergunta).reshape(1, -1)
    similaridades = cosine_similarity(pergunta_vector, docs_embeddings)[0]
    indices_top = np.argsort(similaridades)[-top_n:][::-1]

    blocos = []
    for i in indices_top:
        bloco = base_docs[i]
        bloco_copy = bloco.copy()
        bloco_copy["similaridade"] = round(float(similaridades[i]), 3)
        blocos.append(bloco_copy)
    return blocos

# Gerar resposta
def gerar_resposta(pergunta):
    pergunta_lower = pergunta.lower()
    base_manual = carregar_base_conhecimento()
    base_docs = carregar_base_docs()

    # Verificar se a pergunta está na base manual
    for entrada in base_manual:
        if entrada["pergunta"].lower().strip() == pergunta_lower.strip():
            resposta = entrada["resposta"]
            email = entrada.get("email")
            modelo = entrada.get("modelo_email")

            resultado = f"**❓ Pergunta:** {entrada['pergunta']}\n\n"
            resultado += f"**💬 Resposta:** {resposta}\n\n"
            if email:
                resultado += f"**📧 Email de contacto:** [{email}](mailto:{email})\n\n"
            if modelo:
                resultado += f"**📝 Modelo de email sugerido:**\n\n```\n{modelo}\n```"
            return resultado

    # Se não estiver na base manual, procurar nos documentos
    embedding_pergunta = gerar_embedding(pergunta)
    blocos_relevantes = procurar_blocos_relevantes(embedding_pergunta, base_docs)

    if blocos_relevantes:
        resposta = "\n\n".join([f"**Trecho relevante:**\n{bloco['texto']}\n\n_Similaridade: {bloco['similaridade']}_" for bloco in blocos_relevantes])
        return resposta

    return "❌ Não foi encontrada resposta para a pergunta. Por favor, tente reformular ou contacte os serviços administrativos."
