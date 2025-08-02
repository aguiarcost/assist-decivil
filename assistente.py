import json
import os
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Variáveis de ambiente
openai.api_key = os.getenv("OPENAI_API_KEY")
PASSWORD = os.getenv("APP_PASSWORD", "decivil2024")

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_EMBEDDINGS = "base_knowledge_vector.json"

# === Funções utilitárias ===

def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def guardar_base_conhecimento(base):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

def gerar_embedding(texto):
    try:
        resposta = openai.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return resposta.data[0].embedding
    except Exception as e:
        print(f"Erro a gerar embedding para: {texto}")
        raise e

def atualizar_embeddings():
    base = carregar_base_conhecimento()
    vetor = []
    for item in base:
        try:
            embedding = gerar_embedding(item["pergunta"])
            vetor.append({
                "pergunta": item["pergunta"],
                "embedding": embedding,
                "resposta": item.get("resposta", ""),
                "email": item.get("email", ""),
                "modelo_email": item.get("modelo_email", "")
            })
        except Exception as e:
            print(f"Erro ao gerar embedding: {e}")
    with open(CAMINHO_EMBEDDINGS, "w", encoding="utf-8") as f:
        json.dump(vetor, f, ensure_ascii=False, indent=2)

# === Adicionar ou editar pergunta ===

def adicionar_ou_editar_pergunta(pergunta, resposta, email, modelo_email, password):
    if password != PASSWORD:
        return False, "❌ Password incorreta."

    base = carregar_base_conhecimento()
    todas = {p["pergunta"]: p for p in base}
    todas[pergunta] = {
        "pergunta": pergunta,
        "resposta": resposta,
        "email": email,
        "modelo_email": modelo_email
    }
    guardar_base_conhecimento(list(todas.values()))
    atualizar_embeddings()
    return True, "✅ Pergunta adicionada ou atualizada com sucesso."

# === Gerar resposta ===

def gerar_resposta(pergunta_utilizador, threshold=0.8):
    try:
        base = carregar_base_conhecimento()
        vetor = []

        if os.path.exists(CAMINHO_EMBEDDINGS):
            with open(CAMINHO_EMBEDDINGS, "r", encoding="utf-8") as f:
                try:
                    vetor = json.load(f)
                except json.JSONDecodeError:
                    return "⚠️ Erro ao carregar embeddings."
        else:
            return "⚠️ Embeddings não encontrados. Adicione perguntas para começar."

        perguntas = [item["pergunta"] for item in vetor]
        embeddings = np.array([item["embedding"] for item in vetor])
        embedding_utilizador = np.array(gerar_embedding(pergunta_utilizador)).reshape(1, -1)

        sims = cosine_similarity(embedding_utilizador, embeddings)[0]
        idx_max = int(np.argmax(sims))
        sim_max = sims[idx_max]

        if sim_max < threshold:
            return "🤔 Não foi encontrada uma resposta suficientemente relevante."

        item = vetor[idx_max]
        resposta = item["resposta"]
        if item.get("email"):
            resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
        if item.get("modelo_email"):
            resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"
        return resposta

    except Exception as e:
        return f"❌ Erro a gerar resposta: {str(e)}"
