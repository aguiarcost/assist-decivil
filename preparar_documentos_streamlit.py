import fitz  # PyMuPDF para PDF
import docx  # para .docx
import os
import json
import numpy as np
import openai
import streamlit as st
import requests
from bs4 import BeautifulSoup

# Chave da API
openai.api_key = st.secrets["OPENAI_API_KEY"]

CAMINHO_BASE = "base_docs_vectorizada.json"

def gerar_embedding(texto):
    response = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def guardar_embedding(texto, embedding):
    if os.path.exists(CAMINHO_BASE):
        with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
            base = json.load(f)
    else:
        base = []

    base.append({"texto": texto, "embedding": embedding})
    with open(CAMINHO_BASE, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

def extrair_texto(file):
    if isinstance(file, str) and file.startswith("http"):
        return extrair_texto_website(file)

    nome = file.name.lower()
    if nome.endswith(".pdf"):
        return extrair_texto_pdf(file)
    elif nome.endswith(".docx"):
        return extrair_texto_docx(file)
    elif nome.endswith(".txt"):
        return extrair_texto_txt(file)
    else:
        raise ValueError("Tipo de ficheiro não suportado.")

def extrair_texto_pdf(file):
    texto = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            texto += page.get_text()
    return texto

def extrair_texto_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extrair_texto_txt(file):
    return file.read().decode("utf-8")

def extrair_texto_website(url):
    resposta = requests.get(url)
    soup = BeautifulSoup(resposta.content, "html.parser")
    textos = soup.stripped_strings
    return "\n".join(textos)

# ✅ Função principal para múltiplos uploads ou links
def processar_documentos(file_or_url_list):
    if not isinstance(file_or_url_list, list):
        file_or_url_list = [file_or_url_list]

    for item in file_or_url_list:
        try:
            texto = extrair_texto(item)
            blocos = [texto[i:i+1000] for i in range(0, len(texto), 1000)]

            for bloco in blocos:
                if bloco.strip():
                    embedding = gerar_embedding(bloco)
                    guardar_embedding(bloco, embedding)

            if isinstance(item, str):
                st.success(f"✅ Conteúdo do website processado: {item}")
            else:
                st.success(f"✅ Ficheiro processado: {item.name}")

        except Exception as e:
            st.error(f"❌ Erro ao processar {item if isinstance(item, str) else item.name}: {e}")
