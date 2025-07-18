import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

def carregar_base():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def gerar_resposta(pergunta):
    base = carregar_base()
    if not base:
        return "⚠️ Base de conhecimento vazia."

    perguntas = [p["pergunta"] for p in base]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(perguntas + [pergunta])

    cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    melhor_indice = cosine_similarities.argmax()
    similaridade = cosine_similarities[0, melhor_indice]

    if similaridade < 0.4:
        return "❌ Pergunta não encontrada na base de conhecimento."

    item = base[melhor_indice]
    resposta = item.get("resposta", "").strip()
    modelo = item.get("modelo", "").strip()

    if not resposta:
        return "⚠️ Esta entrada não contém uma resposta válida."

    if modelo:
        resposta += f"\n\n<details><summary>📧 Modelo de email sugerido</summary>\n\n```\n{modelo}\n```\n</details>"

    return resposta
