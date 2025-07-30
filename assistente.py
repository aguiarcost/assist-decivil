import json  
import os  
import numpy as np  
from sentence_transformers import SentenceTransformer

# Carregamento do modelo de linguagem para embeddings (adiado até primeira utilização)
model = None
def get_model():
    """Carrega (ou retorna) o modelo de linguagem para geração de embeddings."""
    global model
    if model is None:
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return model

def gerar_base_vetorial(base_docs):
    """
    Gera o ficheiro base_knowledge_vector.json com os vetores de embeddings para cada pergunta da base de conhecimento.
    """
    model = get_model()
    perguntas = [item['pergunta'] for item in base_docs]
    # Gerar embeddings para todas as perguntas da base
    embeddings = model.encode(perguntas)
    # Converter para listas Python (para serialização JSON)
    embeddings_list = embeddings.tolist() if hasattr(embeddings, 'tolist') else list(embeddings)
    vetor_data = []
    for item, emb in zip(base_docs, embeddings_list):
        vetor_data.append({
            "pergunta": item['pergunta'],
            "embedding": emb
        })
    # Salvar os vetores em JSON
    with open('base_knowledge_vector.json', 'w', encoding='utf-8') as f:
        json.dump(vetor_data, f, ensure_ascii=False, indent=2)
    return True

def gerar_resposta(pergunta):
    """
    Retorna o registro da base de conhecimento correspondente à `pergunta`.
    Se não houver correspondência exata, usa a busca vetorial para encontrar a resposta mais relevante.
    """
    # Carregar base de conhecimento
    try:
        with open('base_conhecimento.json', 'r', encoding='utf-8') as f:
            base_docs = json.load(f)
    except Exception:
        base_docs = []
    # 1. Verificar correspondência exata (ignorando diferenças de espaços e maiúsculas/minúsculas)
    for item in base_docs:
        if item['pergunta'].strip().lower() == pergunta.strip().lower():
            return item  # retorna o dicionário com pergunta, resposta, etc.
    # 2. Se não encontrada, realizar busca vetorial (memória semântica)
    if not base_docs:
        # Base vazia ou não carregada corretamente
        return {
            "pergunta": pergunta,
            "resposta": "Desculpe, não encontrei informação sobre essa pergunta.",
            "email": "",
            "modelo_email": ""
        }
    # Certificar que os vetores estão disponíveis (gerar se ficheiro não existe)
    if not os.path.exists('base_knowledge_vector.json'):
        gerar_base_vetorial(base_docs)
    try:
        with open('base_knowledge_vector.json', 'r', encoding='utf-8') as f:
            base_vector_data = json.load(f)
    except Exception:
        base_vector_data = []
    if not base_vector_data:
        # Não foi possível carregar vetores (ou arquivo vazio)
        return {
            "pergunta": pergunta,
            "resposta": "Desculpe, não encontrei informação sobre essa pergunta.",
            "email": "",
            "modelo_email": ""
        }
    # Gerar embedding da pergunta fornecida
    model = get_model()
    query_emb = model.encode([pergunta])[0]
    # Calcular similaridade coseno entre o embedding da pergunta e os embeddings da base
    embeddings_matrix = np.array([entry['embedding'] for entry in base_vector_data])
    # Normalizar os vetores para cálculo de similaridade
    base_norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
    base_norms[base_norms == 0] = 1e-9  # evitar divisão por zero
    base_normalized = embeddings_matrix / base_norms
    query_norm = np.linalg.norm(query_emb)
    if query_norm == 0:
        query_norm = 1e-9
    query_normalized = query_emb / query_norm
    # Calcular pontuação de similaridade (produto interno, já que todos estão normalizados)
    sims = np.dot(base_normalized, query_normalized)
    best_idx = int(np.argmax(sims))
    # Recuperar a entrada correspondente ao melhor índice encontrado
    if 0 <= best_idx < len(base_docs):
        melhor_item = base_docs[best_idx]
        return melhor_item
    else:
        # Caso de segurança: tentar localizar pelo texto da pergunta no vetor (se índices divergirem)
        if 0 <= best_idx < len(base_vector_data):
            pergunta_encontrada = base_vector_data[best_idx].get('pergunta')
            if pergunta_encontrada:
                for item in base_docs:
                    if item['pergunta'] == pergunta_encontrada:
                        return item
        # Se nada for encontrado, retornar mensagem de não localizado
        return {
            "pergunta": pergunta,
            "resposta": "Desculpe, não encontrei informação sobre essa pergunta.",
            "email": "",
            "modelo_email": ""
        }
