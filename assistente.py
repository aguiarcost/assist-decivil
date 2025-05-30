import json
import openai
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Carregar base de conhecimento manual
with open("base_conhecimento.json", "r", encoding="utf-8") as f:
    base_manual = json.load(f)

# Tentar carregar base vetorizada
try:
    with open("base_docs_vectorizada.json", "r", encoding="utf-8") as f:
        base_docs = json.load(f)
except FileNotFoundError:
    base_docs = []

# Gerar embedding para pergunta
def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

# Procurar blocos mais relevantes nos documentos vetorizados
def procurar_blocos_relevantes(embedding_pergunta, top_n=3):
    if not base_docs:
        return []

    docs_embeddings = np.array([bloco["embedding"] for bloco in base_docs])
    pergunta_vector = np.array(embedding_pergunta).reshape(1, -1)
    similaridades = cosine_similarity(pergunta_vector, docs_embeddings)[0]
    indices_top = np.argsort(similaridades)[-top_n:][::-1]
    return [base_docs[i]["texto"] for i in indices_top]

# Gerar resposta
def gerar_resposta(pergunta):
    pergunta_lower = pergunta.lower()

    # Se for uma pergunta sobre funcionalidades
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

📤 **Podes carregar ficheiros para enriquecer a base de conhecimento**, incluindo:
- PDFs
- Documentos Word (.docx)
- Websites (via URL)

📨 **Sugestões de modelos de email prontos a enviar**

Podes perguntar, por exemplo:
- "Como faço para reservar uma sala?"
- "Quem trata de avarias no telefone?"
- "Dá-me um exemplo de email para pedir estacionamento"
- "Consulta o regulamento de avaliação anexo"
"""

    # Verificar se a pergunta existe na base manual
    for entrada in base_manual:
        if entrada["pergunta"].lower() in pergunta_lower:
            resposta = entrada
            return f"""
**❓ Pergunta:** {resposta['pergunta']}

**💬 Resposta:** {resposta['resposta']}

**📧 Email de contacto:** [{resposta['email']}](mailto:{resposta['email']})

**📝 Modelo de email sugerido:**
```text
{resposta['modelo_email']}
```
"""

    # Se não encontrar, usar base vetorizada
    embedding = gerar_embedding(pergunta)
    blocos_relevantes = procurar_blocos_relevantes(embedding)

    contexto = "\n---\n".join(blocos_relevantes)
    prompt = f"""
Usa os blocos seguintes de texto como base para responder à pergunta:

{contexto}

Pergunta: {pergunta}

Responde com:
- uma explicação clara
- o email de contacto, se existir
- um modelo de email sugerido, se fizer sentido
    """

    resposta = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return resposta.choices[0].message.content
