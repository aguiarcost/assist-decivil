import json
import numpy as np
import streamlit as st
from datetime import datetime
from supabase import create_client

# Configurações
TABLE_NAME = "base_conhecimento"
PASSWORD = "decivil2024"

# Conexão Supabase
@st.cache_resource
def _sb_client():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        st.error("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY não definidos nos secrets.")
        st.stop()
    return create_client(url, key)

# Ler base de conhecimento
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

# Upsert por pergunta
def sb_upsert(pergunta: str, resposta: str, email: str, modelo_email: str):
    sb = _sb_client()
    payload = {
        "pergunta": (pergunta or "").strip(),
        "resposta": (resposta or "").strip(),
        "email": (email or "").strip(),
        "modelo_email": (modelo_email or "").strip(),
        "created_at": datetime.utcnow().isoformat()
    }
    sb.table(TABLE_NAME).upsert(payload, on_conflict="pergunta").execute()
    return ler_base_conhecimento()

# Apagar por pergunta
def sb_delete_by_pergunta(pergunta: str):
    sb = _sb_client()
    sb.table(TABLE_NAME).delete().eq("pergunta", pergunta.strip()).execute()
    return ler_base_conhecimento()

# Exportar JSON
def exportar_toda_base_json() -> str:
    dados = ler_base_conhecimento()
    return json.dumps(
        [
            {
                "pergunta": d["pergunta"],
                "resposta": d["resposta"],
                "email": d["email"],
                "modelo_email": d["modelo_email"],
            }
            for d in dados
        ],
        ensure_ascii=False,
        indent=2
    )

# Função principal de resposta (sem embeddings, só base)
def gerar_resposta(pergunta: str) -> tuple[str, str]:
    base = ler_base_conhecimento()
    for item in base:
        if item["pergunta"].strip().lower() == pergunta.strip().lower():
            resposta = item.get("resposta", "")
            modelo_email = item.get("modelo_email", "")
            return resposta, modelo_email
    return "❌ Não encontrei uma resposta para a tua pergunta.", ""
