import json
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

# Carregar base de conhecimento
def carregar_base():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Gerar resposta com similaridade
def gerar_resposta(pergunta):
    base = carregar_base()
    if not base:
        return "⚠️ A base de conhecimento está vazia ou inacessível."

    perguntas = [item["pergunta"] for item in base]
    vectorizer = TfidfVectorizer().fit_transform(perguntas + [pergunta])
    cosine_sim = cosine_similarity(vectorizer[-1], vectorizer[:-1]).flatten()

    if max(cosine_sim) < 0.3:
        return "🤔 Não encontrei uma resposta adequada na base de conhecimento."

    idx = cosine_sim.argmax()
    item = base[idx]

    resposta = f"{item['resposta']}".strip()

    if item.get("modelo"):
        resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo'].strip()}\n```"

    if item.get("email"):
        resposta += f"\n\n📮 Para mais informações: `{item['email'].strip()}`"

    return resposta
