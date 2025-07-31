import streamlit as st
import json
import os
from datetime import datetime
from assistente import gerar_resposta, guardar_nova_pergunta

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"
PASSWORD_ADMIN = "decivil2024"

st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fff3e0; }
    .titulo-container { display: flex; align-items: center; gap: 10px; margin-top: 10px; margin-bottom: 30px; }
    .titulo-container img { width: 70px; height: auto; }
    .titulo-container h1 { color: #ef6c00; font-size: 2em; margin: 0; }
    .footer { text-align: center; color: gray; margin-top: 50px; }
    .spacer { margin: 50px 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_pergunta_no_historico(pergunta):
    registo = {"pergunta": pergunta, "timestamp": datetime.now().isoformat()}
    historico = []
    if os.path.exists(CAMINHO_HISTORICO):
        try:
            with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as f:
                historico = json.load(f)
        except json.JSONDecodeError:
            historico = []
    historico.append(registo)
    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

base_conhecimento = carregar_base_conhecimento()
perguntas = [p["pergunta"] for p in base_conhecimento]

pergunta_dropdown = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas)
resposta = ""
if pergunta_dropdown:
    resposta = gerar_resposta(pergunta_dropdown)
    guardar_pergunta_no_historico(pergunta_dropdown)

if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)  # Espaçamento visual

# Inserção manual protegida por password
with st.expander("➕ Inserir nova pergunta"):
    nova_pergunta = st.text_input("Nova pergunta")
    nova_resposta = st.text_area("Resposta à pergunta")
    novo_email = st.text_input("Email de contacto (opcional)")
    modelo_email = st.text_area("Modelo de email sugerido (opcional)")
    password = st.text_input("Password de administrador", type="password")

    if st.button("Guardar nova pergunta"):
        if password != PASSWORD_ADMIN:
            st.error("⚠️ Password incorreta.")
        elif not nova_pergunta or not nova_resposta:
            st.warning("⚠️ Preencha a pergunta e a resposta.")
        else:
            guardar_nova_pergunta(nova_pergunta, nova_resposta, novo_email, modelo_email)
            st.success("✅ Pergunta adicionada com sucesso.")
            st.rerun() 

st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
