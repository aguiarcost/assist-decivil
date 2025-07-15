import fitz  # PyMuPDF para PDFs
import docx  # Para .docx
import os
import json
import openai
import requests
from bs4 import BeautifulSoup

# Caminho da base vetorizada
CAMINHO_BASE = "base_vectorizada.json"

# Obter chave da API (ambiente)
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Função: gerar embedding de texto
def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

# Função: guardar texto + embedding na base
def guardar_embedding(origem, pagina, texto, embedding):
    if os.path.exists(CAMINHO_BASE):
        with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
            base = json.load(f)
    else:
        base = []

    base.append({
        "origem": origem,
        "pagina": pagina,
        "texto": texto,
        "embedding": embedding
    })

    with open(CAMINHO_BASE, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

# Função: extrair texto conforme o tipo de input
def extrair_texto(file):
    if isinstance(file, str) and file.startswith("http"):
        return extrair_texto_website(file), file, 0
    nome = file.name.lower()
    if nome.endswith(".pdf"):
        return extrair_texto_pdf(file)
    elif nome.endswith(".docx"):
        return extrair_texto_docx(file), nome, 0
    elif nome.endswith(".txt"):
        return file.read().decode("utf-8"), nome, 0
    else:
        raise ValueError("Tipo de ficheiro não suportado.")

def extrair_texto_pdf(file):
    texto_total = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for i, page in enumerate(doc):
            texto_total += page.get_text()
    return texto_total, file.name, 0

def extrair_texto_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extrair_texto_website(url):
    resposta = requests.get(url)
    soup = BeautifulSoup(resposta.content, "html.parser")
    return "\n".join(soup.stripped_strings)

# Função principal para processar documento
def processar_documento(file_or_url):
    texto, origem, pagina_base = extrair_texto(file_or_url)

    blocos = [texto[i:i+1000] for i in range(0, len(texto), 1000)]

    for i, bloco in enumerate(blocos):
        if bloco.strip():
            embedding = gerar_embedding(bloco)
            guardar_embedding(origem, pagina_base + i + 1, bloco, embedding)
