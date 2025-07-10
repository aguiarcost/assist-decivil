import os
import json
import fitz  # PyMuPDF para PDFs
import docx
import requests
from bs4 import BeautifulSoup
import openai

# Definir caminho da base vetorizada
CAMINHO_BASE = "base_vectorizada.json"

# Obter chave da API
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Função para gerar embeddings
def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

# Guardar texto com embedding
def guardar_embedding(texto, embedding, origem="Desconhecido"):
    if os.path.exists(CAMINHO_BASE):
        with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
            base = json.load(f)
    else:
        base = []

    base.append({"texto": texto, "embedding": embedding, "origem": origem})
    with open(CAMINHO_BASE, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

# Extrair texto de PDF
def extrair_texto_pdf(file):
    texto = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            texto += page.get_text()
    return texto

# Extrair texto de DOCX
def extrair_texto_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

# Extrair texto de TXT
def extrair_texto_txt(file):
    return file.read().decode("utf-8")

# Extrair texto de um website
def extrair_texto_website(url):
    try:
        resposta = requests.get(url)
        soup = BeautifulSoup(resposta.content, "html.parser")
        textos = soup.stripped_strings
        return "\n".join(textos)
    except:
        return ""

# Função para processar qualquer tipo de entrada
def processar_documento(file_or_url):
    if isinstance(file_or_url, str) and file_or_url.startswith("http"):
        texto = extrair_texto_website(file_or_url)
        origem = file_or_url
    else:
        nome = file_or_url.name.lower()
        if nome.endswith(".pdf"):
            texto = extrair_texto_pdf(file_or_url)
        elif nome.endswith(".docx"):
            texto = extrair_texto_docx(file_or_url)
        elif nome.endswith(".txt"):
            texto = extrair_texto_txt(file_or_url)
        else:
            raise ValueError("Tipo de ficheiro não suportado.")
        origem = nome

    # Dividir em blocos de 1000 caracteres
    blocos = [texto[i:i+1000] for i in range(0, len(texto), 1000)]
    for bloco in blocos:
        if bloco.strip():
            embedding = gerar_embedding(bloco)
            guardar_embedding(bloco, embedding, origem=origem)
