import json
import openai
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Carregar base manual
with open("base_conhecimento.json", "r", encoding="utf-8") as f:
    base_manual = json.load(f)

# Carregar base vetorizada
try:
    with open("base_docs_vectorizada.json", "r", encoding="utf-8") as f:
        base_docs = json.load(f)
except FileNotFoundError:
    base_docs = []

def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

def procurar_blocos_relevantes(embedding_pergunta, top_n=3):
    if not base_docs:
        return []

    docs_embeddings = np.array([bloco["embedding"] for bloco in base_docs])
    pergunta_vector = np.array(embedding_pergunta).reshape(1, -1)
    similaridades = cosine_similarity(pergunta_vector, docs_embeddings)[0]
    indices_top = np.argsort(similaridades)[-top_n:][::-1]
    return [base_docs[i] for i in indices_top]

def gerar_resposta(pergunta):
    pergunta_lower = pergunta.lower()

    # Explicação das funcionalidades
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

    # Verificar se pergunta já existe na base manual
    for entrada in base_manual:
        if entrada["pergunta"].lower() in pergunta_lower:
            resposta = entrada
            break
    else:
        # Se não existir, usa contexto documental
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

        resultado = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return resultado.choices[0].message.content

    # Se for resposta manual, formatar
    if isinstance(resposta, dict):
        return f"""
**❓ Pergunta:** {resposta['pergunta']}

**💬 Resposta:** {resposta['resposta']}

**📧 Email de contacto:** [{resposta['email']}](mailto:{resposta['email']})

**📝 Modelo de email sugerido:**

