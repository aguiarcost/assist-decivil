import json
import numpy as np
from datetime import datetime
import streamlit as st
from supabase import create_client

# -----------------------------
# Configuração Supabase
# -----------------------------
def _sb_client():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        st.error("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY não definidos nos secrets.")
        st.stop()
    return create_client(url, key)

TABLE_NAME = "base_conhecimento"

# -----------------------------
# Funções de acesso à base
# -----------------------------
def carregar_perguntas_frequentes() -> list[str]:
    sb = _sb_client()
    res = sb.table(TABLE_NAME).select("pergunta").order("pergunta").execute()
    return [r["pergunta"] for r in (res.data or []) if r.get("pergunta")]

def obter_resposta(pergunta: str) -> tuple[str, str]:
    """Devolve (resposta, modelo_email) para a pergunta, ou (None,None)."""
    sb = _sb_client()
    res = sb.table(TABLE_NAME).select("*").eq("pergunta", pergunta).execute()
    if res.data:
        item = res.data[0]
        resposta = item.get("resposta", "")
        modelo = item.get("modelo_email", "")
        email = item.get("email", "")
        texto = resposta
        if email:
            texto += f"\n\n**📧 Contacto:** [{email}](mailto:{email})"
        return texto, modelo
    return None, None

def upsert_pergunta(pergunta: str, resposta: str, email: str, modelo_email: str):
    sb = _sb_client()
    payload = {
        "pergunta": (pergunta or "").strip(),
        "resposta": (resposta or "").strip(),
        "email": (email or "").strip(),
        "modelo_email": (modelo_email or "").strip(),
        "created_at": datetime.utcnow().isoformat()
    }
    sb.table(TABLE_NAME).upsert(payload, on_conflict="pergunta").execute()

def apagar_pergunta(pergunta: str):
    sb = _sb_client()
    sb.table(TABLE_NAME).delete().eq("pergunta", pergunta.strip()).execute()

def importar_perguntas(novas: list[dict]):
    sb = _sb_client()
    rows = []
    for it in novas:
        if not isinstance(it, dict):
            continue
        if "pergunta" in it and "resposta" in it:
            rows.append({
                "pergunta": (it.get("pergunta") or "").strip(),
                "resposta": (it.get("resposta") or "").strip(),
                "email": (it.get("email") or "").strip(),
                "modelo_email": (it.get("modelo_email") or it.get("modelo") or "").strip(),
                "created_at": datetime.utcnow().isoformat()
            })
    if rows:
        sb.table(TABLE_NAME).upsert(rows, on_conflict="pergunta").execute()

def exportar_perguntas() -> str:
    sb = _sb_client()
    res = sb.table(TABLE_NAME).select("*").order("pergunta").execute()
    dados = res.data or []
    export = []
    for d in dados:
        export.append({
            "pergunta": d.get("pergunta", ""),
            "resposta": d.get("resposta", ""),
            "email": d.get("email", ""),
            "modelo_email": d.get("modelo_email", ""),
        })
    return json.dumps(export, ensure_ascii=False, indent=2)
