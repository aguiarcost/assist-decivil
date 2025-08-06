import streamlit as st
from assistente import (
    carregar_base_conhecimento,
    guardar_base_conhecimento,
    editar_base_conhecimento,
    gerar_resposta,
    gerar_embedding
)

st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

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
    .footer {
        text-align: center; color: gray; margin-top: 50px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Base de conhecimento
perguntas = carregar_base_conhecimento()
perguntas_opcoes = [p["pergunta"] for p in perguntas]

# Escolher pergunta
pergunta_selecionada = st.selectbox("Escolha uma pergunta:", [""] + perguntas_opcoes)
resposta = ""
if pergunta_selecionada:
    resposta = gerar_resposta(pergunta_selecionada)

if resposta:
    st.markdown("----")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

# Espaço extra
st.markdown("<br><br>", unsafe_allow_html=True)

# Inserir nova pergunta
with st.expander("➕ Inserir nova pergunta"):
    with st.form("form_nova"):
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta")
        novo_email = st.text_input("Email (opcional)")
        novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
        password = st.text_input("Password de administrador", type="password")
        submeter = st.form_submit_button("Guardar")

        if submeter:
            if password != st.secrets["ADMIN_PASSWORD"]:
                st.error("❌ Password inválida.")
            elif not nova_pergunta or not nova_resposta:
                st.warning("⚠️ Pergunta e resposta são obrigatórias.")
            else:
                try:
                    novo_item = {
                        "pergunta": nova_pergunta,
                        "resposta": nova_resposta,
                        "email": novo_email,
                        "modelo_email": novo_modelo,
                        "embedding": gerar_embedding(nova_pergunta)
                    }
                    guardar_base_conhecimento([novo_item])
                    st.success("✅ Pergunta adicionada com sucesso.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar pergunta: {e}")

# Editar pergunta existente
with st.expander("✏️ Editar pergunta existente"):
    pergunta_a_editar = st.selectbox("Selecionar pergunta para editar", [""] + perguntas_opcoes)
    if pergunta_a_editar:
        pergunta_obj = next((p for p in perguntas if p["pergunta"] == pergunta_a_editar), {})
        with st.form("form_editar"):
            nova_resposta = st.text_area("Nova resposta", value=pergunta_obj.get("resposta", ""))
            novo_email = st.text_input("Novo email", value=pergunta_obj.get("email", ""))
            novo_modelo = st.text_area("Novo modelo de email", value=pergunta_obj.get("modelo_email", ""))
            password_editar = st.text_input("Password de administrador", type="password")
            submeter_edicao = st.form_submit_button("Guardar alterações")
            if submeter_edicao:
                if password_editar != st.secrets["ADMIN_PASSWORD"]:
                    st.error("❌ Password inválida.")
                else:
                    try:
                        novo_item = {
                            "resposta": nova_resposta,
                            "email": novo_email,
                            "modelo_email": novo_modelo
                        }
                        editar_base_conhecimento(pergunta_a_editar, novo_item)
                        st.success("✅ Pergunta editada com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao editar pergunta: {e}")

st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
