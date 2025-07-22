import fitz  # PyMuPDF para PDF
import docx
import os
import json
import openai
import requests
from bs4 import BeautifulSoup
import time  # Para sleep em reintentos

# Caminho da base vetorizada para documentos
CAMINHO_BASE = "base_documents_vector.json"

# Obter chave da API
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Inicializar o arquivo JSON se não existir
if not os.path.exists(CAMINHO_BASE):
    with open(CAMINHO_BASE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    print(f"✅ Arquivo {CAMINHO_BASE} criado vazio.")

# Gerar embedding com reintentos
def gerar_embedding(texto, tentativas=3):
    if not openai.api_key:
        raise RuntimeError("Chave API OpenAI não definida.")
    for tentativa in range(tentativas):
        try:
            print(f"Tentativa {tentativa + 1} de gerar embedding para bloco de texto (tamanho: {len(texto)} chars)...")
            response = openai.embeddings.create(
                input=texto,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Erro na tentativa {tentativa + 1}: {e}")
            if tentativa < tentativas - 1:
                time.sleep(2 ** tentativa)  # Backoff exponencial
    raise RuntimeError(f"Falha ao gerar embedding após {tentativas} tentativas.")

# Guardar bloco com embedding
def guardar_embedding(origem, pagina, texto, embedding):
    try:
        if os.path.exists(CAMINHO_BASE):
            with open(CAMINHO_BASE, "r", encoding="utf-8") as f:
                base = json.load(f)
        else:
            base = []
    except json.JSONDecodeError:
        print("Arquivo JSON corrompido; reiniciando como vazio.")
        base = []

    base.append({
        "origem": origem,
        "pagina": pagina,
        "texto": texto,
        "embedding": embedding
    })

    try:
        with open(CAMINHO_BASE, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=2)
        print(f"✅ Bloco salvo: {origem}, página {pagina}")
    except Exception as e:
        print(f"Erro ao salvar JSON: {e}")
        raise

# Extrair texto (sem mudanças, mas adicione log)
def extrair_texto(file_or_url):
    # ... (código original)
    texto, origem = ...  # Supondo o código original
    print(f"Texto extraído de {origem}: {len(texto)} caracteres")
    return texto, origem

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
