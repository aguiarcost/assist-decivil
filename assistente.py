import json
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

CAMINHO_BASE = "base_conhecimento.json"

def carregar_base():
    if os.path.exists(CAMINHO_BASE):
        with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def gerar_resposta(pergunta_utilizador):
    base = carregar_base()
    perguntas = [item["pergunta"] for item in base]
    
    if not perguntas:
        return "❌ Base de conhecimento vazia."

    # Vetorização
    vect = TfidfVectorizer().fit_transform(perguntas + [pergunta_utilizador])
    similaridades = cosine_similarity(vect[-1], vect[:-1]).flatten()

    idx_mais_proximo = similaridades.argmax()
    melhor_match = base[idx_mais_proximo]

    resposta = melhor_match.get("resposta", "❌ Sem resposta definida.")
    email = melhor_match.get("email", "")
    modelo = melhor_match.get("modelo_email", "")

    resposta_final = f"{resposta}"

    if email:
        resposta_final += f"\n\n📧 **Email de contacto:** {email}"
    if modelo:
        resposta_final += f"\n\n📄 **Modelo de email sugerido:**\n```\n{modelo}\n```"

    return resposta_final
