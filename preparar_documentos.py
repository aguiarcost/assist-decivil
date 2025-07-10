import os
import json
from PyPDF2 import PdfReader
import openai

# Caminho da base de dados vetorizada
CAMINHO_BASE = "base_vectorizada.json"
DIRETORIO = "documentos"  # Diretório onde estão os PDFs

# Chave da API
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Extrair texto de um PDF, página por página
def extrair_blocos_pdf(caminho):
    reader = PdfReader(caminho)
    blocos = []
    for i, pagina in enumerate(reader.pages):
        texto = pagina.extract_text()
        if texto:
            texto = texto.strip()
            sub_blocos = [texto[j:j+1000] for j in range(0, len(texto), 1000)]
            for sub_bloco in sub_blocos:
                blocos.append({
                    "origem": os.path.basename(caminho),
                    "pagina": i + 1,
                    "texto": sub_bloco
                })
    return blocos

# Processar todos os PDFs e gerar embeddings
base = []
for ficheiro in os.listdir(DIRETORIO):
    if ficheiro.endswith(".pdf"):
        caminho = os.path.join(DIRETORIO, ficheiro)
        blocos = extrair_blocos_pdf(caminho)
        for bloco in blocos:
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
                print(f"❌ Erro na página {bloco['pagina']} do ficheiro {bloco['origem']}: {e}")

# Guardar a base vetorizada
with open(CAMINHO_BASE, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"✅ {len(base)} blocos processados e guardados em {CAMINHO_BASE}")
