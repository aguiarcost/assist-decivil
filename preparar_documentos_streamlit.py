import fitz  # PyMuPDF para PDF
import docx
import os
import json
import numpy as np
import openai
import requests
from bs4 import BeautifulSoup

# Caminho para a base vetorizada (embeddings)
CAMINHO_VETORIZADA = "base_vectorizada.json"

# Configurar chave da API OpenAI a partir do ambiente, se disponível
if not openai.api_key:
    api_key_env = os.getenv("OPENAI_API_KEY", "")
    if api_key_env:
        openai.api_key = api_key_env

def gerar_embedding(texto):
    """Gera o embedding para um determinado texto usando o modelo de embeddings da OpenAI."""
    try:
        response = openai.Embedding.create(input=texto, model="text-embedding-ada-002")
        return response["data"][0]["embedding"]
    except Exception as e:
        raise RuntimeError(f"Erro ao gerar embedding: {e}")

def guardar_embedding(origem, pagina, texto, embedding):
    """Guarda no ficheiro vetorizado um bloco de texto com o respetivo embedding."""
    if os.path.exists(CAMINHO_VETORIZADA):
        try:
            with open(CAMINHO_VETORIZADA, "r", encoding="utf-8") as f:
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
    with open(CAMINHO_VETORIZADA, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

def extrair_texto(file_or_url):
    """Extrai texto de um ficheiro (PDF, DOCX, TXT) ou de um URL fornecido."""
    if isinstance(file_or_url, str) and file_or_url.startswith("http"):
        return extrair_texto_website(file_or_url), file_or_url
    # Se for um ficheiro, identificar o tipo pelo nome
    nome = getattr(file_or_url, "name", "").lower()
    if nome.endswith(".pdf"):
        return extrair_texto_pdf(file_or_url), nome
    elif nome.endswith(".docx"):
        return extrair_texto_docx(file_or_url), nome
    elif nome.endswith(".txt"):
        return extrair_texto_txt(file_or_url), nome
    else:
        raise ValueError("Tipo de ficheiro não suportado.")

def extrair_texto_pdf(file):
    """Extrai todo o texto de um ficheiro PDF."""
    texto = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            texto += page.get_text()
    return texto

def extrair_texto_docx(file):
    """Extrai texto de um ficheiro Word (.docx)."""
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extrair_texto_txt(file):
    """Lê o conteúdo de um ficheiro de texto (.txt)."""
    return file.read().decode("utf-8")

def extrair_texto_website(url):
    """Faz scrape de um URL e extrai o texto visível da página HTML."""
    resposta = requests.get(url, timeout=10)
    soup = BeautifulSoup(resposta.content, "html.parser")
    textos = soup.stripped_strings
    return "\n".join(textos)

def processar_documento(file_or_url):
    """Processa um documento ou URL, extraindo o texto e guardando os seus embeddings por blocos."""
    texto, origem = extrair_texto(file_or_url)
    # Dividir o texto em blocos de tamanho manejável (por exemplo, 1000 caracteres)
    blocos = [texto[i:i+1000] for i in range(0, len(texto), 1000)]
    for i, bloco in enumerate(blocos, start=1):
        if bloco.strip():
            emb = gerar_embedding(bloco)
            guardar_embedding(origem, i, bloco, emb)
