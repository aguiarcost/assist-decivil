import json
import os
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Inicializar chave da OpenAI (usa st.secrets ou variável ambiente no Streamlit Cloud)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Função para carregar dados de conhecimento e documentos
def carregar_dados():
    with open("base_knowledge_vector.json", "r", encoding="utf-8") as f:
        knowledge_data = json.load(f)

    knowledge_perguntas = [item.get("pergunta", "") for item in knowledge_data if "pergunta" in item]
    knowledge_embeddings = np.array([item["embedding"] for item in knowledge_data if "embedding" in item])

    documents_data = []
    documents_embeddings = []
    if os.path.exists("base_documents_vector.json"):
        with open("base_documents_vector.json", "r", encoding="utf-8") as f:
            documents_data = json.load(f)
            documents_embeddings = np.array([item["embedding"] for item in documents_data if "embedding" in item])

    return knowledge_data, knowledge_data, knowledge_perguntas, knowledge_embeddings, documents_data, documents_embeddings

# Função para gerar embedding de um texto
def gerar_embedding(texto):
    try:
        response = openai.embeddings.create(
            input=texto,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        return None

# Função principal para gerar resposta
def gerar_resposta(pergunta, knowledge_data, knowledge_perguntas, knowledge_embeddings, documents_data, documents_embeddings):
    pergunta_embedding = gerar_embedding(pergunta)
    if pergunta_embedding is None:
        return "Erro ao gerar embedding da pergunta. Verifique a chave da OpenAI."

    pergunta_embedding_np = np.array(pergunta_embedding).reshape(1, -1)

    melhores_resultados = []

    if knowledge_embeddings.size > 0:
        similaridades_knowledge = cosine_similarity(pergunta_embedding_np, knowledge_embeddings)[0]
        idx_max = int(np.argmax(similaridades_knowledge))
        melhores_resultados.append((similaridades_knowledge[idx_max], knowledge_data[idx_max].get("resposta", "Resposta não disponível.")))

    if documents_embeddings != [] and len(documents_embeddings) > 0:
        documents_embeddings_np = np.array(documents_embeddings)
        similaridades_docs = cosine_similarity(pergunta_embedding_np, documents_embeddings_np)[0]
        idx_max_doc = int(np.argmax(similaridades_docs))
        melhores_resultados.append((similaridades_docs[idx_max_doc], documents_data[idx_max_doc].get("texto", "Texto não disponível.")))

    if not melhores_resultados:
        return "Não encontrei nenhuma resposta relevante."

    # Ordenar por similaridade (mais relevante primeiro)
    melhores_resultados.sort(key=lambda x: x[0], reverse=True)
    return melhores_resultados[0][1]

# Carregar os dados uma vez ao iniciar
knowledge_base, knowledge_data, knowledge_perguntas, knowledge_embeddings, documents_data, documents_embeddings = carregar_dados()
