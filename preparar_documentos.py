import os
import json
from PyPDF2 import PdfReader
import openai

# API key da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "")
if not openai.api_key:
    raise ValueError("❌ API key não definida. Usa a variável de ambiente OPENAI_API_KEY.")

# Diretório com PDFs
diretorio = "documentos"
ficheiro_saida = "base_docs_vectorizada.json"

# Verifica se o diretório existe
if not os.path.exists(diretorio):
    raise FileNotFoundError(f"❌ Diretório '{diretorio}' não encontrado.")

# Função para extrair blocos de texto
def extrair_blocos_pdf(caminho):
    reader = PdfReader(caminho)
    blocos = []
    for i, pagina in enumerate(reader.pages):
        texto = pagina.extract_text()
        if texto:
            texto_limpo = texto.strip()
            # Dividir em blocos de até 1000 caracteres
            blocos.extend([{
                "origem": os.path.basename(caminho),
                "pagina": i + 1,
                "texto": texto_limpo[j:j+1000]
            } for j in range(0, len(texto_limpo), 1000)])
    return blocos

# Recolher blocos
todos_blocos = []
for ficheiro in os.listdir(diretorio):
    if ficheiro.endswith(".pdf"):
        caminho = os.path.join(diretorio, ficheiro)
        print(f"📄 A processar: {ficheiro}")
        blocos = extrair_blocos_pdf(caminho)
        todos_blocos.extend(blocos)

# Gerar embeddings
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
        print(f"⚠️ Erro ao gerar embedding para {bloco['origem']} p{bloco['pagina']}: {e}")

# Guardar JSON
with open(ficheiro_saida, "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)

print(f"✅ {len(base)} blocos processados e guardados em {ficheiro_saida}")
