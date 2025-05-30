import openai
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Lê a base de dados com os embeddings
with open("base_vectorizada.json", "r", encoding="utf-8") as f:
    base = json.load(f)

def gerar_resposta(pergunta):
    # Gerar embedding da pergunta
    resposta_emb = openai.embeddings.create(
        input=pergunta,
        model="text-embedding-3-small"
    ).data[0].embedding

    # Preparar os dados
    textos = [item["texto"] for item in base]
    embeddings = [item["embedding"] for item in base]

    # Calcular similaridades
    sims = cosine_similarity(
        [resposta_emb],
        embeddings
    )[0]

    # Escolher os 3 mais relevantes
    top_idxs = sims.argsort()[-3:][::-1]
    contexto = "\n\n".join([textos[i] for i in top_idxs])

    # Criar prompt
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
