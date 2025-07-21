import json
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

def carregar_base():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def gerar_resposta(pergunta):
    base = carregar_base()
    if not base:
        return "⚠️ Base de conhecimento vazia."

    perguntas = [item["pergunta"] for item in base]
    respostas = [item["resposta"] for item in base]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(perguntas)
    pergunta_vec = vectorizer.transform([pergunta])
    similaridades = cosine_similarity(pergunta_vec, tfidf_matrix).flatten()

    idx_mais_similar = similaridades.argmax()
    if similaridades[idx_mais_similar] < 0.3:
        return "🤷‍♂️ Desculpe, não encontrei uma resposta adequada."

    entrada = base[idx_mais_similar]
    resposta = f"{entrada['resposta']}"

    if entrada.get("email"):
        resposta += f"\n\n✉️ **Email de contacto sugerido:** `{entrada['email']}`"
    if entrada.get("modelo"):
        resposta += f"\n\n📄 **Modelo de email sugerido:**\n\n```\n{entrada['modelo']}\n```"

    return resposta
