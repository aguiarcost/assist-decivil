import os
import json
from PyPDF2 import PdfReader
import openai

# Caminhos
DIRETORIO_DOCUMENTOS = "documentos"
FICHEIRO_SAIDA = "base_vectorizada.json"

# Chave da API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# Extrair texto em blocos de 1000 caracteres
def extrair_blocos_texto(texto, origem, pagina):
    texto = texto.strip()
    return [{
        "origem": origem,
        "pagina": pagina,
        "texto": texto[i:i+1000]
    } for i in range(0, len(texto), 1000)]

# Extrair blocos de texto de PDF
def extrair_blocos_pdf(caminho):
    reader = PdfReader(caminho)
    blocos = []
    for i, pagina in enumerate(reader.pages):
        texto = pagina.extract_text()
        if texto:
            blocos.extend(extrair_blocos_texto(texto, os.path.basename(caminho), i + 1))
    return blocos

# Processar diretório
def processar_diretorio():
    todos_blocos = []
    for ficheiro in os.listdir(DIRETORIO_DOCUMENTOS):
        if ficheiro.endswith(".pdf"):
            caminho = os.path.join(DIRETORIO_DOCUMENTOS, ficheiro)
            todos_blocos.extend(extrair_blocos_pdf(caminho))
    return todos_blocos

# Gerar embeddings
def gerar_embeddings(blocos):
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
            print(f"Erro no ficheiro {bloco['origem']} pág {bloco['pagina']}: {e}")
    return base

# Executar tudo
def main():
    blocos = processar_diretorio()
    print(f"📄 {len(blocos)} blocos de texto extraídos.")
    base = gerar_embeddings(blocos)
    with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(base)} blocos processados e guardados em '{FICHEIRO_SAIDA}'.")

if __name__ == "__main__":
    main()
