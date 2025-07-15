import os
import json
from PyPDF2 import PdfReader
import openai

# Caminho para o diretório com PDFs e o ficheiro de saída
DIRETORIO_DOCUMENTOS = "documentos"
FICHEIRO_SAIDA = "base_vectorizada.json"

# Chave da API (ambiente)
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Extrair blocos de texto de PDF (página a página)
def extrair_blocos_pdf(caminho_pdf):
    reader = PdfReader(caminho_pdf)
    blocos = []
    for i, pagina in enumerate(reader.pages):
        texto = pagina.extract_text()
        if texto:
            blocos.append({
                "origem": os.path.basename(caminho_pdf),
                "pagina": i + 1,
                "texto": texto.strip()
            })
    return blocos

# Recolher blocos de todos os PDFs no diretório
def recolher_blocos():
    todos_blocos = []
    for ficheiro in os.listdir(DIRETORIO_DOCUMENTOS):
        if ficheiro.endswith(".pdf"):
            caminho = os.path.join(DIRETORIO_DOCUMENTOS, ficheiro)
            blocos = extrair_blocos_pdf(caminho)
            todos_blocos.extend(blocos)
    return todos_blocos

# Gerar embedding e guardar
def gerar_base_vectorizada():
    blocos = recolher_blocos()
    base = []

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
            print(f"❌ Erro ao gerar embedding para {bloco['origem']} (página {bloco['pagina']}): {e}")

    with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(base)} blocos processados e guardados em {FICHEIRO_SAIDA}")

if __name__ == "__main__":
    gerar_base_vectorizada()
