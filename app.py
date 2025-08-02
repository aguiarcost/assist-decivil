import streamlit as st
from assistente import (
    gerar_resposta,
    listar_perguntas,
    inserir_ou_atualizar_pergunta,
    obter_pergunta_por_texto,
    PASSWORD_CORRETA,
)

st.set_page_config(page_title="Felisberto – Assistente ACSUTA", layout="wide")

# Título
st.markdown("""
    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px;'>
        <img src='https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png' width='60'/>
        <h1 style='color:#ef6c00'>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Perguntas disponíveis
perguntas = listar_perguntas()
pergunta_selecionada = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas)

resposta = ""
if pergunta_selecionada:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_selecionada)

if resposta:
    st.markdown("### 💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

st.markdown("---")

# Expansor para inserir nova pergunta
with st.expander("➕ Inserir nova pergunta"):
    nova_pergunta = st.text_input("Pergunta")
    nova_resposta = st.text_area("Resposta")
    novo_email = st.text_input("Email de contacto (opcional)")
    novo_modelo_email = st.text_area("Modelo de email sugerido (opcional)")
    password = st.text_input("Password para guardar", type="password")

    if st.button("Guardar nova pergunta"):
        if password != PASSWORD_CORRETA:
            st.error("❌ Password incorreta.")
        elif not nova_pergunta or not nova_resposta:
            st.warning("⚠️ Pergunta e resposta são obrigatórias.")
        else:
            inserir_ou_atualizar_pergunta(nova_pergunta, nova_resposta, novo_email, novo_modelo_email)
            st.success("✅ Pergunta adicionada com sucesso.")
            st.rerun()

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# Expansor para editar pergunta existente
with st.expander("✏️ Editar pergunta existente"):
    pergunta_a_editar = st.selectbox("Selecionar pergunta a editar", [""] + perguntas, key="edit_selector")

    if pergunta_a_editar:
        dados_existentes = obter_pergunta_por_texto(pergunta_a_editar)
        texto_edit = st.text_input("Pergunta", value=dados_existentes.get("pergunta", ""), key="edit_pergunta")
        resposta_edit = st.text_area("Resposta", value=dados_existentes.get("resposta", ""), key="edit_resposta")
        email_edit = st.text_input("Email de contacto (opcional)", value=dados_existentes.get("email", ""), key="edit_email")
        modelo_email_edit = st.text_area("Modelo de email sugerido (opcional)", value=dados_existentes.get("modelo_email", ""), key="edit_modelo")
        password_edit = st.text_input("Password para editar", type="password", key="edit_password")

        if st.button("Guardar alterações"):
            if password_edit != PASSWORD_CORRETA:
                st.error("❌ Password incorreta.")
            elif not texto_edit or not resposta_edit:
                st.warning("⚠️ Pergunta e resposta são obrigatórias.")
            else:
                inserir_ou_atualizar_pergunta(texto_edit, resposta_edit, email_edit, modelo_email_edit)
                st.success("✅ Pergunta atualizada com sucesso.")
                st.rerun()

# Rodapé
st.markdown("<br><div style='text-align: center; color: gray;'>© 2025 AAC</div>", unsafe_allow_html=True)
