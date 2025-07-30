import json
import os
import numpy as np
import openai
from gerar_embeddings import main as generate_embeddings

# Modelo de embedding OpenAI
EMBEDDING_MODEL = "text-embedding-3-small"

def gerar_resposta(pergunta):
    """
    Retorna o registro da base de conhecimento correspondente à `pergunta`.
    Se não houver correspondência exata, usa a busca vetorial para encontrar a resposta mais relevante.
    """
    # Carregar base de conhecimento do ficheiro
    try:
        with open('base_conhecimento.json', 'r', encoding='utf-8') as f:
            base_docs = json.load(f)
    except Exception:
        base_docs = []
    # 1. Verificar correspondência exata (ignorando espaços e maiúsculas/minúsculas)
    for item in base_docs:
        if item['pergunta'].strip().lower() == pergunta.strip().lower():
            return item  # retorna o dicionário completo (pergunta, resposta, etc.)
    # 2. Se não encontrada resposta exata, realizar busca vetorial (semântica)
    if not base_docs:
        # Base de conhecimento vazia ou não carregada corretamente
        return {
            "pergunta": pergunta,
            "resposta": "Desculpe, não encontrei informação sobre essa pergunta.",
            "email": "",
            "modelo_email": ""
        }
    # Garantir que os vetores de embeddings estão disponíveis (gerar se ficheiro não existe)
    if not os.path.exists('base_knowledge_vector.json'):
        generate_embeddings()
    try:
        with open('base_knowledge_vector.json', 'r', encoding='utf-8') as f:
            base_vector_data = json.load(f)
    except Exception:
        base_vector_data = []
    if not base_vector_data:
        # Não foi possível carregar os vetores (ou arquivo vazio)
        return {
            "pergunta": pergunta,
            "resposta": "Desculpe, não encontrei informação sobre essa pergunta.",
            "email": "",
            "modelo_email": ""
        }
    # Usar modelo de embedding OpenAI para a pergunta do usuário
    try:
        response = openai.Embedding.create(model=EMBEDDING_MODEL, input=[pergunta])
        query_emb = response['data'][0]['embedding']
    except Exception as e:
        return {
            "pergunta": pergunta,
            "resposta": "Desculpe, não encontrei informação sobre essa pergunta.",
            "email": "",
            "modelo_email": ""
        }
    # Calcular similaridades coseno entre o embedding da pergunta e os embeddings da base
    embeddings_matrix = np.array([entry['embedding'] for entry in base_vector_data])
    base_norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
    base_norms[base_norms == 0] = 1e-9  # evitar divisão por zero
    base_normalized = embeddings_matrix / base_norms
    query_norm = np.linalg.norm(query_emb)
    if query_norm == 0:
        query_norm = 1e-9
    query_normalized = np.array(query_emb) / query_norm
    sims = np.dot(base_normalized, query_normalized)
    best_idx = int(np.argmax(sims))
    # Recuperar a entrada correspondente ao índice com maior similaridade
    if 0 <= best_idx < len(base_docs):
        melhor_item = base_docs[best_idx]
        return melhor_item
    else:
        # Caso de segurança: tentar localizar pelo texto da pergunta no vetor, se índices estiverem desalinhados
        if 0 <= best_idx < len(base_vector_data):
            pergunta_encontrada = base_vector_data[best_idx].get('pergunta')
            if pergunta_encontrada:
                for item in base_docs:
                    if item['pergunta'] == pergunta_encontrada:
                        return item
        # Se nada for encontrado, retornar mensagem padrão de não localizado
        return {
            "pergunta": pergunta,
            "resposta": "Desculpe, não encontrei informação sobre essa pergunta.",
            "email": "",
            "modelo_email": ""
        }
