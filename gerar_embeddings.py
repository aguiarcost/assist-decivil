
import json
import os
import numpy as np
from openai import OpenAI
from tqdm import tqdm

CAMINHO_BASE = "base_conhecimento.json"
CAMINHO_EMBEDDINGS = "embeddings.npy"
CAMINHO_INDICE = "indice.json"

client = OpenAI()

def gerar_embedding(texto):
    try:
        response = client.embeddings.create(
            input=texto,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Erro ao gerar embedding para: {texto}\n{e}")
        return None

# Carregar base de conhecimento
with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
    base = json.load(f)

embeddings = []
indice = []

# Gerar embeddings
for item in tqdm(base):
    pergunta = item.get("pergunta")
    if pergunta:
        emb = gerar_embedding(pergunta)
        if emb:
            embeddings.append(emb)
            indice.append(pergunta)

# Guardar resultados
np.save(CAMINHO_EMBEDDINGS, np.array(embeddings))
with open(CAMINHO_INDICE, "w", encoding="utf-8") as f:
    json.dump(indice, f, ensure_ascii=False, indent=2)

print("Embeddings gerados com sucesso.")
