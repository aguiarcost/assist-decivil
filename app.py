# app.py - Código Principal da Aplicação Streamlit

import streamlit as st
from assistente import (
    carregar_base_conhecimento,
    gerar_resposta,
    adicionar_pergunta_supabase,
    atualizar_pergunta_supabase,
)
import os
import hashlib  # Para hashing de password

st.set_page_config(page_title="Felisberto, Assistente ACSUTA", layout="wide")

# Estilo personalizado com avatar e tons laranja
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
    .footer {
        text-align: center;
        color: gray;
        margin-top: 50px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Hash da password admin para segurança
ADMIN_PASSWORD_HASH = hashlib.sha256(os.environ.get("ADMIN_PASSWORD", "").encode()).hexdigest()

# Carregar perguntas com cache
@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_perguntas_ordenadas():
    perguntas = carregar_base_conhecimento()
    return sorted([p["pergunta"] for p in perguntas])

perguntas_ordenadas = get_perguntas_ordenadas()

st.markdown("## ❓ Perguntas Frequentes")

pergunta_selecionada = st.selectbox("Escolha uma pergunta:", [""] + perguntas_ordenadas)

if pergunta_selecionada:
    resposta = gerar_resposta(pergunta_selecionada)
    st.markdown("### 💬 Resposta")
    st.markdown(resposta, unsafe_allow_html=True)

st.markdown("---")
st.markdown("## ➕ Inserir nova pergunta")

with st.expander("Adicionar nova pergunta"):
    nova_pergunta = st.text_input("Pergunta")
    nova_resposta = st.text_area("Resposta")
    novo_email = st.text_input("Email de contacto (opcional)")
    novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
    password = st.text_input("Password de administrador", type="password")
    if st.button("Guardar nova pergunta"):
        if not nova_pergunta or not nova_resposta:
            st.warning("⚠️ Pergunta e resposta são obrigatórias.")
        elif hashlib.sha256(password.encode()).hexdigest() != ADMIN_PASSWORD_HASH:
            st.error("❌ Password incorreta.")
        else:
            sucesso = adicionar_pergunta_supabase(nova_pergunta, nova_resposta, novo_email, novo_modelo)
            if sucesso:
                st.success("✅ Nova pergunta adicionada com sucesso.")
                st.cache_data.clear()  # Limpa cache
            else:
                st.error("❌ Erro ao adicionar pergunta.")

st.markdown("---")
st.markdown("## ✏️ Editar pergunta existente")

with st.expander("Editar pergunta existente"):
    pergunta_a_editar = st.selectbox("Selecione a pergunta:", [""] + perguntas_ordenadas)
    if pergunta_a_editar:
        dados = {p["pergunta"]: p for p in carregar_base_conhecimento()}[pergunta_a_editar]
        nova_resposta = st.text_area("Editar resposta", value=dados.get("resposta", ""))
        novo_email = st.text_input("Editar email (opcional)", value=dados.get("email", ""))
        novo_modelo = st.text_area("Editar modelo de email (opcional)", value=dados.get("modelo_email", ""))
        password_edit = st.text_input("Password de administrador", type="password", key="edit_pwd")
        if st.button("Guardar alterações"):
            if hashlib.sha256(password_edit.encode()).hexdigest() != ADMIN_PASSWORD_HASH:
                st.error("❌ Password incorreta.")
            else:
                sucesso = atualizar_pergunta_supabase(pergunta_a_editar, nova_resposta, novo_email, novo_modelo)
                if sucesso:
                    st.success("✅ Pergunta atualizada com sucesso.")
                    st.cache_data.clear()  # Limpa cache
                else:
                    st.error("❌ Erro ao atualizar pergunta.")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
