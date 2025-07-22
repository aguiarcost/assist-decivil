import fitz  # PyMuPDF para PDF
import docx
import os
import json
import openai
import requests
from bs4 import BeautifulSoup
import time  # Para sleep em reintentos
import streamlit as st  # Para st.session_state

# Inicializar base_documents_vector em st.session_state
if 'base_documents_vector' not in st.session_state:
    st.session_state.base_documents_vector = []

# Obter chave da API
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Gerar embedding com reintentos e timeout
def gerar_embedding(texto, tentativas=5):
    if not openai.api_key:
        raise RuntimeError("Chave API OpenAI não definida.")
    for tentativa in range(tentativas):
        try:
            print(f"Tentativa {tentativa + 1} de gerar embedding para bloco de texto (tamanho: {len(texto)} chars)...")
            response = openai.embeddings.create(
                input=texto,
                model="text-embedding-3-small",
                timeout=30  # Timeout de 30 segundos por chamada
            )
            return response.data[0].embedding
        except openai.APITimeoutError:
            print(f"Timeout na tentativa {tentativa + 1}.")
            if tentativa < tentativas - 1:
                time.sleep(5)  # Espera mais longa após timeout
        except Exception as e:
            print(f"Erro na tentativa {tentativa + 1}: {e}")
            if tentativa < tentativas - 1:
                time.sleep(2 ** tentativa)  # Backoff exponencial
    raise RuntimeError(f"Falha ao gerar embedding após {tentativas} tentativas.")

# Guardar bloco com embedding em st.session_state
def guardar_embedding(origem, pagina, texto, embedding):
    base = st.session_state.base_documents_vector
    base.append({
        "origem": origem,
        "pagina": pagina,
        "texto": texto,
        "embedding": embedding
    })
    st.session_state.base_documents_vector = base  # Atualiza a session_state
    print(f"✅ Bloco salvo em session_state: {origem}, página {pagina}")

# Extrair texto com limpeza de encoding
def extrair_texto(file_or_url):
    try:
        if isinstance(file_or_url, str) and file_or_url.startswith("http"):
            texto = extrair_texto_website(file_or_url)
            origem = file_or_url
        else:
            nome = file_or_url.name.lower() if hasattr(file_or_url, 'name') else os.path.basename(file_or_url).lower()
            if nome.endswith(".pdf"):
                texto = extrair_texto_pdf(file_or_url)
                origem = nome
            elif nome.endswith(".docx"):
                texto = extrair_texto_docx(file_or_url)
                origem = nome
            elif nome.endswith(".txt"):
                texto = extrair_texto_txt(file_or_url)
                origem = nome
            else:
                raise ValueError(f"Tipo de ficheiro não suportado: {nome}")
        
        # Limpeza de encoding: Substitui bytes inválidos para UTF-8
        texto = texto.encode('utf-8', 'replace').decode('utf-8')
        print(f"Texto extraído e limpo de {origem}: {len(texto)} caracteres")
        return texto, origem
    except Exception as e:
        print(f"Erro ao extrair texto de {origem if 'origem' in locals() else file_or_url}: {e}")
        raise

def extrair_texto_pdf(file):
    texto = ""
    stream = file if isinstance(file, bytes) else file.read()
    try:
        with fitz.open(stream=stream, filetype="pdf") as doc:
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if not page_text.strip():
                    print(f"Aviso: Página {page_num + 1} de {os.path.basename(file.name if hasattr(file, 'name') else file)} está vazia.")
                texto += page_text
    except Exception as e:
        raise RuntimeError(f"Erro ao processar PDF: {e}")
    return texto

def extrair_texto_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extrair_texto_txt(file):
    return file.read().decode("utf-8", errors='replace')

def extrair_texto_website(url):
    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()  # Levanta erro para códigos HTTP inválidos
        soup = BeautifulSoup(resposta.content, "html.parser")
        textos = soup.stripped_strings
        return "\n".join(textos)
    except Exception as e:
        raise RuntimeError(f"Erro ao acessar URL {url}: {e}")

# Processar documento
def processar_documento(file_or_url):
    texto, origem = extrair_texto(file_or_url)
    blocos = [texto[i:i+1000] for i in range(0, len(texto), 1000)]
    print(f"Número de blocos gerados para {origem}: {len(blocos)}")

    salvos = 0
    for i, bloco in enumerate(blocos):
        if bloco.strip():
            try:
                print(f"Processando bloco {i + 1}/{len(blocos)}...")
                embedding = gerar_embedding(bloco)
                guardar_embedding(origem, i + 1, bloco, embedding)
                salvos += 1
            except Exception as e:
                print(f"Erro ao processar bloco {i + 1}: {e}")
        else:
            print(f"Bloco {i + 1} vazio; ignorado.")

    if salvos == 0:
        raise RuntimeError(f"Nenhum bloco salvo para {origem}. Verifique texto extraído.")
    return salvos  # Retorne o número de salvos para verificação em app.py


import json

# Guardar vetor de documentos no final do processamento
with open("base_documents_vector.json", "w", encoding="utf-8") as f:
    json.dump(st.session_state.base_documents_vector, f, ensure_ascii=False, indent=2)
