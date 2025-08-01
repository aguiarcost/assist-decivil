import streamlit as st
import json
import os
from datetime import datetime
from assistente import gerar_resposta, carregar_base_conhecimento, guardar_base_conhecimento

# Caminhos
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"
PASSWORD_ADMIN = "decivil2024"

# Layout da página
st.set_page_config(page_title="Felisberto — Assistente ACSUTA", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #fff3e0;
    }
    .titulo-container {
        display: flex;
        align-items: center;
        gap: 10px;
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
    .spacer {
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

# Função auxiliar
def guardar_pergunta_no_historico(pergunta):
    registo = {"pergunta": pergunta, "timestamp": datetime.now().isoformat()}
    if os.path.exists(CAMINHO_HISTORICO):
        try:
            with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as f:
                historico = json.load(f)
        except json.JSONDecodeError:
            historico = []
    else:
        historico = []
    historico.append(registo)
    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

# Carregar base
base_conhecimento = carregar_base_conhecimento()
perguntas = sorted(p["pergunta"] for p in base_conhecimento)

# Interface de seleção
pergunta_escolhida = st.selectbox("❓ Escolha uma pergunta", [""] + perguntas)

resposta = ""
if pergunta_escolhida:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_escolhida)
        guardar_pergunta_no_historico(pergunta_escolhida)

if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

# Espaço visual
st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# Expander para inserir nova pergunta
with st.expander("➕ Inserir nova pergunta manualmente"):
    nova_pergunta = st.text_input("Nova pergunta")
    nova_resposta = st.text_area("Resposta à pergunta")
    novo_email = st.text_input("Email (opcional)")
    novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
    password = st.text_input("Palavra-passe de edição", type="password")

    if st.button("Guardar pergunta"):
        if not nova_pergunta or not nova_resposta:
            st.warning("⚠️ A pergunta e a resposta são obrigatórias.")
        elif password != PASSWORD_ADMIN:
            st.error("❌ Palavra-passe incorreta.")
        else:
            perguntas_existentes = {p["pergunta"]: p for p in base_conhecimento}
            perguntas_existentes[nova_pergunta] = {
                "pergunta": nova_pergunta,
                "resposta": nova_resposta,
                "email": novo_email.strip(),
                "modelo_email": novo_modelo.strip()
            }
            guardar_base_conhecimento(list(perguntas_existentes.values()))
            st.success("✅ Nova pergunta adicionada com sucesso. Atualize a página para ver no menu.")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
