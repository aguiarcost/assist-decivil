import openai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Caminhos
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Chave da API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Carregar base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except json.JSONDecodeError:
            return []
    return []

# Guardar base de conhecimento
def guardar_base_conhecimento(base):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

# Gerar embedding
def get_embedding(texto):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return np.array(response.data[0].embedding)

# Gerar todos os embeddings e guardar
def gerar_embeddings():
    base = carregar_base_conhecimento()
    vetores = []
    for item in base:
        try:
            emb = get_embedding(item["pergunta"]).tolist()
            vetores.append({
                "pergunta": item["pergunta"],
                "embedding": emb,
                "resposta": item.get("resposta", ""),
                "email": item.get("email", ""),
                "modelo_email": item.get("modelo_email", "")
            })
        except Exception as e:
            print(f"❌ Erro a gerar embedding para: {item['pergunta']}\n{e}")
    with open(CAMINHO_KNOWLEDGE_VECTOR, "w", encoding="utf-8") as f:
        json.dump(vetores, f, ensure_ascii=False, indent=2)

# Gerar resposta à pergunta
def gerar_resposta(pergunta_utilizador, threshold=0.8):
    try:
        base = carregar_base_conhecimento()
        if not base:
            return "❗ Base de conhecimento vazia."

        # Correspondência exata
        for item in base:
            if item["pergunta"].strip().lower() == pergunta_utilizador.strip().lower():
                resposta = item.get("resposta", "")
                email = item.get("email", "")
                modelo = item.get("modelo_email", "")
                if email:
                    resposta += f"\n\n📫 **Email de contacto:** {email}"
                if modelo:
                    resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
                return resposta

        # Busca por similaridade
        if not os.path.exists(CAMINHO_KNOWLEDGE_VECTOR):
            return "❗ Não foram encontrados embeddings. Atualize a base de conhecimento."

        with open(CAMINHO_KNOWLEDGE_VECTOR, "r", encoding="utf-8") as f:
            knowledge_data = json.load(f)

        embeddings = np.array([item["embedding"] for item in knowledge_data])
        perguntas = [item["pergunta"] for item in knowledge_data]
        respostas = knowledge_data

        emb_user = get_embedding(pergunta_utilizador).reshape(1, -1)
        sims = cosine_similarity(emb_user, embeddings)[0]
        idx_max = int(np.argmax(sims))

        if sims[idx_max] >= threshold:
            item = respostas[idx_max]
            resposta = item.get("resposta", "")
            email = item.get("email", "")
            modelo = item.get("modelo_email", "")
            if email:
                resposta += f"\n\n📫 **Email de contacto:** {email}"
            if modelo:
                resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
            return resposta
        else:
            return "❓ Não encontrei resposta relevante na base de conhecimento."

    except Exception as e:
        return f"❌ Erro ao gerar resposta: {e}"
