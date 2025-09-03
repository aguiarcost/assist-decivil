import os
import json
from typing import List, Dict, Optional, Tuple

import streamlit as st
from supabase import create_client


# ---------- Config / Secrets ----------
def _get_admin_password() -> str:
    # podes sobrepor em secrets.toml: ADMIN_PASSWORD="..."
    return st.secrets.get("ADMIN_PASSWORD", "decivil2024")


def _supabase_client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Faltam as credenciais do Supabase. Define SUPABASE_URL e SUPABASE_SERVICE_KEY em .streamlit/secrets.toml"
        )
    return create_client(url, key)


TABELA = "base_conhecimento"  # campos: id(uuid), pergunta(text), resposta(text), email(text), modelo_email(text), created_at(ts)


# ---------- Leitura ----------
def obter_todos() -> List[Dict]:
    sb = _supabase_client()
    resp = sb.table(TABELA).select("*").order("pergunta").execute()
    dados = resp.data or []
    # Normalize keys para evitar KeyErrors
    for d in dados:
        d.setdefault("email", "")
        d.setdefault("modelo_email", "")
    return dados


def obter_perguntas() -> List[str]:
    return [d["pergunta"] for d in obter_todos()]


def obter_por_pergunta(pergunta: str) -> Optional[Dict]:
    sb = _supabase_client()
    resp = sb.table(TABELA).select("*").eq("pergunta", pergunta).limit(1).execute()
    data = resp.data or []
    if not data:
        return None
    d = data[0]
    d.setdefault("email", "")
    d.setdefault("modelo_email", "")
    return d


# ---------- Escrita ----------
def validar_password(pw: str) -> bool:
    return pw.strip() == _get_admin_password()


def upsert_registo(pergunta: str, resposta: str, email: str = "", modelo_email: str = "") -> None:
    sb = _supabase_client()
    payload = {
        "pergunta": pergunta.strip(),
        "resposta": resposta.strip(),
        "email": email.strip(),
        "modelo_email": modelo_email.strip(),
    }
    # upsert por "pergunta"
    sb.table(TABELA).upsert(payload, on_conflict="pergunta").execute()


def apagar_por_pergunta(pergunta: str) -> None:
    sb = _supabase_client()
    sb.table(TABELA).delete().eq("pergunta", pergunta).execute()


# ---------- Import / Export ----------
def exportar_json() -> str:
    dados = obter_todos()
    # Exporta apenas campos relevantes (sem ids/timestamps)
    enxutos = [
        {
            "pergunta": d.get("pergunta", ""),
            "resposta": d.get("resposta", ""),
            "email": d.get("email", ""),
            "modelo_email": d.get("modelo_email", ""),
        }
        for d in dados
    ]
    return json.dumps(enxutos, ensure_ascii=False, indent=2)


def importar_json(conteudo: List[Dict]) -> Tuple[int, int]:
    """Devolve (inseridos_ou_atualizados, total_recebidos). Usa upsert por pergunta."""
    if not isinstance(conteudo, list):
        raise ValueError("O ficheiro JSON deve conter uma lista.")
    count = 0
    for item in conteudo:
        p = (item.get("pergunta") or "").strip()
        r = (item.get("resposta") or "").strip()
        e = (item.get("email") or "").strip()
        m = (item.get("modelo_email") or "").strip()
        if p and r:
            upsert_registo(p, r, e, m)
            count += 1
    return count, len(conteudo)


# ---------- Resposta ----------
def formatar_resposta_markdown(registo: Dict) -> str:
    """Devolve markdown com a resposta + contacto + modelo (se existir)."""
    if not registo:
        return "Não encontrei uma resposta para essa pergunta."
    resposta = registo.get("resposta", "").strip()
    email = registo.get("email", "").strip()
    modelo = registo.get("modelo_email", "").strip()

    partes = [resposta] if resposta else []

    if email:
        partes.append(f"\n**📧 Email de contacto:** [{email}](mailto:{email})")
    if modelo:
        partes.append("\n**📝 Modelo de email sugerido:**\n\n```\n" + modelo + "\n```")

    return "\n".join(partes)


def gerar_resposta(pergunta: str) -> str:
    reg = obter_por_pergunta(pergunta)
    return formatar_resposta_markdown(reg)
