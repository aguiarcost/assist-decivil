import json
import os
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

CAMINHO_BASE = "base_vectorizada.json"
CAMINHO_CONHECIMENTO = "base_conhecimento.json"

# Carregar embeddings dos documentos
def carregar_base_docs():
    if os.path.exists(CAMINHO_BASE):
        try:
            with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Carregar base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Gerar resposta
def gerar_resposta(pergunta):
    # 1. Procurar correspondência exata na base de conhecimento
    base_conhecimento = carregar_base_conhecimento()
    for item in base_conhecimento:
        if pergunta.strip().lower() == item["pergunta"].strip().lower():
            resposta = item["resposta"]
            complemento = ""
            if item.get("email"):
                complemento += f"\n\n📬 **Contacto sugerido:** `{item['email']}`"
            if item.get("modelo"):
                complemento += f"\n\n✉️ **Modelo de email:**\n```\n{item['modelo']}\n```"
            return resposta + complemento

    # 2. Procurar nos documentos com embeddings
    base_docs = carregar_base_docs()
    if not base_docs:
        return "❌ Nenhuma base de documentos está carregada para ajudar com esta pergunta."

    try:
        resposta_embedding = openai.embeddings.create(
            input=pergunta,
            model="text-embedding-3-small"
        )
        pergunta_vector = resposta_embedding.data[0].embedding
    except Exception as e:
        return f"❌ Erro ao gerar embedding da pergunta: {e}"

    docs_vetorizados = [doc["embedding"] for doc in base_docs]
    similares = cosine_similarity([pergunta_vector], docs_vetorizados)[0]

    top_indices = np.argsort(similares)[::-1][:3]
    blocos_relevantes = [base_docs[i] for i in top_indices if similares[i] > 0.75]

    if not blocos_relevantes:
        return "🤔 Não encontrei uma resposta exata. Por favor reformule a pergunta ou tente com outro termo."

    contexto = "\n\n".join(
        f"(Fonte: {b['origem']}, página {b['pagina']})\n{b['texto']}" for b in blocos_relevantes
    )

    prompt = f"""A seguir está um conjunto de excertos de documentos. Usa apenas essas informações para responder à pergunta.
    
### Documentos
{contexto}

### Pergunta
{pergunta}

### Resposta
"""

    try:
        resposta_modelo = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "És um assistente administrativo objetivo e útil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return resposta_modelo.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Erro ao gerar resposta com o modelo: {e}"
