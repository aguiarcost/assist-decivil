import streamlit as st
from assistente import gerar_resposta, carregar_base_conhecimento, guardar_base_conhecimento
from gerar_embeddings import main as gerar_embeddings
import datetime

# Configuração da página
st.set_page_config(page_title="Felisberto - Assistente ACSUTA", layout="wide")

st.markdown(
    """
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
    .spacer {
        margin: 40px 0;
    }
    .footer {
        text-align: center;
        color: gray;
        margin-top: 50px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Cabeçalho
st.markdown(
    """
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Carregamento base
base = carregar_base_conhecimento()
perguntas = sorted([p["pergunta"] for p in base])

# Dropdown
pergunta_escolhida = st.selectbox("📌 Escolha uma pergunta:", [""] + perguntas)

# Resposta
if pergunta_escolhida:
    resposta = gerar_resposta(pergunta_escolhida)
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# Inserção manual com password
if st.button("➕ Inserir nova pergunta"):
    st.session_state["mostrar_nova"] = True

if st.session_state.get("mostrar_nova", False):
    st.markdown("### 📝 Nova Pergunta")
    with st.form("nova_pergunta_form"):
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta")
        novo_email = st.text_input("Email (opcional)")
        novo_modelo = st.text_area("Modelo de email (opcional)")
        password = st.text_input("Password", type="password")
        submeter = st.form_submit_button("Guardar")

        if submeter:
            if password != "decivil2024":
                st.error("🔒 Password incorreta.")
            elif not nova_pergunta or not nova_resposta:
                st.warning("❗ A pergunta e a resposta são obrigatórias.")
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
                st.session_state["mostrar_nova"] = False
                st.rerun()

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# Secção de edição
st.markdown("## ✏️ Editar pergunta existente")
pergunta_editar = st.selectbox("Selecione a pergunta a editar:", [""] + perguntas, key="editar_pergunta")

if pergunta_editar:
    item = next((p for p in base if p["pergunta"] == pergunta_editar), None)
    if item:
        with st.form("form_edicao"):
            nova_resposta = st.text_area("Resposta", value=item.get("resposta", ""))
            novo_email = st.text_input("Email (opcional)", value=item.get("email", ""))
            novo_modelo = st.text_area("Modelo de email (opcional)", value=item.get("modelo_email", ""))
            apagar = st.checkbox("🗑️ Apagar esta pergunta")
            submeter = st.form_submit_button("Guardar alterações")

            if submeter:
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

st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
