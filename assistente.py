import openai
import os
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Carregar chave API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Caminhos unificados
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"
CAMINHO_DOCUMENTS_VECTOR = "base_documents_vector.json"

# Carregar dados
def carregar_dados():
    # Base de conhecimento (Q&A)
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            knowledge_base = json.load(f)
    else:
        knowledge_base = []
    
    # Embeddings da base de conhecimento
    if os.path.exists(CAMINHO_KNOWLEDGE_VECTOR):
        with open(CAMINHO_KNOWLEDGE_VECTOR, "r", encoding="utf-8") as f:
            knowledge_data = json.load(f)
    else:
        knowledge_data = []
    
    knowledge_embeddings = np.array([item["embedding"] for item in knowledge_data]) if knowledge_data else np.array([])
    knowledge_perguntas = [item["pergunta"] for item in knowledge_data]
    
    # Documentos (chunks)
    if os.path.exists(CAMINHO_DOCUMENTS_VECTOR):
        with open(CAMINHO_DOCUMENTS_VECTOR, "r", encoding="utf-8") as f:
            documents_data = json.load(f)
    else:
        documents_data = []
    
    documents_embeddings = np.array([item["embedding"] for item in documents_data]) if documents_data else np.array([])
    
    return knowledge_base, knowledge_data, knowledge_perguntas, knowledge_embeddings, documents_data, documents_embeddings

knowledge_base, knowledge_data, knowledge_perguntas, knowledge_embeddings, documents_data, documents_embeddings = carregar_dados()

# Gerar embedding
def get_embedding(text):
    response = openai.embeddings.create(model="text-embedding-3-small", input=text)
    return np.array(response.data[0].embedding).reshape(1, -1)

# Gerar resposta
def gerar_resposta(pergunta_utilizador, use_documents=True, threshold=0.8):
    try:
        # Verificar correspondência exata na base de conhecimento (para dropdown)
        for item in knowledge_base:
            if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                modelo = item.get("modelo_email", "")
                if modelo:
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
                return resposta + "\n\n(Fonte: Base de conhecimento, correspondência exata)"
        
        # Se não houver correspondência exata, usar busca por similaridade
        embedding_utilizador = get_embedding(pergunta_utilizador)
        
        # Busca na base de conhecimento
        if len(knowledge_embeddings) > 0:
            sims_knowledge = cosine_similarity(embedding_utilizador, knowledge_embeddings)[0]
            max_sim_k = np.max(sims_knowledge)
            if max_sim_k >= threshold:
                idx = int(np.argmax(sims_knowledge))
                item = knowledge_data[idx]
                resposta = item["resposta"]
                if item.get("email"):
                    resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
                modelo = item.get("modelo_email", "")
                if modelo:
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
                return resposta + f"\n\n(Fonte: Base de conhecimento, similaridade: {max_sim_k:.2f})"
        
        # Se não encontrou ou similaridade baixa, usa RAG nos documentos
        if use_documents and len(documents_embeddings) > 0:
            sims_docs = cosine_similarity(embedding_utilizador, documents_embeddings)[0]
            top_indices = np.argsort(sims_docs)[-3:][::-1]  # Top 3 chunks
            context = ""
            sources = []
            for idx in top_indices:
                if sims_docs[idx] > 0.7:  # Threshold para relevância
                    item = documents_data[idx]
                    context += f"\n\n---\n{item['texto']}"
                    sources.append(f"{item['origem']}, página {item['pagina']}")
            
            if context:
                # Prompt para GPT
                prompt = f"Baseado no contexto seguinte, responde à pergunta: {pergunta_utilizador}\n\nContexto:{context}\n\nResposta:"
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300
                )
                generated = response.choices[0].message.content.strip()
                return generated + f"\n\n(Fonte: Documentos processados - {', '.join(sources)})"
        
        return "❓ Não foi possível encontrar uma resposta adequada na base de conhecimento ou documentos."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {str(e)}"
