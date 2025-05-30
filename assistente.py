import json
import openai
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Lê a chave da OpenAI dos segredos (via Streamlit Cloud)
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Carrega base manual de perguntas/respostas
with open("base_conhecimento.json", "r", encoding="utf-8") as f:
    base_manual = json.load(f)

# Carrega base vetorizada de documentos (se existir)
try:
    with open("base_docs_vectorizada.json", "r", encoding="utf-8") as f:
        base_docs = json.load(f)
except FileNotFoundError:
    base_docs = []

# Função para gerar embedding da pergunta
def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

# Função para encontrar os blocos de documentos mais relevantes
def procurar_blocos_relevantes(embedding_pergunta, top_n=3):
    if not base_docs:
        return []

    docs_embeddings = np.array([bloco["embedding"] for bloco in base_docs])
    pergunta_vector = np.array(embedding_pergunta).reshape(1, -1)

    similaridades = cosine_similarity(pergunta_vector, docs_embeddings)[0]
    indices_top = np.argsort(similaridades)[-top_n:][::-1]

    blocos_relevantes = [base_docs[i] for i in indices_top]
    return blocos_relevantes

# Função principal de resposta
def gerar_resposta(pergunta):
    pergunta_lower = pergunta.lower()

    # Resposta padrão sobre o que o assistente pode fazer
    if any(x in pergunta_lower for x in [
        "o que podes fazer", "que sabes fazer", "para que serves",
        "lista de coisas", "ajudas com", "que tipo de", "funcionalidades"
    ]):
        return """
Posso ajudar-te com várias tarefas administrativas no DECivil. Eis alguns exemplos:

✅ Informações sobre:
- Como reservar salas (GOP)
- Pedidos de estacionamento
- Apoio informático e acesso Wi-Fi
- Registo de convidados no sistema
- Declarações e contactos com a DRH
- Comunicação de avarias

📄 Também posso consultar documentos administrativos para responder a perguntas mais específicas, como:
- Regulamentos
- Orientações internas
- Notas informativas

📨 E ainda sugiro modelos de email prontos a enviar sempre que possível.

Podes perguntar, por exemplo:
- "Como faço para reservar uma sala?"
- "Quem trata de avarias no telefone?"
- "Dá-me um exemplo de email para pedir estacionamento"
"""

    # Caso normal com embeddings e contexto
    embedding = gerar_embedding(pergunta)
    blocos = procurar_blocos_relevantes(embedding, top_n=3)

    contexto = "\n\n".join(
        f"[{bloco['origem']}, página {bloco['pagina']}]:\n{bloco['texto']}" for bloco in blocos
    )

    prompt = f"""
Estás a ajudar docentes e investigadores do DECivil a resolver dúvidas administrativas.

Usa a seguinte base de conhecimento estruturada:
{json.dumps(base_manual, indent=2)}

E, se necessário, também estes excertos retirados de documentos:
{contexto}

Pergunta: {pergunta}

Responde com:
- uma explicação simples
- o contacto de email
- um modelo de email sugerido (se aplicável)
"""

    resposta = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return resposta.choices[0].message.content
