import openai
import json
import os
import time

# Carregar chave API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Caminhos
CAMINHO_BASE = "base_conhecimento.json"
CAMINHO_VETORES = "base_knowledge_vector.json"

# Modelo de embedding
EMBEDDING_MODEL = "text-embedding-3-small"

def gerar_embedding(texto, tentativas=3):
    for tentativa in range(tentativas):
        try:
            response = openai.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texto
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Erro ao gerar embedding para: {texto}\n\n{e}")
            time.sleep(2)
    return None

def main():
    if not os.path.exists(CAMINHO_BASE):
        print(f"⚠️ Ficheiro {CAMINHO_BASE} não encontrado.")
        return

    with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
        base_conhecimento = json.load(f)

    base_vectorizada = []

    for entrada in base_conhecimento:
        pergunta = entrada.get("pergunta", "")
        if pergunta:
            embedding = gerar_embedding(pergunta)
            if embedding:
                base_vectorizada.append({
                    "pergunta": pergunta,
                    "resposta": entrada.get("resposta", ""),
                    "email": entrada.get("email", ""),
                    "modelo_email": entrada.get("modelo_email", ""),
                    "embedding": embedding
                })

    with open(CAMINHO_VETORES, "w", encoding="utf-8") as f:
        json.dump(base_vectorizada, f, ensure_ascii=False, indent=2)

    print("✅ Embeddings gerados e guardados em base_knowledge_vector.json")

if __name__ == "__main__":
    main()
```

