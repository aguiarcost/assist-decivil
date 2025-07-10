import os
import json
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Carregar chave da API
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_BASE_DOCS = "base_vectorizada.json"

# Carregar base de conhecimento
def carregar_base_conhecimento():
    try:
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# Carregar base vetorizada de documentos
def carregar_base_docs():
    try:
        with open(CAMINHO_BASE_DOCS, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# Gerar embedding
def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

# Encontrar blocos relevantes por similaridade
def procurar_blocos_relevantes(embedding, base_docs, top_n=3):
    docs_embeddings = np.array([bloco["embedding"] for bloco in base_docs])
    pergunta_vector = np.array(embedding).reshape(1, -1)
    similaridades = cosine_similarity(pergunta_vector, docs_embeddings)[0]
    indices_top = np.argsort(similaridades)[-top_n:][::-1]
    blocos_relevantes = []
    for idx in indices_top:
        blocos_relevantes.append({
            "texto": base_docs[idx]["texto"],
            "origem": base_docs[idx].get("origem", "Desconhecida"),
            "similaridade": float(similaridades[idx])
        })
    return blocos_relevantes

# Função principal
def gerar_resposta(pergunta):
    pergunta_lower = pergunta.lower()
    base_conhecimento = carregar_base_conhecimento()

    # Verificação por correspondência exata
    for entrada in base_conhecimento:
        if entrada["pergunta"].lower().strip() == pergunta_lower.strip():
            resposta = entrada["resposta"]
            email = entrada.get("email", "")
            modelo_email = entrada.get("modelo_email", "")

            resposta_final = f"**💬 Resposta:** {resposta}"
            if email:
                resposta_final += f"\n\n**📧 Contacto:** [{email}](mailto:{email})"
            if modelo_email:
                resposta_final += f"\n\n**✉️ Modelo de email sugerido:**\n```\n{modelo_email}\n```"
            return resposta_final

    # Se não existir na base de conhecimento, procurar nos documentos
    base_docs = carregar_base_docs()
    if not base_docs:
        return "⚠️ A base de documentos ainda não foi carregada ou está vazia."

    embedding = gerar_embedding(pergunta)
    blocos = procurar_blocos_relevantes(embedding, base_docs, top_n=3)

    if not blocos:
        return "❌ Não encontrei resposta à sua pergunta nos documentos disponíveis."

    resposta = "🔎 A sua pergunta não consta na base de conhecimento, mas encontrei conteúdos semelhantes:\n\n"
    for bloco in blocos:
        resposta += f"- **Fonte:** {bloco['origem']} | **Similaridade:** {bloco['similaridade']:.2f}\n"
        resposta += f"> {bloco['texto'][:500].strip()}...\n\n"
    return resposta
