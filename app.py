import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import os

# Configurações Supabase
SUPABASE_URL = "https://shphlpyzasvylrosamid.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNocGhscHl6YXN2eWxyb3NhbWlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQxNzI2MzAsImV4cCI6MjA2OTc0ODYzMH0.layrRm6BnmiQDwKg6HwGdCh6LaEN31gM7aMETodxrrQ"
PASSWORD_ADMIN = "decivil2024"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Layout da app
st.set_page_config(page_title="Felisberto – Assistente ACSUTA", layout="wide")
st.title("🤖 Felisberto – Assistente Administrativo ACSUTA")

# Funções Supabase
def listar_perguntas():
    resp = supabase.table("perguntas").select("*").order("created_at", desc=False).execute()
    return resp.data if resp.data else []

def inserir_pergunta(pergunta, resposta, email, modelo):
    supabase.table("perguntas").insert({
        "pergunta": pergunta,
        "resposta": resposta,
        "email": email,
        "modelo": modelo,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

def atualizar_pergunta(id_, resposta, email, modelo):
    supabase.table("perguntas").update({
        "resposta": resposta,
        "email": email,
        "modelo": modelo
    }).eq("id", id_).execute()

def apagar_pergunta(id_):
    supabase.table("perguntas").delete().eq("id", id_).execute()

# Carregamento das perguntas
dados = listar_perguntas()
opcoes = [d["pergunta"] for d in dados]

# Dropdown com perguntas
pergunta_escolhida = st.selectbox("📌 Escolha uma pergunta:", [""] + opcoes)
if pergunta_escolhida:
    item = next((d for d in dados if d["pergunta"] == pergunta_escolhida), None)
    if item:
        st.markdown("### 💡 Resposta")
        st.markdown(item["resposta"])
        if item.get("email"):
            st.markdown(f"📫 **Email de contacto:** {item['email']}")
        if item.get("modelo"):
            st.markdown("📧 **Modelo de email sugerido:**")
            st.code(item["modelo"])

st.markdown("---")

# Expander para nova pergunta
with st.expander("➕ Inserir nova pergunta"):
    nova_p = st.text_input("Pergunta")
    nova_r = st.text_area("Resposta")
    nova_e = st.text_input("Email (opcional)")
    nova_m = st.text_area("Modelo de email sugerido (opcional)")
    pw = st.text_input("Password de administrador", type="password")
    if st.button("💾 Guardar nova pergunta"):
        if pw != PASSWORD_ADMIN:
            st.error("🔒 Password incorreta.")
        elif not nova_p or not nova_r:
            st.warning("❗ Preencha a pergunta e a resposta.")
        else:
            inserir_pergunta(nova_p, nova_r, nova_e, nova_m)
            st.success("✅ Pergunta adicionada.")
            st.experimental_rerun()

# Expander para editar ou apagar perguntas
with st.expander("✏️ Editar ou apagar pergunta existente"):
    editar = st.selectbox("Selecione uma pergunta para editar/apagar:", [""] + opcoes, key="editar")
    if editar:
        item = next((d for d in dados if d["pergunta"] == editar), None)
        if item:
            resp = st.text_area("Resposta", value=item["resposta"])
            email = st.text_input("Email", value=item.get("email", ""))
            modelo = st.text_area("Modelo de email sugerido", value=item.get("modelo", ""))
            apagar = st.checkbox("🗑️ Apagar esta pergunta")
            pw2 = st.text_input("Password para confirmar", type="password")
            if st.button("✅ Aplicar alterações"):
                if pw2 != PASSWORD_ADMIN:
                    st.error("🔒 Password incorreta.")
                else:
                    if apagar:
                        apagar_pergunta(item["id"])
                        st.success("❌ Pergunta apagada.")
                    else:
                        atualizar_pergunta(item["id"], resp, email, modelo)
                        st.success("✅ Pergunta atualizada.")
                    st.experimental_rerun()

st.markdown("---")
st.caption("© 2025 AAC")
