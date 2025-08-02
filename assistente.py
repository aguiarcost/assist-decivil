import os
import json
import numpy as np
import openai
from sklearn.metrics.pairwise import cosine_similarity

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Chave da API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Carregar base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Guardar base de conhecimento
def guardar_base_conhecimento(nova_pergunta):
    base = carregar_base_conhecimento()
    todas = {p["pergunta"]: p for p in base}
    todas[nova_pergunta["pergunta"]] = nova_pergunta
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
    atualizar_embeddings()

# Obter embedding
def get_embedding(texto):
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Erro a gerar embedding: {e}")
        return None

# Atualizar embeddings após nova pergunta
def atualizar_embeddings():
    base = carregar_base_conhecimento()
    dados = []
    for item in base:
        embedding = get_embedding(item["pergunta"])
        if embedding:
            dados.append({
                "pergunta": item["pergunta"],
                "resposta": item["resposta"],
                "email": item.get("email", ""),
                "modelo_email": item.get("modelo_email", ""),
                "embedding": embedding
            })
    with open(CAMINHO_KNOWLEDGE_VECTOR, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

# Gerar resposta
def gerar_resposta(pergunta_utilizador, threshold=0.8):
    try:
        with open(CAMINHO_KNOWLEDGE_VECTOR, "r", encoding="utf-8") as f:
            data = json.load(f)
        embeddings = np.array([d["embedding"] for d in data])
        perguntas = [d["pergunta"] for d in data]

        emb_utilizador = get_embedding(pergunta_utilizador)
        if emb_utilizador is None:
            return "Erro ao gerar o embedding da pergunta."

        sims = cosine_similarity([emb_utilizador], embeddings)[0]
        idx = int(np.argmax(sims))
        if sims[idx] >= threshold:
            item = data[idx]
            resposta = item["resposta"]
            if item.get("email"):
                resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
            if item.get("modelo_email"):
                resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
            return resposta
        else:
            return "❓ Não foi possível encontrar uma resposta adequada."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {str(e)}"
