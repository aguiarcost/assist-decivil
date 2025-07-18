import json
import os
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Caminho para a base de conhecimento
CAMINHO_CONHECIMENTO = "base_conhecimento.json"

# Carregar base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Gerar embeddings usando OpenAI
def gerar_embedding(texto):
    try:
        resposta = openai.Embedding.create(
            input=texto,
            model="text-embedding-ada-002"
        )
        return resposta["data"][0]["embedding"]
    except Exception as e:
        return None

# Função principal: gerar resposta
def gerar_resposta(pergunta_usuario):
    base = carregar_base_conhecimento()
    if not base or not pergunta_usuario.strip():
        return "❌ Não foi possível carregar a base de conhecimento ou a pergunta está vazia."

    embedding_pergunta = gerar_embedding(pergunta_usuario)
    if embedding_pergunta is None:
        return "❌ Erro ao gerar embedding para a pergunta."

    melhores_resultados = []

    for entrada in base:
        entrada_pergunta = entrada.get("pergunta", "")
        entrada_resposta = entrada.get("resposta", "")

        if not entrada_pergunta or not entrada_resposta:
            continue

        embedding_base = gerar_embedding(entrada_pergunta)
        if embedding_base:
            score = cosine_similarity(
                [embedding_pergunta], [embedding_base]
            )[0][0]
            melhores_resultados.append((score, entrada))

    if not melhores_resultados:
        return "❌ Nenhuma correspondência encontrada na base de conhecimento."

    melhores_resultados.sort(reverse=True, key=lambda x: x[0])
    melhor_score, melhor = melhores_resultados[0]

    if melhor_score < 0.70:
        return f"❌ Nenhuma resposta suficientemente próxima encontrada (score: {melhor_score:.2f})"

    resposta = melhor.get("resposta", "").strip()
    extras = []

    if melhor.get("modelo"):
        extras.append(f"📧 **Modelo de email sugerido:**\n\n{melhor['modelo'].strip()}")

    if melhor.get("email"):
        extras.append(f"📨 **Email de contacto:** {melhor['email'].strip()}")

    if not resposta:
        return "⚠️ A pergunta foi reconhecida, mas não tem resposta definida."

    return resposta + ("\n\n---\n\n" + "\n\n".join(extras) if extras else "")
