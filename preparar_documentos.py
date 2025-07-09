import os
import json
from PyPDF2 import PdfReader
import openai

# Lê a chave da API (ambiente ou ficheiro de configuração)
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Diretório de entrada e saída
DIRETORIO_DOCUMENTOS = "documentos"
CAMINHO_BASE = "base_docs_vectorizada.json"

# Função para extrair texto por página de um PDF

def extrair_blocos_pdf(caminho):
    reader = PdfReader(caminho)
    blocos = []
    for i, pagina in enumerate(reader.pages):
        texto = pagina.extract_text()
        if texto:
            blocos.append({
                "origem": os.path.basename(caminho),
                "pagina": i + 1,
                "texto": texto.strip()
            })
    return blocos

# Função para gerar embeddings com verificação

def gerar_embedding(texto):
    try:
        resposta = openai.embeddings.create(
            input=texto,
            model="text-embedding-3-small"
        )
        return resposta.data[0].embedding
    except Exception as e:
        print(f"Erro a gerar embedding: {e}")
        return None

# Função principal para processar documentos do diretório

def processar_documentos():
    todos_blocos = []
    for ficheiro in os.listdir(DIRETORIO_DOCUMENTOS):
        if ficheiro.endswith(".pdf"):
            caminho = os.path.join(DIRETORIO_DOCUMENTOS, ficheiro)
            blocos = extrair_blocos_pdf(caminho)
            todos_blocos.extend(blocos)

    base = []
    for bloco in todos_blocos:
        embedding = gerar_embedding(bloco["texto"])
        if embedding:
            base.append({
                "origem": bloco["origem"],
                "pagina": bloco["pagina"],
                "texto": bloco["texto"],
                "embedding": embedding
            })

    with open(CAMINHO_BASE, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(base)} blocos guardados em {CAMINHO_BASE}")

# Execução direta

if __name__ == "__main__":
    processar_documentos()
