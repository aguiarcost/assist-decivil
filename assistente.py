import json
import os
import streamlit as st
import numpy as np
from datetime import datetime
from supabase import create_client  # ✅ corrigido: não importar Client

# =========================
# Configuração Supabase
# =========================
TABLE_NAME = "base_conhecimento"
ADMIN_PASSWORD = "decivil2024"

def _sb_client():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        st.error("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY não definidos nos secrets.")
        st.stop()
    return create_client(url, key)

# =========================
# Funções Base de Conhecimento
# =========================
def ler_base_conhecimento() -> list:
    sb = _sb_client()
    res = sb.table(TABLE_NAME).select("*").order("pergunta").execute()
    dados = res.data or []
    out = []
    for r in dados:
        out.append({
            "id": r.get("id"),
            "pergunta": (r.get("pergunta") or "").strip(),
            "resposta": (r.get("resposta") or "").strip(),
            "email": (r.get("email") or "").strip(),
            "modelo_email": (r.get("modelo_email") or r.get("modelo") or "").strip(),
            "created_at": r.get("created_at"),
        })
    return out

def upsert_pergunta(_, nova: dict) -> list:
    sb = _sb_client()
    payload = {
        "pergunta": (nova.get("pergunta") or "").strip(),
        "resposta": (nova.get("resposta") or "").strip(),
        "email": (nova.get("email") or "").strip(),
        "modelo_email": (nova.get("modelo_email") or "").strip(),
        "updated_at": datetime.utcnow().isoformat()
    }
    sb.table(TABLE_NAME).upsert(payload, on_conflict="pergunta").execute()
    return ler_base_conhecimento()

def apagar_pergunta(_, pergunta: str) -> list:
    sb = _sb_client()
    sb.table(TABLE_NAME).delete().eq("pergunta", pergunta.strip()).execute()
    return ler_base_conhecimento()

def exportar_toda_base_json() -> str:
    dados = ler_base_conhecimento()
    return json.dumps(
        [
            {
                "pergunta": d["pergunta"],
                "resposta": d["resposta"],
                "email": d.get("email", ""),
                "modelo_email": d.get("modelo_email", "")
            }
            for d in dados
        ],
        ensure_ascii=False, indent=2
    )
