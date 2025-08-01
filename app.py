import streamlit as st
import json
from datetime import datetime
from assistente import (
    gerar_resposta,
    carregar_base_conhecimento,
    guardar_base_conhecimento,
    editar_pergunta,
    apagar_pergunta,
)

# Constantes
PASSWORD_CORRETA = "decivil2024"

# Configuração da página
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

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
        margin-top: 80px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Carregar base
base_conhecimento = carregar_base_conhecimento()
perguntas = sorted([p["pergunta"] for p in base_conhecimento])

# Interface principal
st.subheader("❓ Fazer uma pergunta")
pergunta_final = st.selectbox("Escolha uma pergunta:", [""] + perguntas)

resposta = ""
if pergunta_final:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_final)

if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(f"<div style='margin-bottom: 40px;'>{resposta}</div>", unsafe_allow_html=True)

# Inserir nova pergunta
st.markdown("---")
if st.button("➕ Inserir nova pergunta"):
    st.session_state.mostrar_formulario = True

if st.session_state.get("mostrar_formulario"):
    st.subheader("Adicionar nova pergunta")
    with st.form("form_nova"):
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta")
        novo_email = st.text_input("Email de contacto (opcional)")
        novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
        password = st.text_input("Password de segurança", type="password")
        submitted = st.form_submit_button("Guardar")
        if submitted:
            if password != PASSWORD_CORRETA:
                st.error("⚠️ Password incorreta.")
            elif not nova_pergunta or not nova_resposta:
                st.warning("⚠️ Preencha pelo menos a pergunta e a resposta.")
            else:
                base = carregar_base_conhecimento()
                todas = {p["pergunta"]: p for p in base}
                todas[nova_pergunta] = {
                    "pergunta": nova_pergunta,
                    "resposta": nova_resposta,
                    "email": novo_email,
                    "modelo_email": novo_modelo,
                }
                guardar_base_conhecimento(list(todas.values()))
                st.success("✅ Pergunta adicionada com sucesso.")
                st.session_state.mostrar_formulario = False
                st.rerun()

# Edição e eliminação
st.markdown("---")
with st.expander("🛠️ Editar ou remover perguntas existentes"):
    for item in base_conhecimento:
        with st.expander(f"✏️ {item['pergunta']}"):
            with st.form(f"edit_{item['pergunta']}"):
                nova_pergunta = st.text_input("Pergunta", value=item["pergunta"])
                nova_resposta = st.text_area("Resposta", value=item["resposta"])
                novo_email = st.text_input("Email", value=item.get("email", ""))
                novo_modelo = st.text_area("Modelo de email", value=item.get("modelo_email", ""))
                password = st.text_input("Password", type="password")
                col_a, col_b = st.columns(2)
                with col_a:
                    atualizar = st.form_submit_button("💾 Atualizar")
                with col_b:
                    eliminar = st.form_submit_button("🗑️ Apagar")

                if atualizar:
                    if password != PASSWORD_CORRETA:
                        st.error("❌ Password incorreta.")
                    else:
                        editar_pergunta(item["pergunta"], nova_pergunta, nova_resposta, novo_email, novo_modelo)
                        st.success("✅ Pergunta atualizada.")
                        st.rerun()
                elif eliminar:
                    if password != PASSWORD_CORRETA:
                        st.error("❌ Password incorreta.")
                    else:
                        apagar_pergunta(item["pergunta"])
                        st.success("✅ Pergunta removida.")
                        st.rerun()

# Rodapé
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
