# assistente.py
import os
import json
import streamlit as st
from typing import List, Dict, Any, Optional

# ---------- Config ----------
LOCAL_JSON = "base_conhecimento.json"
TABELA = "base_conhecimento"

# ---------- Supabase client ----------
def _get_supabase():
    """Devolve o cliente Supabase se existir configuração; caso contrário None."""
    try:
        from supabase import create_client  # requer 'supabase' no requirements
        url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None

# ---------- Fallback JSON ----------
def _ler_json() -> List[Dict[str, Any]]:
    if not os.path.exists(LOCAL_JSON):
        return []
    try:
        with open(LOCAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            # normalizar chaves
            norm = []
            for x in data:
                norm.append({
                    "id": x.get("id"),
                    "pergunta": x.get("pergunta", "").strip(),
                    "resposta": x.get("resposta", "").strip(),
                    "email": x.get("email", "").strip(),
                    "modelo_email": x.get("modelo_email", "").strip(),
                })
            return norm
    except Exception:
        return []

def _gravar_json(registos: List[Dict[str, Any]]) -> None:
    with open(LOCAL_JSON, "w", encoding="utf-8") as f:
        json.dump(registos, f, ensure_ascii=False, indent=2)

# ---------- API pública usada no app ----------
def ler_base_conhecimento() -> List[Dict[str, Any]]:
    """Lê toda a base (Supabase se existir; senão JSON)."""
    sb = _get_supabase()
    if sb:
        # selecionar colunas relevantes
        res = sb.table(TABELA).select("id, pergunta, resposta, email, modelo_email").order("pergunta").execute()
        linhas = res.data or []
        # garantir tipos/normalização
        for x in linhas:
            x["pergunta"] = (x.get("pergunta") or "").strip()
            x["resposta"] = (x.get("resposta") or "").strip()
            x["email"] = (x.get("email") or "").strip()
            x["modelo_email"] = (x.get("modelo_email") or "").strip()
        # manter cópia local (cache/backup)
        if linhas:
            _gravar_json(linhas)
        return linhas
    # fallback local
    return _ler_json()

def criar_pergunta(pergunta: str, resposta: str, email: str = "", modelo_email: str = "") -> None:
    reg = {
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip(),
        "email": (email or "").strip(),
        "modelo_email": (modelo_email or "").strip(),
    }
    sb = _get_supabase()
    if sb:
        sb.table(TABELA).insert(reg).execute()
        # atualizar cache local
        todos = ler_base_conhecimento()
        _gravar_json(todos)
        return
    # local JSON
    todos = _ler_json()
    # evitar duplicados por pergunta
    dedup = {x["pergunta"]: x for x in todos}
    dedup[reg["pergunta"]] = reg
    _gravar_json(list(dedup.values()))

def editar_pergunta(id_ou_pergunta: str, nova_pergunta: str, nova_resposta: str,
                    novo_email: str = "", novo_modelo_email: str = "") -> None:
    sb = _get_supabase()
    payload = {
        "pergunta": nova_pergunta.strip(),
        "resposta": nova_resposta.strip(),
        "email": (novo_email or "").strip(),
        "modelo_email": (novo_modelo_email or "").strip(),
    }
    if sb:
        # Aceita id (uuid) ou a pergunta como “chave”
        if _parece_uuid(id_ou_pergunta):
            sb.table(TABELA).update(payload).eq("id", id_ou_pergunta).execute()
        else:
            sb.table(TABELA).update(payload).eq("pergunta", id_ou_pergunta).execute()
        _gravar_json(ler_base_conhecimento())
        return
    # local JSON
    todos = _ler_json()
    houve = False
    for x in todos:
        if x.get("id") == id_ou_pergunta or x.get("pergunta") == id_ou_pergunta:
            x.update(payload)
            houve = True
            break
    if not houve:
        # se não encontrou, cria
        todos.append(payload)
    _gravar_json(todos)

def apagar_pergunta(id_ou_pergunta: str) -> None:
    sb = _get_supabase()
    if sb:
        if _parece_uuid(id_ou_pergunta):
            sb.table(TABELA).delete().eq("id", id_ou_pergunta).execute()
        else:
            sb.table(TABELA).delete().eq("pergunta", id_ou_pergunta).execute()
        _gravar_json(ler_base_conhecimento())
        return
    # local JSON
    todos = _ler_json()
    novos = [x for x in todos if x.get("id") != id_ou_pergunta and x.get("pergunta") != id_ou_pergunta]
    _gravar_json(novos)

def _parece_uuid(valor: str) -> bool:
    if not valor or not isinstance(valor, str):
        return False
    return len(valor) in (36, 32) and "-" in valor
