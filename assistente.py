# -*- coding: utf-8 -*-
"""
Módulo backend do Assist-Decivil
--------------------------------
- Suporte a Supabase (v2.x) com fallback para ficheiro JSON local.
- API compatível com app.py: ler_base_conhecimento, sb_upsert, sb_delete_by_pergunta,
  exportar_toda_base_json, sb_bulk_import, além das funções CRUD de baixo nível:
  carregar_perguntas, criar_pergunta, atualizar_pergunta, apagar_pergunta,
  exportar_base_json e importar_base_json.
"""
from __future__ import annotations
import os, json, uuid, datetime as _dt
from typing import List, Dict, Any, Optional

# Tenta aceder a st.secrets quando a app corre em Streamlit
try:
    import streamlit as st  # type: ignore
except Exception:  # pragma: no cover
    st = None  # type: ignore

# Tenta carregar o cliente Supabase v2
try:
    from supabase import create_client, Client  # type: ignore
except Exception:  # pragma: no cover
    create_client = None  # type: ignore
    Client = None  # type: ignore

# --- Configurações ---
BASE_JSON_PATH = os.getenv("BASE_JSON_PATH", "base_conhecimento.json")
VECTOR_JSON_PATH = os.getenv("VECTOR_JSON_PATH", "base_knowledge_vector.json")
SUPABASE_URL = (os.getenv("SUPABASE_URL") 
                or (st.secrets.get("SUPABASE_URL") if st and hasattr(st, "secrets") and "SUPABASE_URL" in st.secrets else None))
SUPABASE_KEY = (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
                or (st.secrets.get("SUPABASE_SERVICE_KEY") if st and hasattr(st, "secrets") and "SUPABASE_SERVICE_KEY" in st.secrets else None))
TABLE_NAME = os.getenv("SUPABASE_TABLE", "assist_decivil_perguntas")

# Password de administração (UI do Streamlit)
ADMIN_PWD = (os.getenv("ADMIN_PASSWORD")
             or (st.secrets.get("admin_password") if st and hasattr(st, "secrets") and "admin_password" in st.secrets else ""))

# Alias compatível com código antigo
PASSWORD = ADMIN_PWD

# Cliente Supabase em cache
_sb: Optional["Client"] = None

def _supabase_ready() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY and create_client is not None)

def _get_sb() -> Optional["Client"]:
    global _sb
    if _sb is None and _supabase_ready():
        try:
            _sb = create_client(SUPABASE_URL, SUPABASE_KEY)  # type: ignore
        except Exception:
            _sb = None
    return _sb

