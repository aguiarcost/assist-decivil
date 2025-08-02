import openai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# --- Caminhos ---
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_EMBEDDINGS = "base_knowledge_vector.json"

# --- API Key ---
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Função: Carregar base de conhecimento ---
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# --- Função: Guardar base de conhecimento ---
def guardar_base_conhecimento(nova_base):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(nova_base, f, ensure_ascii=False, indent=2)

# --- Função: Gerar embedding OpenAI ---
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

# --- Função: Gerar embedding de nova pergunta e atualizar ficheiro ---
def gerar_embedding(pergunta, resposta, email="", modelo_email=""):
    if not pergunta:
        return
    embedding = get_embedding(pergunta)
    if embedding is None:
        return
    nova_entrada = {
        "pergunta": pergunta,
        "embedding": embedding,
        "resposta": resposta,
        "email": email,
        "modelo_email": modelo_email
    }

    dados_existentes = []
    if os.path.exists(CAMINHO_EMBEDDINGS):
        try:
            with open(CAMINHO_EMBEDDINGS, "r", encoding="utf-8") as f:
                dados_existentes = json.load(f)
        except json.JSONDecodeError:
            pass

    # Remover duplicado da mesma pergunta
    dados_existentes = [d for d in dados_existentes if d["pergunta"] != pergunta]
    dados_existentes.append(nova_entrada)

    with open(CAMINHO_EMBEDDINGS, "w", encoding="utf-8") as f:
        json.dump(dados_existentes, f, ensure_ascii=False, indent=2)

# --- Função: Gerar resposta a partir da base ---
def gerar_resposta(pergunta_utilizador, threshold=0.8):
    try:
        with open(CAMINHO_EMBEDDINGS, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return "⚠️ Base de conhecimento ainda não tem embeddings."

    perguntas = [d["pergunta"] for d in data]
    embeddings = np.array([d["embedding"] for d in data])

    emb_utilizador = get_embedding(pergunta_utilizador)
    if emb_utilizador is None or len(embeddings) == 0:
        return "⚠️ Erro a gerar resposta."

    emb_utilizador = np.array(emb_utilizador).reshape(1, -1)
    sims = cosine_similarity(emb_utilizador, embeddings)[0]

    idx_mais_proximo = int(np.argmax(sims))
    if sims[idx_mais_proximo] < threshold:
        return "❓ Não encontrei uma resposta adequada na base de conhecimento."

    item = data[idx_mais_proximo]
    resposta = item["resposta"]

    # Apresentar email e modelo se existirem
    if item.get("email"):
        resposta += f"\n\n📫 **Email de contacto:** {item['email']}"
    if item.get("modelo_email"):
        resposta += f"\n\n📧 **Modelo de email sugerido:**\n```\n{item['modelo_email']}\n```"

    return resposta
