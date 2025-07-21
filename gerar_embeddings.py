
import openai
import pickle
import os
import json
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import numpy as np

CAMINHO_EMBEDDINGS = "embeddings.pkl"
CAMINHO_CONHECIMENTO = "base_conhecimento.json"

def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def gerar_embedding_openai(texto):
    try:
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=texto
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return None

def guardar_na_base_com_embbeding(texto, origem="Documento carregado"):
    base_conhecimento = carregar_base_conhecimento()
    nova_entrada = {
        "pergunta": origem,
        "resposta": texto.strip(),
        "email": "",
        "modelo": ""
    }
    base_conhecimento.append(nova_entrada)

    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base_conhecimento, f, ensure_ascii=False, indent=2)

    # Gerar e guardar embedding
    embedding = gerar_embedding_openai(origem)
    if embedding:
        with open(CAMINHO_EMBEDDINGS, "ab") as f:
            pickle.dump((origem, embedding), f)
