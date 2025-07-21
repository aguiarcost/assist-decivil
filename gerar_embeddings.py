import json
import os
import openai
from tqdm import tqdm

CAMINHO_BASE = "base_conhecimento.json"
CAMINHO_VETORIZADA = "base_vectorizada.json"

# Configurar chave da API (necessário definir OPENAI_API_KEY no ambiente)
if "OPENAI_API_KEY" in os.environ:
    openai.api_key = os.environ["OPENAI_API_KEY"]
else:
    raise RuntimeError("É necessário definir a variável de ambiente OPENAI_API_KEY com a chave da API OpenAI.")

def gerar_embedding(texto):
    try:
        resp = openai.Embedding.create(input=texto, model="text-embedding-ada-002")
        return resp["data"][0]["embedding"]
    except Exception as e:
        print(f"Erro ao gerar embedding para: {texto}\n{e}")
        return None

# Carregar base de conhecimento
if not os.path.exists(CAMINHO_BASE):
    raise FileNotFoundError(f"Não foi encontrado o ficheiro {CAMINHO_BASE}.")
with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
    base_conhecimento = json.load(f)

# Gerar embeddings para todas as perguntas na base de conhecimento
lista_embeddings = []
for item in tqdm(base_conhecimento, desc="Gerando embeddings"):
    pergunta = item.get("pergunta")
    if pergunta:
        emb = gerar_embedding(pergunta)
        if emb:
            lista_embeddings.append({"pergunta": pergunta, "embedding": emb})

# Guardar resultados no ficheiro JSON vetorizado
with open(CAMINHO_VETORIZADA, "w", encoding="utf-8") as f:
    json.dump(lista_embeddings, f, ensure_ascii=False, indent=2)
print(f"✅ Embeddings gerados e guardados em {CAMINHO_VETORIZADA}")
