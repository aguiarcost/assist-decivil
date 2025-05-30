import openai
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Carregar base vectorizada
with open("base_vectorizada.json", "r", encoding="utf-8") as f:
    base = json.load(f)

def gerar_embedding(texto):
    response = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def gerar_resposta(pergunta):
    pergunta_emb = gerar_embedding(pergunta)
    pergunta_emb_np = np.array(pergunta_emb).reshape(1, -1)

    textos = [item["texto"] for item in base]
    embeddings = [item["embedding"] for item in base]
    embeddings_np = np.array(embeddings)

    # Calcular similaridade
    sims = cosine_similarity(pergunta_emb_np, embeddings_np)[0]
    top_idxs = sims.argsort()[-3:][::-1]
    contexto = "\n\n".join([textos[i] for i in top_idxs])

    prompt = f"""
    Estás a ajudar docentes e investigadores do DECivil a tratarem de assuntos administrativos,
    sem recorrer ao secretariado. Usa apenas o seguinte contexto:

    {contexto}

    Pergunta: {pergunta}
    Responde com:
    - uma explicação simples
    - o contacto de email, se aplicável
    - e um modelo de email sugerido, se fizer sentido.
    """

    resposta = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return resposta.choices[0].message.content
