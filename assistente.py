import openai
import os
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Carregar chave API
openai.api_key = os.getenv("OPENAI_API_KEY")


def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def guardar_base_conhecimento(nova_lista):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(nova_lista, f, ensure_ascii=False, indent=2)


# Gerar embedding
def get_embedding(text):
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small", input=text
        )
        return np.array(response.data[0].embedding).reshape(1, -1)
    except Exception as e:
        print(f"❌ Erro a gerar embedding para: {text}\n{e}")
        return None


# Carregar embeddings
def carregar_embeddings():
    if os.path.exists(CAMINHO_KNOWLEDGE_VECTOR):
        try:
            with open(CAMINHO_KNOWLEDGE_VECTOR, "r", encoding="utf-8") as f:
                dados = json.load(f)
                perguntas = [item["pergunta"] for item in dados]
                embeddings = np.array([item["embedding"] for item in dados])
                return perguntas, embeddings, dados
        except Exception as e:
            print(f"Erro ao carregar embeddings: {e}")
    return [], np.array([]), []


# Gerar resposta
def gerar_resposta(pergunta_utilizador, threshold=0.8):
    try:
        base_conhecimento = carregar_base_conhecimento()
        perguntas_emb, embeddings, dados_emb = carregar_embeddings()

        # Verificar correspondência exata
        for item in base_conhecimento:
            if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 <strong>Email de contacto:</strong> {item['email']}"
                modelo = item.get("modelo_email", "")
                if modelo:
                    resposta += f"\n\n📧 <strong>Modelo de email sugerido:</strong><br><pre>{modelo}</pre>"
                return resposta

        # Verificar por similaridade
        if embeddings.size > 0:
            embedding_utilizador = get_embedding(pergunta_utilizador)
            if embedding_utilizador is None:
                return "❌ Erro ao gerar embedding da pergunta."

            sims = cosine_similarity(embedding_utilizador, embeddings)[0]
            max_sim = np.max(sims)
            if max_sim >= threshold:
                idx = int(np.argmax(sims))
                item = dados_emb[idx]
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 <strong>Email de contacto:</strong> {item['email']}"
                modelo = item.get("modelo_email", "")
                if modelo:
                    resposta += f"\n\n📧 <strong>Modelo de email sugerido:</strong><br><pre>{modelo}</pre>"
                return resposta

        return "❓ Não foi possível encontrar uma resposta adequada na base de conhecimento."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {str(e)}"
