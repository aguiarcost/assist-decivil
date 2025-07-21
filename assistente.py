import json
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def gerar_resposta(pergunta_usuario):
    base_conhecimento = carregar_base_conhecimento()
    if not base_conhecimento:
        return "⚠️ A base de conhecimento está vazia."

    perguntas = [item["pergunta"] for item in base_conhecimento]
    
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(perguntas + [pergunta_usuario])
    
    similaridades = cosine_similarity(X[-1], X[:-1]).flatten()
    indice_mais_similar = similaridades.argmax()

    if similaridades[indice_mais_similar] < 0.2:
        return "🤔 Desculpe, não encontrei uma resposta adequada para essa pergunta."

    item = base_conhecimento[indice_mais_similar]
    resposta = item.get("resposta", "").strip()
    modelo = item.get("modelo_email", "").strip()

    if not resposta:
        return "❌ Esta pergunta não tem uma resposta definida."

    if modelo:
        return f"**Resposta:**\n{resposta}\n\n---\n\n**✉️ Modelo de Email:**\n```\n{modelo}\n```"
    else:
        return f"**Resposta:**\n{resposta}"
