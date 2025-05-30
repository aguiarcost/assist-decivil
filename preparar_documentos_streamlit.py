import fitz  # PyMuPDF
import docx
import requests
from bs4 import BeautifulSoup
import json
import numpy as np
import openai
import os

CAMINHO_BASE = "base_docs_vectorizada.json"

# Carregar base existente ou iniciar vazia
def carregar_base():
    if os.path.exists(CAMINHO_BASE):
        with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Guardar base atualizada
def guardar_base(base):
    with open(CAMINHO_BASE, "w", encoding="utf-8") as f:
        json.dump(base, f, indent=2, ensure_ascii=False)

# Extrair texto do PDF
def extrair_texto_pdf(uploaded_file):
    texto = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            texto += page.get_text()
    return texto

# Extrair texto de ficheiro Word
def extrair_texto_docx(uploaded_file):
    texto = ""
    doc = docx.Document(uploaded_file)
    for para in doc.paragraphs:
        texto += para.text + "\n"
    return texto

# Extrair texto de ficheiro TXT
def extrair_texto_txt(uploaded_file):
    return uploaded_file.read().decode("utf-8")

# Extrair texto de URL
def extrair_texto_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text()

# Gerar embeddings em blocos
def gerar_blocos_e_embeddings(texto, tamanho=500):
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    blocos = [texto[i:i+tamanho] for i in range(0, len(texto), tamanho)]
    resultado = []
    for bloco in blocos:
        if len(bloco.strip()) < 10:
            continue
        embedding = openai.embeddings.create(
            input=bloco,
            model="text-embedding-3-small"
        ).data[0].embedding
        resultado.append({"texto": bloco, "embedding": embedding})
    return resultado

# Função principal
def processar_documento(uploaded_file, tipo="ficheiro"):
    if tipo == "ficheiro":
        nome = uploaded_file.name
        if nome.endswith(".pdf"):
            texto = extrair_texto_pdf(uploaded_file)
        elif nome.endswith(".docx"):
            texto = extrair_texto_docx(uploaded_file)
        elif nome.endswith(".txt"):
            texto = extrair_texto_txt(uploaded_file)
        else:
            raise ValueError("Formato de ficheiro não suportado.")
    elif tipo == "url":
        texto = extrair_texto_url(uploaded_file)
    else:
        raise ValueError("Tipo de origem desconhecido.")

    base = carregar_base()
    novos_blocos = gerar_blocos_e_embeddings(texto)
    base.extend(novos_blocos)
    guardar_base(base)
