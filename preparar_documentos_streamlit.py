import os
import json
import fitz            # PyMuPDF
import docx            # python-docx
import requests
from bs4 import BeautifulSoup
import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

CAMINHO_DOCS = "base_docs_vectorizada.json"

# ---------- Utils ----------
def _ler_json(caminho, default):
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def _escrever_json(caminho, conteudo):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)

def _get_openai_client():
    if OpenAI is None:
        return None
    api_key = None
    try:
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def _embedding(texto):
    client = _get_openai_client()
    if not client:
        return None
    try:
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return resp.data[0].embedding
    except Exception:
        return None

# ---------- Extração de texto ----------
def _texto_pdf(file_bytes):
    texto = ""
    with fitz.open(stream=file_bytes.read(), filetype="pdf") as doc:
        for i, page in enumerate(doc):
            texto += f"\n[__PAGINA__={i+1}]\n" + page.get_text()
    return texto

def _texto_docx(file_obj):
    d = docx.Document(file_obj)
    return "\n".join(p.text for p in d.paragraphs)

def _texto_txt(file_obj):
    return file_obj.read().decode("utf-8", errors="ignore")

def _texto_url(url):
    r = requests.get(url, timeout=20)
    soup = BeautifulSoup(r.content, "html.parser")
    # remove scripts/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    textos = list(soup.stripped_strings)
    return "\n".join(textos)

# ---------- Processador ----------
def processar_documento(file_or_url):
    """
    Recebe:
      - ficheiro carregado via Streamlit (PDF/DOCX/TXT)
      - ou URL (string começada por http)
    Gera chunks + embeddings e guarda em base_docs_vectorizada.json
    """
    if isinstance(file_or_url, str) and file_or_url.startswith("http"):
        origem = file_or_url
        texto = _texto_url(file_or_url)
    else:
        nome = file_or_url.name.lower()
        origem = nome
        if nome.endswith(".pdf"):
            texto = _texto_pdf(file_or_url)
        elif nome.endswith(".docx"):
            texto = _texto_docx(file_or_url)
        elif nome.endswith(".txt"):
            texto = _texto_txt(file_or_url)
        else:
            raise ValueError("Formato não suportado. Use .pdf, .docx, .txt ou URL.")

    # chunking simples
    chunks = []
    pagina_atual = None
    buf = []
    for linha in texto.splitlines():
        if linha.startswith("[__PAGINA__="):
            # fecha chunk anterior
            if buf:
                chunks.append(("\n".join(buf)).strip(),)
                buf = []
            try:
                pagina_atual = int(linha.split("=")[1].strip("]"))
            except Exception:
                pagina_atual = None
        else:
            buf.append(linha)
    if buf:
        chunks.append(("\n".join(buf)).strip(),)

    base = _ler_json(CAMINHO_DOCS, [])

    for c in chunks:
        if not c or not c[0].strip():
            continue
        conteudo = c[0]
        emb = _embedding(conteudo)
        item = {
            "origem": origem,
            "pagina": pagina_atual,
            "texto": conteudo,
            "embedding": emb
        }
        base.append(item)

    _escrever_json(CAMINHO_DOCS, base)
