import streamlit as st
from assistente import (
    gerar_resposta,
    carregar_perguntas,
    adicionar_pergunta,
    atualizar_pergunta,
)
import os

st.set_page_config("Felisberto - Assistente Administrativo", layout="centered")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

st.markdown("# 🤖 Felisberto, Assistente Administrativo")
st.markdown("Faça uma pergunta ou selecione uma das existentes:")

# Mostrar perguntas no dropdown
perguntas_existentes = [p["pergunta"] for p in carregar_perguntas()]
pergunta_selecionada = st.selectbox("Perguntas frequentes", [""] + perguntas_existentes)

resposta = ""
if pergunta_selecionada:
    resposta = gerar_resposta(pergunta_selecionada)

if resposta:
    st.markdown("## 💡 Resposta")
    st.markdown(resposta, unsafe_allow_html=True)
    st.markdown("---")

# Espaçamento entre resposta e inserção
st.markdown("")

# Inserção ou edição de pergunta (com password)
with st.expander("➕ Inserir ou editar pergunta"):
    modo = st.radio("Modo", ["Nova pergunta", "Editar pergunta"], horizontal=True)
    if modo == "Nova pergunta":
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta")
        novo_email = st.text_input("Email de contacto (opcional)")
        novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
        form_password = st.text_input("Password de administrador", type="password")
        if st.button("Guardar nova pergunta"):
            if form_password == ADMIN_PASSWORD:
                if nova_pergunta and nova_resposta:
                    sucesso = adicionar_pergunta(nova_pergunta, nova_resposta, novo_email, novo_modelo)
                    if sucesso:
                        st.success("✅ Pergunta adicionada com sucesso.")
                        st.rerun()
                    else:
                        st.warning("⚠️ Esta pergunta já existe.")
                else:
                    st.warning("⚠️ Preencha a pergunta e a resposta.")
            else:
                st.error("🔒 Password incorreta.")

    else:
        pergunta_a_editar = st.selectbox("Selecionar pergunta para editar", perguntas_existentes)
        pergunta_original = next(p for p in carregar_perguntas() if p["pergunta"] == pergunta_a_editar)
        nova_resposta = st.text_area("Nova resposta", value=pergunta_original["resposta"])
        novo_email = st.text_input("Novo email (opcional)", value=pergunta_original.get("email", ""))
        novo_modelo = st.text_area("Novo modelo de email (opcional)", value=pergunta_original.get("modelo_email", ""))
        form_password = st.text_input("Password de administrador", type="password")
        if st.button("Atualizar pergunta"):
            if form_password == ADMIN_PASSWORD:
                atualizar_pergunta(pergunta_a_editar, nova_resposta, novo_email, novo_modelo)
                st.success("✅ Pergunta atualizada com sucesso.")
                st.rerun()
            else:
                st.error("🔒 Password incorreta.")
