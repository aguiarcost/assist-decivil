import json
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_KNOWLEDGE_VECTOR = "base_knowledge_vector.json"

def gerar_embedding(texto):
    response = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def main():
    if not os.path.exists(CAMINHO_CONHECIMENTO):
        print("⚠️ Ficheiro base_conhecimento.json não encontrado.")
        return

    with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
        conhecimento = json.load(f)

    vetor = []
    for item in conhecimento:
        pergunta = item.get("pergunta", "").strip()
        resposta = item.get("resposta", "").strip()
        email = item.get("email", "").strip()
        modelo_email = item.get("modelo_email", "").strip()
        if pergunta:
            embedding = gerar_embedding(pergunta)
            vetor.append({
                "pergunta": pergunta,
                "resposta": resposta,
                "email": email,
                "modelo_email": modelo_email,
                "embedding": embedding
            })

    with open(CAMINHO_KNOWLEDGE_VECTOR, "w", encoding="utf-8") as f:
        json.dump(vetor, f, ensure_ascii=False, indent=2)

    print(f"✅ Gerado {len(vetor)} embeddings para a base de conhecimento.")

if __name__ == "__main__":
    main()
