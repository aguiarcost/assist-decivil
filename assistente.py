# assistente.py
import os
import json
from typing import List, Dict, Any, Optional

import streamlit as st
from supabase import create_client  # requer 'supabase' no requirements

# -------------------------
# Config
# -------------------------
TABELA = "base_conhecimento"
LOCAL_JSON = "base_conhecimento.json"

# -------------------------
# Helpers Supabase / Fallback
# -------------------------
def _get_supabase():
    """
    Devolve o cliente Supabase se houver credenciais válidas nos secrets ou env.
    Caso contrário, devolve None e a app passa a usar o JSON local.
    """
    url = None
    key = None

    # Streamlit Cloud / local .streamlit/secrets.toml
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_SERVICE_KEY")
    except Exception:
        pass

    # Variáveis de ambiente (codespaces, local, etc.)
    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception:
        return None


def _normalizar_registo(x: Dict[str, Any]) -> Dict[str, Any]:
    """Garante chaves e remove espaços extra."""
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


def _parece_uuid(valor: str) -> bool:
    return isinstance(valor, str) and "-" in valor and len(valor) in (36, 32)


# -------------------------
# API pública usada no app
# -------------------------
def ler_base_conhecimento() -> List[Dict[str, Any]]:
    """
    Lê toda a base de conhecimento. Usa Supabase se disponível,
    senão recorre ao JSON local. Mantém JSON como cache/backup.
    """
    sb = _get_supabase()
    if sb:
        res = sb.table(TABELA).select(
            "id, pergunta, resposta, email, modelo_email"
        ).order("pergunta").execute()
        linhas = [_normalizar_registo(x) for x in (res.data or [])]
        if linhas:  # backup local
            _gravar_json(linhas)
        return linhas
    return _ler_json()


@st.cache_data(show_spinner=False)
def carregar_perguntas_frequentes() -> List[str]:
    """
    Devolve apenas a lista de perguntas, ordenadas para o dropdown.
    É cacheada para tornar o UI mais rápido (é invalidada nos writes).
    """
    base = ler_base_conhecimento()
    return sorted({x["pergunta"] for x in base if x["pergunta"]})


def obter_resposta_por_pergunta(pergunta: str) -> Optional[Dict[str, str]]:
    """
    Devolve um dicionário com 'resposta', 'email' e 'modelo_email'
    para a pergunta indicada, se existir; caso contrário, None.
    """
    if not pergunta:
        return None
    base = ler_base_conhecimento()
    for x in base:
        if x["pergunta"] == pergunta:
            return {
                "resposta": x["resposta"],
                "email": x.get("email", ""),
                "modelo_email": x.get("modelo_email", ""),
            }
    return None


def criar_pergunta(pergunta: str, resposta: str, email: str = "", modelo_email: str = "") -> None:
    """
    Cria nova pergunta. No JSON local faz deduplicação por pergunta.
    No Supabase, insere e atualiza o cache local.
    """
    reg = _normalizar_registo(
        {"pergunta": pergunta, "resposta": resposta, "email": email, "modelo_email": modelo_email}
    )

    sb = _get_supabase()
    if sb:
        sb.table(TABELA).insert(reg).execute()
        # invalida cache do dropdown e atualiza backup local
        st.cache_data.clear()
        _gravar_json(ler_base_conhecimento())
        return

    # Local JSON (dedupe por pergunta)
    todos = _ler_json()
    dedup = {x["pergunta"]: x for x in todos}
    dedup[reg["pergunta"]] = reg
    novos = list(dedup.values())
    _gravar_json(novos)
    st.cache_data.clear()


def editar_pergunta(
    id_ou_pergunta: str,
    nova_pergunta: str,
    nova_resposta: str,
    novo_email: str = "",
    novo_modelo_email: str = "",
) -> None:
    payload = _normalizar_registo(
        {"pergunta": nova_pergunta, "resposta": nova_resposta, "email": novo_email, "modelo_email": novo_modelo_email}
    )

    sb = _get_supabase()
    if sb:
        if _parece_uuid(id_ou_pergunta):
            sb.table(TABELA).update(payload).eq("id", id_ou_pergunta).execute()
        else:
            sb.table(TABELA).update(payload).eq("pergunta", id_ou_pergunta).execute()
        st.cache_data.clear()
        _gravar_json(ler_base_conhecimento())
        return

    # Local JSON
    todos = _ler_json()
    houve = False
    for x in todos:
        if x.get("id") == id_ou_pergunta or x.get("pergunta") == id_ou_pergunta:
            x.update(payload)
            houve = True
            break
    if not houve:
        todos.append(payload)
    _gravar_json(todos)
    st.cache_data.clear()


def apagar_pergunta(id_ou_pergunta: str) -> None:
    sb = _get_supabase()
    if sb:
        if _parece_uuid(id_ou_pergunta):
            sb.table(TABELA).delete().eq("id", id_ou_pergunta).execute()
        else:
            sb.table(TABELA).delete().eq("pergunta", id_ou_pergunta).execute()
        st.cache_data.clear()
        _gravar_json(ler_base_conhecimento())
        return

    # Local JSON
    todos = _ler_json()
    novos = [
        x for x in todos
        if x.get("id") != id_ou_pergunta and x.get("pergunta") != id_ou_pergunta
    ]
    _gravar_json(novos)
    st.cache_data.clear()
