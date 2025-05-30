import os
import json
from PyPDF2 import PdfReader
import openai

# Lê a chave da API (streamlit secrets ou variável de ambiente)
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Diretório com PDFs
diretorio = "documentos"
ficheiro_saida = "base_docs_vectorizada.json"

# Função para extrair texto de um PDF, página a página
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

# Recolher todos os textos
todos_blocos = []
for ficheiro in os.listdir(diretorio):
    if ficheiro.endswith(".pdf"):
        caminho = os.path.join(diretorio, ficheiro)
        blocos = extrair_blocos_pdf(caminho)
        todos_blocos.extend(blocos)

# Gerar embeddings e guardar
base = []
for bloco in todos_blocos:
    try:
        resposta = openai.embeddings.create(
            input=bloco["texto"],
            model="text-embedding-3-small"
        )
        embedding = resposta.data[0].embedding
        base.append({
            "origem": bloco["origem"],
            "pagina": bloco["pagina"],
            "texto": bloco["texto"],
            "embedding": embedding
        })
    except Exception as e:
        print(f"Erro ao gerar embedding para página {bloco['pagina']} de {bloco['origem']}: {e}")

# Guardar base
with open(ficheiro_saida, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"✅ {len(base)} blocos processados e guardados em {ficheiro_saida}")
