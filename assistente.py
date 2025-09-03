# assistente.py
import os
import json
import difflib
from typing import List, Dict, Any

import streamlit as st
from supabase import create_client

TABELA = "base_conhecimento"
LOCAL_JSON = "base_conhecimento.json"

def _get_supabase():
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
    key = st.secrets.get("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_SERVICE_KEY"))
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

def _normalizar_registo(x: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": x.get("id"),
        "pergunta": (x.get("pergunta") or "").strip(),
        "resposta": (x.get("resposta") or "").strip(),
        "email": (x.get("email") or "").strip(),
        "modelo_email": (x.get("modelo_email") or "").strip(),
    }

def _ler_json() -> List[Dict[str, Any]]:
    if not os.path.exists(LOCAL_JSON):
        return []
    try:
        with open(LOCAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [_normalizar_registo(x) for x in data]
    except Exception:
        return []

def _gravar_json(registos: List[Dict[str, Any]]) -> None:
    registos_norm = [_normalizar_registo(x) for x in registos]
    with open(LOCAL_JSON, "w", encoding="utf-8") as f:
        json.dump(registos_norm, f, ensure_ascii=False, indent=2)

def ler_base_conhecimento() -> List[Dict[str, Any]]:
    sb = _get_supabase()
    if sb:
        res = sb.table(TABELA).select("id, pergunta, resposta, email, modelo_email").order("pergunta").execute()
        linhas = [_normalizar_registo(x) for x in (res.data or [])]
        if linhas:
            _gravar_json(linhas)
        return linhas
    return _ler_json()

def encontrar_perguntas_semelhantes(texto: str, n=3, cutoff=0.6) -> List[str]:
    todas = [x["pergunta"] for x in ler_base_conhecimento() if x.get("pergunta")]
    return difflib.get_close_matches(texto, todas, n=n, cutoff=cutoff)
