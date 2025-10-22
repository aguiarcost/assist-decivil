import os
import json
import time
import streamlit as st
from supabase import create_client, Client
from httpx import ConnectError, HTTPStatusError

# === Inicialização segura ===
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning("⚠️ Não foi possível inicializar a ligação ao Supabase.")
        print("Erro ao criar cliente Supabase:", e)
else:
    st.warning("⚠️ Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas em st.secrets.")

# === Funções ===
def ler_base_conhecimento():
    """Lê todos os registos da base de conhecimento (Supabase ou local)."""
    if supabase is None:
        return _ler_base_local("base_conhecimento.json")

    for tentativa in range(3):
        try:
            response = (
                supabase.table("base_conhecimento")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return response.data or []
        except ConnectError as e:
            print(f"Tentativa {tentativa+1}/3: erro de ligação ao Supabase -> {e}")
            time.sleep(2)
        except HTTPStatusError as e:
            print("Erro HTTP Supabase:", e)
            break
        except Exception as e:
            print("Erro inesperado:", e)
            break

    st.warning("⚠️ Falha ao ligar ao Supabase. A usar base local.")
    return _ler_base_local("base_conhecimento.json")


def _ler_base_local(ficheiro_json: str):
    """Fallback: lê base de conhecimento de um ficheiro local."""
    try:
        with open(ficheiro_json, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Ficheiro local base_conhecimento.json não encontrado.")
    except json.JSONDecodeError:
        st.error("❌ Erro ao ler JSON local.")
    return []


def criar_pergunta(pergunta, resposta, email="", modelo_email=""):
    if supabase is None:
        st.warning("Sem ligação ao Supabase. Pergunta não gravada.")
        return None
    try:
        response = supabase.table("base_conhecimento").insert(
            {"pergunta": pergunta, "resposta": resposta, "email": email, "modelo_email": modelo_email}
        ).execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao criar pergunta: {e}")
        return None


def editar_pergunta(id_registo, nova_pergunta, nova_resposta):
    if supabase is None:
        st.warning("Sem ligação ao Supabase.")
        return None
    try:
        response = supabase.table("base_conhecimento").update(
            {"pergunta": nova_pergunta, "resposta": nova_resposta}
        ).eq("id", id_registo).execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao editar pergunta: {e}")
        return None


def apagar_pergunta(id_registo):
    if supabase is None:
        st.warning("Sem ligação ao Supabase.")
        return None
    try:
        response = supabase.table("base_conhecimento").delete().eq("id", id_registo).execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao apagar pergunta: {e}")
        return None
