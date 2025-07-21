import json
import openai

# 🔑 Coloca aqui a tua chave da OpenAI
openai.api_key = "COLA_AQUI_A_TUA_CHAVE"

# 📄 Lê a base de conhecimento original
with open("base_conhecimento.json", "r", encoding="utf-8") as f:
    base = json.load(f)

# 🔁 Adiciona embeddings a cada pergunta
nova_base = []
for entrada in base:
    pergunta = entrada.get("pergunta")
    if pergunta:
        resposta = openai.embeddings.create(
            input=pergunta,
            model="text-embedding-3-small"
        )
        embedding = resposta.data[0].embedding
        entrada["embedding"] = embedding
        nova_base.append(entrada)

# 💾 Guarda novo ficheiro com embeddings
with open("base_conhecimento_com_embeddings.json", "w", encoding="utf-8") as f:
    json.dump(nova_base, f, ensure_ascii=False, indent=2)

print("✅ Embeddings criados com sucesso.")
