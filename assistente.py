import json
import streamlit as st
from typing import List, Dict, Any, Optional
from supabase import create_client, Client

# -----------------------------
# Config
# -----------------------------
TABELA = "base_conhecimento"
PASSWORD = "decivil2024"  # pedido do utilizador

# -----------------------------
# Supabase Client (singleton)
# -----------------------------
def _sb() -> Client:
    """Cria/recupera o cliente Supabase a partir dos secrets."""
    if "supabase_client" not in st.session_state:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL ou SUPABASE_SERVICE_KEY não definidos em .streamlit/secrets.toml")
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client

# -----------------------------
# Leitura
# -----------------------------
@st.cache_data(show_spinner=False, ttl=60)
def ler_base_conhecimento() -> List[Dict[str, Any]]:
    """Lê todas as perguntas ordenadas alfabeticamente."""
    sb = _sb()
    res = sb.table(TABELA).select("*").order("pergunta").execute()
    rows = res.data or []
    # normalizar chaves para garantir presença
    for r in rows:
        r.setdefault("email", "")
        r.setdefault("modelo_email", "")
        r.setdefault("resposta", "")
        r.setdefault("pergunta", "")
    return rows

def _limpar_cache():
    """Limpa cache dos dados após mutação."""
    ler_base_conhecimento.clear()

# -----------------------------
# Escrita
# -----------------------------
def sb_upsert(pergunta: str, resposta: str, email: str = "", modelo_email: str = "") -> None:
    """Cria/atualiza uma entrada por 'pergunta' (única)."""
    sb = _sb()
    payload = {
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip(),
        "email": email.strip(),
        "modelo_email": modelo_email.strip(),
    }
    # upsert com conflito em 'pergunta'
    sb.table(TABELA).upsert(payload, on_conflict="pergunta").execute()
    _limpar_cache()

def sb_delete_by_pergunta(pergunta: str) -> None:
    sb = _sb()
    sb.table(TABELA).delete().eq("pergunta", pergunta.strip()).execute()
    _limpar_cache()

# -----------------------------
# Export / Import
# -----------------------------
def exportar_toda_base_json() -> str:
    dados = ler_base_conhecimento()
    # remove campos supérfluos
    campos = ("pergunta", "resposta", "email", "modelo_email")
    limpa = [{k: (d.get(k) or "") for k in campos} for d in dados]
    return json.dumps(limpa, ensure_ascii=False, indent=2)

def sb_bulk_import(lista: List[Dict[str, Any]]) -> None:
    """Importa uma lista de Q&A. Upsert por 'pergunta'."""
    if not isinstance(lista, list):
        raise ValueError("O JSON deve ser uma lista.")
    normalizados = []
    for item in lista:
        if not isinstance(item, dict):
            continue
        p = (item.get("pergunta") or "").strip()
        r = (item.get("resposta") or "").strip()
        if not p or not r:
            continue
        normalizados.append({
            "pergunta": p,
            "resposta": r,
            "email": (item.get("email") or "").strip(),
            "modelo_email": (item.get("modelo_email") or "").strip(),
        })
    if normalizados:
        sb = _sb()
        sb.table(TABELA).upsert(normalizados, on_conflict="pergunta").execute()
        _limpar_cache()
