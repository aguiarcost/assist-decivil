import json
import openai
from tqdm import tqdm

openai.api_key = "A_TUA_CHAVE_AQUI"  # OU usa `st.secrets["OPENAI_API_KEY"]` se quiseres adaptar

def gerar_embedding(texto):
    response = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

# Carregar base original
with open("base_conhecimento.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

base_vectorizada = []
for entrada in tqdm(dados):
    texto = entrada.get("texto", "")
    embedding = gerar_embedding(texto)
    base_vectorizada.append({
        "texto": texto,
        "embedding": embedding
    })

with open("base_vectorizada.json", "w", encoding="utf-8") as f:
    json.dump(base_vectorizada, f, ensure_ascii=False, indent=2)

print("✅ Embeddings gerados com sucesso.")
