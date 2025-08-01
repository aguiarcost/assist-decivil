import streamlit as st
import json
from assistente import (
    gerar_resposta,
    carregar_base_conhecimento,
    guardar_base_conhecimento,
    get_embedding
)
import numpy as np

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
    .footer {
        text-align: center;
        color: gray;
        margin-top: 50px;
    }
    .resposta-bloco {
        margin-bottom: 50px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Carregar base
base_conhecimento = carregar_base_conhecimento()
perguntas_ordenadas = sorted([p["pergunta"] for p in base_conhecimento])

# Dropdown para escolher pergunta
pergunta_escolhida = st.selectbox("Escolha uma pergunta:", [""] + perguntas_ordenadas)

resposta = ""
if pergunta_escolhida:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_escolhida)

# Mostrar resposta formatada
if resposta:
    st.markdown("<div class='resposta-bloco'>", unsafe_allow_html=True)
    st.markdown("### 💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Expansor para inserir nova pergunta
st.markdown("---")
if st.button("➕ Inserir nova pergunta"):
    st.session_state.mostrar_formulario = True

if st.session_state.get("mostrar_formulario"):
    st.markdown("## Nova pergunta manual")
    nova_pergunta = st.text_input("Pergunta")
    nova_resposta = st.text_area("Resposta")
    novo_email = st.text_input("Email (opcional)")
    novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
    password = st.text_input("Password", type="password")

    if st.button("Guardar pergunta"):
        if password != "decivil2024":
            st.error("🔐 Password incorreta.")
        elif not nova_pergunta or not nova_resposta:
            st.warning("⚠️ Preencha a pergunta e a resposta.")
        else:
            nova_entrada = {
                "pergunta": nova_pergunta,
                "resposta": nova_resposta,
                "email": novo_email,
                "modelo_email": novo_modelo
            }
            base = carregar_base_conhecimento()
            todas = {p["pergunta"]: p for p in base}
            todas[nova_pergunta] = nova_entrada
            guardar_base_conhecimento(list(todas.values()))
            st.success("✅ Pergunta adicionada com sucesso. Reinicie a app para ver no menu.")
            st.session_state.mostrar_formulario = False

# Rodapé
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