# ---------- Utilitários JSON ----------
def _read_json(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            # Se o JSON estiver inválido, devolve lista vazia para não partir a app
            return []

def _write_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _normalize_items(items: list) -> list:
    norm = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        it = dict(it)
        it.setdefault("pergunta", "")
        it.setdefault("resposta", "")
        it.setdefault("email", "")
        it.setdefault("modelo_email", "")
        if not it.get("id"):
            it["id"] = str(uuid.uuid4())
        norm.append(it)
    return norm

# ---------- API principal ----------
def carregar_perguntas() -> List[Dict[str, Any]]:
    """
    Carrega perguntas da Supabase; se não estiver configurada, do JSON local.
    Normaliza os registos (campos e IDs) no retorno.
    """
    sb = _get_sb()
    if sb:
        try:
            resp = sb.table(TABLE_NAME).select("*").order("created_at", desc=False).execute()
            data = resp.data or []
            # Normaliza campos esperados
            for it in data:
                it.setdefault("email", "")
                it.setdefault("modelo_email", "")
            return data
        except Exception:
            # Fallback para JSON
            pass

    data = _read_json(BASE_JSON_PATH)
    data = _normalize_items(data)
    # Garante que fica persistido normalizado localmente
    try:
        _write_json(BASE_JSON_PATH, data)
    except Exception:
        pass
    return data

def criar_pergunta(pergunta: str, resposta: str, email: str = "", modelo_email: str = "") -> Dict[str, Any]:
    sb = _get_sb()
    novo = {
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip(),
        "email": (email or "").strip(),
        "modelo_email": (modelo_email or "").strip(),
    }
    if sb:
        try:
            resp = sb.table(TABLE_NAME).insert(novo).execute()
            return (resp.data or [novo])[0]
        except Exception:
            pass
    # JSON fallback
    items = carregar_perguntas()
    novo["id"] = str(uuid.uuid4())
    items.append(novo)
    _write_json(BASE_JSON_PATH, items)
    return novo

def atualizar_pergunta(id: str, pergunta: str, resposta: str, email: str = "", modelo_email: str = "") -> Dict[str, Any]:
    sb = _get_sb()
    update = {
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip(),
        "email": (email or "").strip(),
        "modelo_email": (modelo_email or "").strip(),
        "updated_at": _dt.datetime.utcnow().isoformat() + "Z",
    }
    if sb:
        try:
            resp = sb.table(TABLE_NAME).update(update).eq("id", id).execute()
            return (resp.data or [{**update, "id": id}])[0]
        except Exception:
            pass
    # JSON fallback
    items = carregar_perguntas()
    for i, it in enumerate(items):
        if str(it.get("id")) == str(id):
            items[i] = {**it, **update, "id": id}
            _write_json(BASE_JSON_PATH, items)
            return items[i]
    # Se não encontrou, cria
    created = {**update, "id": str(uuid.uuid4())}
    items.append(created)
    _write_json(BASE_JSON_PATH, items)
    return created

def apagar_pergunta(id: str) -> bool:
    sb = _get_sb()
    if sb:
        try:
            sb.table(TABLE_NAME).delete().eq("id", id).execute()
            return True
        except Exception:
            pass
    items = carregar_perguntas()
    kept = [it for it in items if str(it.get("id")) != str(id)]
    _write_json(BASE_JSON_PATH, kept)
    return len(kept) != len(items)

def exportar_base_json() -> bytes:
    data = carregar_perguntas()
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

def importar_base_json(data_bytes: bytes) -> int:
    try:
        payload = json.loads(data_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError("JSON inválido para importação") from e

    if isinstance(payload, dict):
        # Permite um objeto {"items":[...]}
        if "items" in payload and isinstance(payload["items"], list):
            entries = payload["items"]
        else:
            entries = [payload]
    elif isinstance(payload, list):
        entries = payload
    else:
        raise ValueError("Formato JSON não suportado. Use lista de objetos ou objeto com 'items'.")

    norm = _normalize_items(entries)
    sb = _get_sb()
    if sb:
        # Upsert seguro: tenta update pelo id; se falhar, faz insert
        for it in norm:
            data_no_id = {k: v for k, v in it.items() if k != "id"}
            try:
                # tenta update
                res = sb.table(TABLE_NAME).update(data_no_id).eq("id", it["id"]).execute()
                if not res.data:
                    # se não havia registo, insere
                    sb.table(TABLE_NAME).insert(it).execute()
            except Exception:
                # se deu erro (tabela, etc.), faz fallback total para ficheiro
                pass

    # JSON fallback ou mirror local
    _write_json(BASE_JSON_PATH, norm)
    return len(norm)

# ---------- API de compatibilidade com app.py ----------
def ler_base_conhecimento() -> List[Dict[str, Any]]:
    return carregar_perguntas()

def sb_upsert(pergunta: str, resposta: str, email: str, modelo_email: str) -> Dict[str, Any]:
    dados = carregar_perguntas()
    atual = next((x for x in dados if (x.get("pergunta") or "").strip() == (pergunta or "").strip()), None)
    if atual and atual.get("id"):
        return atualizar_pergunta(atual["id"], pergunta, resposta, email, modelo_email)
    return criar_pergunta(pergunta, resposta, email, modelo_email)

def sb_delete_by_pergunta(pergunta: str) -> bool:
    dados = carregar_perguntas()
    alvo = next((x for x in dados if (x.get("pergunta") or "").strip() == (pergunta or "").strip()), None)
    if not alvo or not alvo.get("id"):
        raise ValueError("Pergunta não encontrada para apagar.")
    return apagar_pergunta(alvo["id"])

def exportar_toda_base_json() -> bytes:
    return exportar_base_json()

def sb_bulk_import(obj: Any) -> int:
    if obj is None:
        raise ValueError("Nenhum dado fornecido para importação.")
    if isinstance(obj, (bytes, bytearray)):
        return importar_base_json(bytes(obj))
    # Assume objeto Python (list/dict)
    return importar_base_json(json.dumps(obj, ensure_ascii=False).encode("utf-8"))
