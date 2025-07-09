import fitz  # PyMuPDF para PDF
import docx  # para .docx
import os
import json
import numpy as np
import openai
import streamlit as st
import requests
from bs4 import BeautifulSoup

# Obter chave da API
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    st.error("🔐 A chave da API da OpenAI não está definida nos segredos. Por favor, adicione OPENAI_API_KEY ao ficheiro secrets.toml.")

CAMINHO_BASE = "base_docs_vectorizada.json"

# Função auxiliar: gerar embedding
def gerar_embedding(texto):
    response = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

# Função auxiliar: guardar texto e embedding
def guardar_embedding(texto, embedding, origem="upload", pagina="?"):
    if os.path.exists(CAMINHO_BASE):
        try:
            with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
                base = json.load(f)
        except json.JSONDecodeError:
            base = []
    else:
        base = []

    base.append({"origem": origem, "pagina": pagina, "texto": texto, "embedding": embedding})
    with open(CAMINHO_BASE, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

# Funções de extração de texto
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

# Função principal para processar e guardar documento
def processar_documentos(file_or_url):
    try:
        texto = extrair_texto(file_or_url)
    except Exception as e:
        st.error(f"Erro ao extrair texto: {e}")
        return

    blocos = [texto[i:i+1000] for i in range(0, len(texto), 1000)]

    for bloco in blocos:
        if bloco.strip():
            try:
                embedding = gerar_embedding(bloco)
                guardar_embedding(bloco, embedding)
            except Exception as e:
                st.warning(f"Erro ao gerar embedding para bloco: {e}")
