from supabase import create_client
import os
import streamlit as st
from supabase import create_client

# Lê as secrets do ficheiro .streamlit/secrets.toml ou do ambiente no Streamlit Cloud
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def ler_base_conhecimento():
    """Lê todos os registos da base de conhecimento."""
    response = supabase.table("base_conhecimento").select("*").order("created_at", desc=True).execute()
    return response.data or []


def criar_pergunta(pergunta, resposta, email="", modelo_email=""):
    """Cria uma nova pergunta na base de dados (sem enviar ID)."""
    novo_registo = {
        "pergunta": pergunta,
        "resposta": resposta,
        "email": email,
        "modelo_email": modelo_email,
    }
    supabase.table("base_conhecimento").insert(novo_registo).execute()


def editar_pergunta(id_ou_pergunta, nova_pergunta, nova_resposta, novo_email="", novo_modelo=""):
    """Edita uma pergunta existente com base no ID ou no texto da pergunta."""
    supabase.table("base_conhecimento").update({
        "pergunta": nova_pergunta,
        "resposta": nova_resposta,
        "email": novo_email,
        "modelo_email": novo_modelo,
    }).eq("id", id_ou_pergunta).execute()


def apagar_pergunta(id_ou_pergunta):
    """Apaga uma pergunta da base de dados com base no ID ou no texto da pergunta."""
    supabase.table("base_conhecimento").delete().eq("id", id_ou_pergunta).execute()
