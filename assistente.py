# assistente.py
import os
import json
from uuid import uuid4
import streamlit as st
from supabase import create_client

# --------- CONFIG SUPABASE ---------
def _sb_client():
    # Tenta secrets do Streamlit; se não houver, tenta variáveis de ambiente
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_SERVICE_KEY", ""))
    if not url or not key:
        raise RuntimeError("❌ SUPABASE_URL e/ou SUPABASE_SERVICE_KEY não estão definidos em secrets nem em variáveis de ambiente.")
    return create_client(url, key)

TABELA = "base_conhecimento"
ADMIN_PWD = "decivil2024"

# --------- LEITURA ---------
@st.cache_data(ttl=60)
def carregar_perguntas():
    sb = _sb_client()
    res = sb.table(TABELA).select("*").order("pergunta").execute()
    return res.data or []

def nomes_perguntas(perguntas):
    return [p["pergunta"] for p in perguntas]

def obter_por_pergunta(perguntas, pergunta):
    for p in perguntas:
        if p["pergunta"] == pergunta:
            return p
    return None

# --------- CRIAR ---------
def criar_pergunta(pergunta, resposta, email, modelo_email):
    sb = _sb_client()
    novo = {
        "id": str(uuid4()),
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip(),
        "email": (email or "").strip(),
        "modelo_email": (modelo_email or "").strip(),
    }
    sb.table(TABELA).insert(novo).execute()
    limpar_cache()
    return novo

# --------- ATUALIZAR ---------
def atualizar_pergunta(reg_id, pergunta, resposta, email, modelo_email):
    sb = _sb_client()
    patch = {
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip(),
        "email": (email or "").strip(),
        "modelo_email": (modelo_email or "").strip(),
    }
    sb.table(TABELA).update(patch).eq("id", reg_id).execute()
    limpar_cache()

# --------- APAGAR ---------
def apagar_pergunta(reg_id):
    sb = _sb_client()
    sb.table(TABELA).delete().eq("id", reg_id).execute()
    limpar_cache()

# --------- DOWNLOAD / UPLOAD ---------
def exportar_base_json():
    # devolve bytes para st.download_button
    data = carregar_perguntas()
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

def importar_base_json(arquivo_bytes):
    sb = _sb_client()
    try:
        conteudo = json.loads(arquivo_bytes.decode("utf-8"))
        if not isinstance(conteudo, list):
            raise ValueError("O ficheiro JSON deve conter uma lista de objetos.")
        # Normaliza campos esperados; gera id quando faltar
        normalizados = []
        for item in conteudo:
            normalizados.append({
                "id": item.get("id", str(uuid4())),
                "pergunta": item.get("pergunta", "").strip(),
                "resposta": item.get("resposta", "").strip(),
                "email": (item.get("email") or "").strip(),
                "modelo_email": (item.get("modelo_email") or "").strip(),
            })
        # Estratégia simples: upsert por id
        for bloco in normalizados:
            sb.table(TABELA).upsert(bloco, on_conflict="id").execute()
        limpar_cache()
        return len(normalizados)
    except json.JSONDecodeError:
        raise ValueError("JSON inválido. Verifica o ficheiro.")

# --------- UTIL ---------
def limpar_cache():
    try:
        st.cache_data.clear()
    except Exception:
        pass

def validar_admin(pwd: str) -> bool:
    return (pwd or "").strip() == ADMIN_PWD
