import streamlit as st
import json
import os
from assistente import gerar_resposta, carregar_base_conhecimento, guardar_base_conhecimento, gerar_embedding

# --- CONFIGURAÇÕES ---
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
ADMIN_PASSWORD = st.secrets["auth"]["admin_password"]

# --- CONFIG PÁGINA ---
st.set_page_config(page_title="Felisberto - Assistente ACSUTA", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #fff3e0;
    }
    .titulo-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 30px;
    }
    .titulo-container img {
        width: 70px;
        height: auto;
    }
    .titulo-container h1 {
        color: #ef6c00;
        font-size: 2em;
        margin: 0;
    }
    .resposta-bloco {
        margin-bottom: 40px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# --- CARREGAR BASE ---
base_conhecimento = carregar_base_conhecimento()

# --- PERGUNTAS DISPONÍVEIS ---
perguntas_existentes = [p["pergunta"] for p in base_conhecimento]
pergunta_selecionada = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas_existentes)

# --- GERAR RESPOSTA ---
if pergunta_selecionada:
    resposta = gerar_resposta(pergunta_selecionada)
    if resposta:
        st.markdown('<div class="resposta-bloco">', unsafe_allow_html=True)
        st.subheader("💡 Resposta do assistente")
        st.markdown(resposta, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- SECÇÃO OPCIONAL: INSERIR NOVA PERGUNTA ---
if st.checkbox("➕ Inserir nova pergunta"):
    st.subheader("Inserir nova pergunta")
    nova_pergunta = st.text_input("Pergunta")
    nova_resposta = st.text_area("Resposta")
    novo_email = st.text_input("Email de contacto (opcional)")
    novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
    password = st.text_input("Password de administrador", type="password")

    if st.button("Guardar pergunta"):
        if password != ADMIN_PASSWORD:
            st.error("🔐 Password incorreta. A pergunta não foi guardada.")
        elif not nova_pergunta or not nova_resposta:
            st.warning("⚠️ Preencha pelo menos a pergunta e a resposta.")
        else:
            base = carregar_base_conhecimento()
            todas = {p["pergunta"]: p for p in base}
            todas[nova_pergunta] = {
                "pergunta": nova_pergunta,
                "resposta": nova_resposta,
                "email": novo_email,
                "modelo_email": novo_modelo
            }
            guardar_base_conhecimento(list(todas.values()))
            gerar_embedding(nova_pergunta, nova_resposta, novo_email, novo_modelo)
            st.success("✅ Pergunta adicionada com sucesso.")
            st.rerun()

# --- SECÇÃO OPCIONAL: EDITAR EXISTENTES ---
if st.checkbox("✏️ Editar perguntas existentes"):
    st.subheader("Editar perguntas")
    pergunta_a_editar = st.selectbox("Escolha uma pergunta para editar:", perguntas_existentes)
    item = next((p for p in base_conhecimento if p["pergunta"] == pergunta_a_editar), None)

    if item:
        edit_resposta = st.text_area("Resposta", value=item.get("resposta", ""))
        edit_email = st.text_input("Email de contacto (opcional)", value=item.get("email", ""))
        edit_modelo = st.text_area("Modelo de email (opcional)", value=item.get("modelo_email", ""))
        password_edit = st.text_input("Password de administrador", type="password")

        if st.button("Guardar alterações"):
            if password_edit != ADMIN_PASSWORD:
                st.error("🔐 Password incorreta. Alterações não guardadas.")
            else:
                for p in base_conhecimento:
                    if p["pergunta"] == pergunta_a_editar:
                        p["resposta"] = edit_resposta
                        p["email"] = edit_email
                        p["modelo_email"] = edit_modelo
                guardar_base_conhecimento(base_conhecimento)
                gerar_embedding(item["pergunta"], edit_resposta, edit_email, edit_modelo)
                st.success("✅ Alterações guardadas.")
                st.rerun()
