import streamlit as st
from assistente import (
    gerar_resposta,
    carregar_perguntas,
    adicionar_pergunta,
    atualizar_pergunta,
    ADMIN_PASSWORD
)

st.set_page_config(page_title="Felisberto - Assistente Administrativo", layout="wide")

st.title("📘 Felisberto - Assistente Administrativo")

# Carregar perguntas da base de dados (Supabase)
perguntas_data = carregar_perguntas()
perguntas_existentes = sorted([p["pergunta"] for p in perguntas_data])

# Interface de seleção de pergunta
pergunta_selecionada = st.selectbox("Escolha uma pergunta:", [""] + perguntas_existentes)

# Mostrar resposta se houver pergunta selecionada
if pergunta_selecionada:
    resposta = gerar_resposta(pergunta_selecionada)
    if resposta:
        st.markdown("---")
        st.markdown(f"**Resposta:**\n\n{resposta}", unsafe_allow_html=True)

# Expansor para adicionar nova pergunta
with st.expander("➕ Inserir nova pergunta manualmente"):
    with st.form("form_nova_pergunta"):
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta")
        novo_email = st.text_input("Email de contacto (opcional)")
        novo_modelo_email = st.text_area("Modelo de email sugerido (opcional)")
        password = st.text_input("Password de administrador", type="password")
        submitted = st.form_submit_button("Guardar pergunta")
    
    if submitted:
        if password != ADMIN_PASSWORD:
            st.error("❌ Password incorreta.")
        elif not nova_pergunta or not nova_resposta:
            st.error("❗ A pergunta e a resposta são obrigatórias.")
        else:
            sucesso = adicionar_pergunta(nova_pergunta, nova_resposta, novo_email, novo_modelo_email)
            if sucesso:
                st.success("✅ Pergunta adicionada com sucesso.")
                st.rerun()
            else:
                st.error("❌ Erro ao adicionar pergunta (pode já existir).")

# Expansor para editar perguntas
with st.expander("✏️ Editar pergunta existente"):
    pergunta_editar = st.selectbox("Selecionar pergunta para editar", [""] + perguntas_existentes, key="edit_select")
    if pergunta_editar:
        dados = next((p for p in perguntas_data if p["pergunta"] == pergunta_editar), None)
        if dados:
            with st.form("form_editar_pergunta"):
                nova_resposta_editar = st.text_area("Editar resposta", value=dados.get("resposta", ""))
                novo_email_editar = st.text_input("Editar email (opcional)", value=dados.get("email", ""))
                novo_modelo_editar = st.text_area("Editar modelo de email (opcional)", value=dados.get("modelo_email", ""))
                password_edit = st.text_input("Password de administrador", type="password", key="edit_pass")
                confirmar = st.form_submit_button("Atualizar pergunta")
            
            if confirmar:
                if password_edit != ADMIN_PASSWORD:
                    st.error("❌ Password incorreta.")
                else:
                    sucesso = atualizar_pergunta(
                        pergunta_editar, nova_resposta_editar, novo_email_editar, novo_modelo_editar
                    )
                    if sucesso:
                        st.success("✅ Pergunta atualizada com sucesso.")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao atualizar pergunta.")
