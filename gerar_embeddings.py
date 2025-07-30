import json
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_SAIDA = "base_knowledge_vector.json"

def gerar_embedding(texto):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return response.data[0].embedding

def main():
    if not os.path.exists(CAMINHO_CONHECIMENTO):
        print("Ficheiro base_conhecimento.json não encontrado.")
        return

    with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
        conhecimento = json.load(f)

    vetor_conhecimento = []
    for item in conhecimento:
        pergunta = item.get("pergunta", "").strip()
        if pergunta:
            embedding = gerar_embedding(pergunta)
            vetor_conhecimento.append({
                "pergunta": pergunta,
                "resposta": item.get("resposta", ""),
                "email": item.get("email", ""),
                "modelo_email": item.get("modelo_email", ""),
                "embedding": embedding
            })

    with open(CAMINHO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(vetor_conhecimento, f, ensure_ascii=False, indent=2)

    print("✅ base_knowledge_vector.json gerado com sucesso.")

if __name__ == "__main__":
    main()
