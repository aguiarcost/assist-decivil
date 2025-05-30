import json
import openai
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Chave da API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Base de conhecimento manual
with open("base_conhecimento.json", "r", encoding="utf-8") as f:
    base_manual = json.load(f)

# Base de documentos vetorizados
try:
    with open("base_docs_vectorizada.json", "r", encoding="utf-8") as f:
        base_docs = json.load(f)
except FileNotFoundError:
    base_docs = []

# Embedding da pergunta
def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

# Encontrar blocos mais relevantes
def procurar_blocos_relevantes(embedding_pergunta, top_n=3):
    if not base_docs:
        return []

    docs_embeddings = np.array([bloco["embedding"] for bloco in base_docs])
    pergunta_vector = np.array(embedding_pergunta).reshape(1, -1)
    similaridades = cosine_similarity(pergunta_vector, docs_embeddings)[0]
    indices_top = np.argsort(similaridades)[-top_n:][::-1]
    return [base_docs[i] for i in indices_top]

# Função principal
def gerar_resposta(pergunta):
    pergunta_lower = pergunta.lower()

    # Resposta padrão sobre funcionalidades
    if any(x in pergunta_lower for x in [
        "o que podes fazer", "que sabes fazer", "para que serves",
        "lista de coisas", "ajudas com", "que tipo de", "funcionalidades"
    ]):
        return """
**📌 Posso ajudar-te com várias tarefas administrativas no DECivil:**

✅ **Informações rápidas**:
- Como reservar salas (GOP)
- Pedidos de estacionamento
- Apoio informático e acesso Wi-Fi
- Registo de convidados no sistema
- Declarações e contactos com a DRH
- Comunicação de avarias

📄 **Consulta de documentos administrativos**, como:
- Regulamentos
- Orientações internas
- Notas informativas

📨 **Sugestões de modelos de email prontos a enviar**

Podes perguntar, por exemplo:
- "Como faço para reservar uma sala?"
- "Quem trata de avarias no telefone?"
- "Dá-me um exemplo de email para pedir estacionamento"
"""

    # Procurar na base manual
    for entrada in base_manual:
        if entrada["pergunta"].lower() in pergunta_lower:
            resposta = entrada
            return f"""
**❓ Pergunta:** {resposta['pergunta']}

**💬 Resposta:** {resposta['resposta']}

**📧 Email de contacto:** [{resposta['email']}](mailto:{resposta['email']})

**📝 Modelo de email sugerido:**

