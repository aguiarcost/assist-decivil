import streamlit as st
from assistente import (
    gerar_resposta,
    guardar_nova_pergunta,
    carregar_base_conhecimento,
    atualizar_pergunta,
)
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Felisberto – Assistente ACSUTA", layout="centered")

st.markdown("## 🤖 Felisberto – Assistente Administrativo")
st.markdown("---")

# Base de conhecimento
perguntas = carregar_base_conhecimento()
perguntas_ordenadas = sorted(perguntas, key=lambda x: x["pergunta"])

# Dropdown
pergunta_selecionada = st.selectbox(
    "Escolha uma pergunta frequente:",
    [""] + [p["pergunta"] for p in perguntas_ordenadas]
)

resposta = ""
if pergunta_selecionada:
    resposta = gerar_resposta(pergunta_selecionada)

if resposta:
    st.markdown("### 💡 Resposta")
    st.markdown(resposta, unsafe_allow_html=True)
    st.markdown("---")

# Inserir nova pergunta (formulário condicionado por botão)
with st.expander("➕ Inserir nova pergunta"):
    with st.form("form_nova_pergunta"):
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta")
        novo_email = st.text_input("Email (opcional)")
        novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
        password_input = st.text_input("Palavra-passe de administrador", type="password")
        submitted = st.form_submit_button("Guardar")
        if submitted:
            if password_input != os.getenv("ADMIN_PASSWORD"):
                st.error("❌ Palavra-passe incorreta.")
            elif not nova_pergunta or not nova_resposta:
                st.warning("⚠️ Preencha pelo menos a pergunta e a resposta.")
            else:
                guardar_nova_pergunta(nova_pergunta, nova_resposta, novo_email, novo_modelo)
                st.success("✅ Pergunta adicionada com sucesso. Recarregue a página.")
                st.stop()

# Editar pergunta existente
with st.expander("✏️ Editar pergunta existente"):
    perguntas_dict = {p["pergunta"]: p for p in perguntas_ordenadas}
    pergunta_editar = st.selectbox("Selecionar pergunta", [""] + list(perguntas_dict.keys()))
    if pergunta_editar:
        dados = perguntas_dict[pergunta_editar]
        with st.form("form_editar_pergunta"):
            nova_pergunta_edit = st.text_input("Pergunta", value=dados["pergunta"])
            nova_resposta_edit = st.text_area("Resposta", value=dados["resposta"])
            novo_email_edit = st.text_input("Email (opcional)", value=dados.get("email", ""))
            novo_modelo_edit = st.text_area("Modelo de email sugerido (opcional)", value=dados.get("modelo_email", ""))
            password_input = st.text_input("Palavra-passe de administrador", type="password")
            submitted = st.form_submit_button("Atualizar")
            if submitted:
                if password_input != os.getenv("ADMIN_PASSWORD"):
                    st.error("❌ Palavra-passe incorreta.")
                else:
                    atualizar_pergunta(dados["id"], {
                        "pergunta": nova_pergunta_edit,
                        "resposta": nova_resposta_edit,
                        "email": novo_email_edit,
                        "modelo_email": novo_modelo_edit
                    })
                    st.success("✅ Pergunta atualizada com sucesso. Recarregue a página.")
                    st.stop()
