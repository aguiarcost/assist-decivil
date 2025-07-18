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

def gerar_resposta(pergunta):
    base = carregar_base_conhecimento()
    perguntas = [item["pergunta"] for item in base]
    respostas = [item["resposta"] for item in base]

    if not perguntas:
        return "Ainda não tenho conhecimento suficiente para responder."

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(perguntas + [pergunta])
    similaridades = cosine_similarity(X[-1], X[:-1])
    indice_mais_similar = similaridades.argmax()

    resposta_base = respostas[indice_mais_similar]
    extra = ""

    entrada_escolhida = base[indice_mais_similar]
    if entrada_escolhida.get("modelo"):
        extra += f"\n\n📧 **Modelo de email sugerido:**\n{entrada_escolhida['modelo']}"
    elif entrada_escolhida.get("email"):
        extra += f"\n\n📬 **Email de contacto:** {entrada_escolhida['email']}"

    return resposta_base + extra
