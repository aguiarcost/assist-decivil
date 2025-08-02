import os
import json
import numpy as np
import openai
from sklearn.metrics.pairwise import cosine_similarity

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

# Password de edição
PASSWORD_CORRETA = os.getenv("APP_EDIT_PASSWORD", "decivil2024")

# Chave da API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Carrega base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Guarda nova base de conhecimento
def guardar_base_conhecimento(base):
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

# Gerar embedding com OpenAI
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

# Atualiza o ficheiro de embeddings
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

# Adiciona ou edita uma pergunta (com password obrigatória)
def adicionar_ou_editar_pergunta(pergunta, resposta, email, modelo_email, password):
    if password != PASSWORD_CORRETA:
        return False, "❌ Password incorreta. Alterações não foram guardadas."

    base = carregar_base_conhecimento()
    # Atualizar ou adicionar
    perguntas_dict = {p["pergunta"]: p for p in base}
    perguntas_dict[pergunta] = {
        "pergunta": pergunta,
        "resposta": resposta,
        "email": email,
        "modelo_email": modelo_email
    }
    nova_base = list(perguntas_dict.values())
    guardar_base_conhecimento(nova_base)
    atualizar_embeddings()
    return True, "✅ Pergunta guardada com sucesso."

# Gerar resposta à pergunta do utilizador
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
        
