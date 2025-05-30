import os
import fitz  # PyMuPDF
import openai
import json
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

def preparar_documentos():
    base = []
    for ficheiro in os.listdir("documentos"):
        if ficheiro.endswith(".pdf"):
            caminho = os.path.join("documentos", ficheiro)
            doc = fitz.open(caminho)
            for pagina_num in range(len(doc)):
                texto = doc.load_page(pagina_num).get_text().strip()
                if texto:
                    embedding = openai.embeddings.create(
                        input=texto,
                        model="text-embedding-3-small"
                    ).data[0].embedding
                    base.append({
                        "origem": ficheiro,
                        "pagina": pagina_num + 1,
                        "texto": texto,
                        "embedding": embedding
                    })
    with open("base_docs_vectorizada.json", "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)
    return len(base)
