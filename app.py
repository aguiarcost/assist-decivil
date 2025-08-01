import streamlit as st
import json
import os
from assistente import (
    gerar_resposta,
    carregar_base_conhecimento,
    guardar_base_conhecimento,
    gerar_embeddings,
)

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"

# Página
st.set_page_config(page_title="Felisberto - Assistente ACSUTA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fff3e0; }
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
    .espaco { margin-top: 40px; margin-bottom: 20px; }
    .footer {
        text-align: center;
        color: gray;
        margin-top: 60px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Carregar base de conhecimento
base = carregar_base_conhecimento()
perguntas = sorted([item["pergunta"] for item in base])

# Escolher pergunta
st.subheader("📌 Escolha uma pergunta")
pergunta_escolhida = st.selectbox("Pergunta:", [""] + perguntas)

# Gerar resposta
if pergunta_escolhida:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_escolhida)
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

# Espaço visual
st.markdown("<div class='espaco'></div>", unsafe_allow_html=True)

# Inserir nova pergunta
with st.expander("➕ Inserir nova pergunta"):
    nova_pergunta = st.text_input("Pergunta")
    nova_resposta = st.text_area("Resposta")
    novo_email = st.text_input("Email (opcional)")
    novo_modelo = st.text_area("Modelo de email (opcional)")
    password = st.text_input("Password para gravar", type="password")

    if st.button("💾 Guardar pergunta"):
        if password != "decivil2024":
            st.error("🔒 Password incorreta.")
        elif not nova_pergunta or not nova_resposta:
            st.warning("⚠️ Pergunta e resposta são obrigatórias.")
        else:
            todas = {p["pergunta"]: p for p in base}
            todas[nova_pergunta] = {
                "pergunta": nova_pergunta,
                "resposta": nova_resposta,
                "email": novo_email,
                "modelo_email": novo_modelo
            }
            guardar_base_conhecimento(list(todas.values()))
            gerar_embeddings()
            st.success("✅ Pergunta adicionada com sucesso.")
            st.rerun()

# Espaço visual
st.markdown("<div class='espaco'></div>", unsafe_allow_html=True)

# Editar pergunta existente
with st.expander("✏️ Editar pergunta existente"):
    pergunta_editar = st.selectbox("Escolha uma pergunta para editar", [""] + perguntas)

    if pergunta_editar:
        item = next((p for p in base if p["pergunta"] == pergunta_editar), {})
        with st.form("form_edicao"):
            nova_resposta = st.text_area("Resposta", value=item.get("resposta", ""))
            novo_email = st.text_input("Email (opcional)", value=item.get("email", ""))
            novo_modelo = st.text_area("Modelo de email (opcional)", value=item.get("modelo_email", ""))
            apagar = st.checkbox("🗑️ Apagar esta pergunta")
            password_edit = st.text_input("Password para editar/apagar", type="password")
            submeter = st.form_submit_button("Guardar alterações")

            if submeter:
                if password_edit != "decivil2024":
                    st.error("🔒 Password incorreta.")
                else:
                    if apagar:
                        base = [p for p in base if p["pergunta"] != pergunta_editar]
                        st.success("❌ Pergunta removida.")
                    else:
                        for p in base:
                            if p["pergunta"] == pergunta_editar:
                                p["resposta"] = nova_resposta
                                p["email"] = novo_email
                                p["modelo_email"] = novo_modelo
                        st.success("✅ Alterações guardadas.")
                    guardar_base_conhecimento(base)
                    gerar_embeddings()
                    st.rerun()

# Rodapé
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
