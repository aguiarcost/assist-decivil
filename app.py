import streamlit as st
from assistente import (
    gerar_resposta,
    listar_perguntas,
    adicionar_ou_atualizar_pergunta,
    obter_pergunta_por_texto,
)
import os

st.set_page_config(page_title="Felisberto", layout="centered")

st.title("🤖 Felisberto, Assistente Administrativo ACSUTA")

st.markdown("---")

# Lista de perguntas para dropdown
perguntas_existentes = listar_perguntas()
pergunta_selecionada = st.selectbox("📌 Escolha uma pergunta:", [""] + perguntas_existentes)

resposta = ""
if pergunta_selecionada:
    resposta = gerar_resposta(pergunta_selecionada)
    if resposta:
        st.markdown("### 💡 Resposta")
        st.markdown(resposta, unsafe_allow_html=True)
        st.markdown("---")

# Toggle para mostrar o formulário de inserção/edição
with st.expander("➕ Inserir ou editar pergunta"):
    st.markdown("⚠️ Esta ação requer password para ser guardada.")
    pergunta_input = st.text_input("Pergunta")
    resposta_input = st.text_area("Resposta")
    email_input = st.text_input("Email (opcional)")
    modelo_input = st.text_area("Modelo de email sugerido (opcional)")
    password = st.text_input("Password", type="password")

    if st.button("💾 Guardar pergunta"):
        if password != os.environ.get("FORM_PASSWORD"):
            st.error("❌ Password incorreta.")
        elif not pergunta_input or not resposta_input:
            st.warning("⚠️ Preencha pelo menos a pergunta e a resposta.")
        else:
            adicionar_ou_atualizar_pergunta(pergunta_input, resposta_input, email_input, modelo_input)
            st.success("✅ Pergunta guardada com sucesso!")
            st.rerun()
