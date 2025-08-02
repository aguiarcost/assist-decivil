import streamlit as st
import os
import json
from datetime import datetime
from assistente import gerar_resposta, carregar_base_conhecimento, guardar_base_conhecimento

# Configuração da página
st.set_page_config(page_title="Felisberto - Assistente ACSUTA", layout="wide")

# Carregar perguntas
base_conhecimento = carregar_base_conhecimento()
perguntas_existentes = sorted([item["pergunta"] for item in base_conhecimento])

# Estilo personalizado
st.markdown("""
    <style>
        .stApp {
            background-color: #fffaf0;
        }
        .titulo {
            color: #d35400;
            font-size: 2.2em;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .separador {
            margin-top: 40px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Título
st.markdown('<div class="titulo">📘 Felisberto, Assistente Administrativo ACSUTA</div>', unsafe_allow_html=True)

# Dropdown de perguntas
pergunta_selecionada = st.selectbox("Escolha uma pergunta existente:", [""] + perguntas_existentes)

# Responder
if pergunta_selecionada:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_selecionada)
    if resposta:
        st.markdown("### 💡 Resposta")
        st.markdown(resposta, unsafe_allow_html=True)

st.markdown('<div class="separador"></div>', unsafe_allow_html=True)

# Adicionar nova pergunta
if st.checkbox("➕ Inserir nova pergunta"):
    with st.form("formulario_nova_pergunta", clear_on_submit=False):
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta")
        novo_email = st.text_input("Email de contacto (opcional)")
        modelo_email = st.text_area("Modelo de email sugerido (opcional)")
        password_input = st.text_input("Palavra-passe", type="password")

        submetido = st.form_submit_button("Guardar")

        if submetido:
            password_correta = os.getenv("PASSWORD_ADMIN") or st.secrets.get("PASSWORD_ADMIN", "")
            if password_input != password_correta:
                st.error("❌ Palavra-passe incorreta.")
            elif not nova_pergunta or not nova_resposta:
                st.warning("⚠️ Preencha a pergunta e a resposta.")
            else:
                novo_item = {
                    "pergunta": nova_pergunta.strip(),
                    "resposta": nova_resposta.strip(),
                    "email": novo_email.strip(),
                    "modelo_email": modelo_email.strip()
                }
                guardar_base_conhecimento(novo_item)
                st.success("✅ Nova pergunta adicionada com sucesso. Recarregue a página para ver no dropdown.")
