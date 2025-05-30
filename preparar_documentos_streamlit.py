import fitz  # PyMuPDF
import openai
import json
import os
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Carrega base existente (se houver)
def carregar_base_existente():
    if os.path.exists("base_docs_vectorizada.json"):
        with open("base_docs_vectorizada.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Processa PDF carregado
def processar_pdf(uploaded_file):
    base = carregar_base_existente()
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    nome = uploaded_file.name

    for pagina_num in range(len(doc)):
        texto = doc.load_page(pagina_num).get_text().strip()
        if texto:
            embedding = openai.embeddings.create(
                input=texto,
                model="text-embedding-3-small"
            ).data[0].embedding
            base.append({
                "origem": nome,
                "pagina": pagina_num + 1,
                "texto": texto,
                "embedding": embedding
            })

    with open("base_docs_vectorizada.json", "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)
    
    return len(doc)
