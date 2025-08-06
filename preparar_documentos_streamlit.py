import streamlit as st
import json
from openai import OpenAI

# Inicializar cliente OpenAI com chave de API do secrets.toml
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Carregar os dados do JSON
try:
    with open('base_conhecimento.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
except FileNotFoundError:
    st.error("Ficheiro 'base_conhecimento.json' não encontrado!")
    st.stop()

# Função para gerar embeddings
def generate_embedding(text):
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        st.error(f"Erro ao gerar embedding: {str(e)}")
        return None

# Gerar embeddings para cada pergunta
for item in data:
    embedding = generate_embedding(item['pergunta'])
    if embedding:
        item['embedding'] = embedding

# Salvar os dados com embeddings em um novo arquivo JSON
try:
    with open('base_knowledge_vector.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    st.success("Embeddings gerados e salvos com sucesso!")
except Exception as e:
    st.error(f"Erro ao salvar ficheiro: {str(e)}")
