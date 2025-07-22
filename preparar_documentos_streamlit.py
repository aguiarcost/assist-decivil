import fitz  # PyMuPDF para PDF
import docx
import os
import json
import openai
import requests
from bs4 import BeautifulSoup

# Caminho da base vetorizada para documentos
CAMINHO_BASE = "base_documents_vector.json"

# Obter chave da API
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Gerar embedding
def gerar_embedding(texto):
    try:
        response = openai.embeddings.create(
            input=texto,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"Erro ao gerar embedding: {e}")

# Guardar bloco com embedding
def guardar_embedding(origem, pagina, texto, embedding):
    if os.path.exists(CAMINHO_BASE):
        try:
            with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
                base = json.load(f)
        except json.JSONDecodeError:
            base = []
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

# Extrair texto
def extrair_texto(file_or_url):
    if isinstance(file_or_url, str) and file_or_url.startswith("http"):
        return extrair_texto_website(file_or_url), file_or_url

    nome = file_or_url.name.lower() if hasattr(file_or_url, 'name') else os.path.basename(file_or_url).lower()
    if nome.endswith(".pdf"):
        return extrair_texto_pdf(file_or_url), nome
    elif nome.endswith(".docx"):
        return extrair_texto_docx(file_or_url), nome
    elif nome.endswith(".txt"):
        return extrair_texto_txt(file_or_url), nome
    else:
        raise ValueError("Tipo de ficheiro não suportado.")

def extrair_texto_pdf(file):
    texto = ""
    stream = file if isinstance(file, bytes) else file.read()
    with fitz.open(stream=stream, filetype="pdf") as doc:
        for page in doc:
            texto += page.get_text()
    return texto

def extrair_texto_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extrair_texto_txt(file):
    return file.read().decode("utf-8")

def extrair_texto_website(url):
    resposta = requests.get(url, timeout=10)
    soup = BeautifulSoup(resposta.content, "html.parser")
    textos = soup.stripped_strings
    return "\n".join(textos)

# Processar documento
def processar_documento(file_or_url):
    texto, origem = extrair_texto(file_or_url)
    blocos = [texto[i:i+1000] for i in range(0, len(texto), 1000)]

    for i, bloco in enumerate(blocos):
        if bloco.strip():
            embedding = gerar_embedding(bloco)
            guardar_embedding(origem, i + 1, bloco, embedding)
