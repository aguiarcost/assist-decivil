import json
from openai import OpenAI

CAMINHO_BASE = "base_conhecimento.json"
CAMINHO_VETORES = "base_vectorizada.json"

client = OpenAI(api_key="INSERE_AQUI_A_SUA_API_KEY_TEMPORARIAMENTE")

def gerar_embedding(pergunta):
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=pergunta
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Erro ao gerar embedding para: {pergunta}\n{e}")
        return None

with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
    conhecimento = json.load(f)

dados = []
for entrada in conhecimento:
    pergunta = entrada["pergunta"]
    embedding = gerar_embedding(pergunta)
    if embedding:
        dados.append({"pergunta": pergunta, "embedding": embedding})

with open(CAMINHO_VETORES, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

print("✅ Embeddings gerados e guardados com sucesso.")
