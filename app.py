import streamlit as st
import os
from assistente import (
    carregar_base_conhecimento,
    gerar_resposta,
    adicionar_ou_editar_pergunta
)

# Título e estilo
st.set_page_config(page_title="Felisberto - Assistente ACSUTA", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #fff3e0; }
    .titulo-container {
        display: flex; align-items: center; gap: 10px;
        margin-top: 10px; margin-bottom: 30px;
    }
    .titulo-container img {
        width: 70px; height: auto;
    }
    .titulo-container h1 {
        color: #ef6c00; font-size: 2em; margin: 0;
    }
    .resposta-box {
        background-color: #fff; padding: 1em;
        border: 1px solid #ddd; border-radius: 8px;
        margin-bottom: 40px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Carregar base de conhecimento
base = carregar_base_conhecimento()
perguntas_disponiveis = sorted([p["pergunta"] for p in base])

# Escolha da pergunta
pergunta_selecionada = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas_disponiveis)

# Geração de resposta
if pergunta_selecionada:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_selecionada)
        st.markdown("### 💡 Resposta do assistente", unsafe_allow_html=True)
        st.markdown(f"<div class='resposta-box'>{resposta}</div>", unsafe_allow_html=True)

# Formulário de inserção/edição
with st.expander("➕ Inserir nova ou editar pergunta"):
    st.markdown("Preencha os dados abaixo. Se a pergunta já existir, será atualizada.")
    pergunta_nova = st.text_input("Pergunta", key="nova_pergunta")
    resposta_nova = st.text_area("Resposta", key="nova_resposta")
    email_novo = st.text_input("Email de contacto (opcional)", key="novo_email")
    modelo_novo = st.text_area("Modelo de email sugerido (opcional)", key="modelo_novo")
    password = st.text_input("Password para guardar", type="password")

    if st.button("Guardar pergunta"):
        if not pergunta_nova or not resposta_nova:
            st.warning("⚠️ Preencha pelo menos a pergunta e a resposta.")
        else:
            sucesso, msg = adicionar_ou_editar_pergunta(
                pergunta_nova.strip(),
                resposta_nova.strip(),
                email_novo.strip(),
                modelo_novo.strip(),
                password.strip()
            )
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

# Rodapé
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
