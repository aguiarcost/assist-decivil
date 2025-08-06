import streamlit as st
from assistente import (
    carregar_base_conhecimento,
    adicionar_pergunta_supabase,
    atualizar_pergunta_supabase,
)
import os

st.set_page_config(page_title="Felisberto, Assistente ACSUTA", layout="wide")

# Estilo personalizado com avatar e tons laranja
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

# Carregar perguntas da base de conhecimento (Supabase)
perguntas = carregar_base_conhecimento()
perguntas_dict = {p["pergunta"]: p for p in perguntas}
perguntas_ordenadas = sorted(perguntas_dict.keys())

st.markdown("## ❓ Perguntas Frequentes")

# Seleção de pergunta frequente
pergunta_selecionada = st.selectbox("Escolha uma pergunta:", [""] + perguntas_ordenadas)

if pergunta_selecionada:
    # Monta a resposta usando os dados já carregados (evita nova leitura do Supabase)
    dados = perguntas_dict[pergunta_selecionada]
    resposta_texto = dados.get("resposta", "").strip()
    email = dados.get("email", "").strip()
    modelo = dados.get("modelo_email", "").strip()
    if email:
        resposta_texto += f"\n\n📫 **Email de contacto:** {email}"
    if modelo:
        resposta_texto += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo}\n```"
    st.markdown("### 💬 Resposta")
    st.markdown(resposta_texto, unsafe_allow_html=True)

st.markdown("---")
st.markdown("## ➕ Inserir nova pergunta")

# Formulário para adicionar nova pergunta (expansível, requer autenticação)
with st.expander("Adicionar nova pergunta"):
    nova_pergunta = st.text_input("Pergunta")
    nova_resposta = st.text_area("Resposta")
    novo_email = st.text_input("Email de contacto (opcional)")
    novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
    password = st.text_input("Password de administrador", type="password")
    if st.button("Guardar nova pergunta"):
        # Validar campos obrigatórios e password
        if not nova_pergunta or not nova_resposta:
            st.warning("⚠️ Pergunta e resposta são obrigatórias.")
        elif password != os.environ.get("ADMIN_PASSWORD", "decivil2024"):
            st.error("❌ Password incorreta.")
        else:
            sucesso = adicionar_pergunta_supabase(nova_pergunta, nova_resposta, novo_email, novo_modelo)
            if sucesso:
                st.success("✅ Nova pergunta adicionada com sucesso.")
                st.experimental_rerun()  # Reexecuta a aplicação para carregar os dados atualizados
            else:
                st.error("❌ Erro ao adicionar pergunta.")

st.markdown("---")
st.markdown("## ✏️ Editar pergunta existente")

# Formulário para editar pergunta existente (expansível, requer autenticação)
with st.expander("Editar pergunta existente"):
    pergunta_a_editar = st.selectbox("Selecione a pergunta:", [""] + perguntas_ordenadas)
    if pergunta_a_editar:
        # Preencher campos com dados atuais da pergunta selecionada
        dados = perguntas_dict[pergunta_a_editar]
        nova_resposta = st.text_area("Editar resposta", value=dados.get("resposta", ""))
        novo_email = st.text_input("Editar email (opcional)", value=dados.get("email", ""))
        novo_modelo = st.text_area("Editar modelo de email (opcional)", value=dados.get("modelo_email", ""))
        password_edit = st.text_input("Password de administrador", type="password", key="edit_pwd")
        if st.button("Guardar alterações"):
            if password_edit != os.environ.get("ADMIN_PASSWORD", "decivil2024"):
                st.error("❌ Password incorreta.")
            else:
                sucesso = atualizar_pergunta_supabase(pergunta_a_editar, nova_resposta, novo_email, novo_modelo)
                if sucesso:
                    st.success("✅ Pergunta atualizada com sucesso.")
                    st.experimental_rerun()  # Reexecuta a aplicação para carregar os dados atualizados
                else:
                    st.error("❌ Erro ao atualizar pergunta.")

# Rodapé
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
