import streamlit as st
from assistente import (
    carregar_base_conhecimento,
    guardar_base_conhecimento,
    gerar_resposta
)

# Configurar página
st.set_page_config(page_title="Felisberto, Assistente ACSUTA", layout="wide")

# Estilo visual
st.markdown("""
    <style>
    .stApp { background-color: #fff3e0; }
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

# Cabeçalho com avatar
st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Carregar base de conhecimento
if "perguntas" not in st.session_state:
    st.session_state.perguntas = carregar_base_conhecimento()

# Dropdown com perguntas existentes
perguntas_existentes = sorted([p["pergunta"] for p in st.session_state.perguntas])
pergunta_selecionada = st.selectbox("Escolha uma pergunta existente:", [""] + perguntas_existentes)

# Gerar resposta
resposta = ""
if pergunta_selecionada:
    resposta = gerar_resposta(pergunta_selecionada)

# Apresentar resposta
if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Expander para adicionar nova OU editar existente
with st.expander("✏️ Adicionar ou editar pergunta existente"):
    form_selecao = st.selectbox("Selecionar pergunta para editar (ou deixe em branco para nova):", [""] + perguntas_existentes)
    
    if form_selecao:
        pergunta_alvo = next((p for p in st.session_state.perguntas if p["pergunta"] == form_selecao), None)
        form_pergunta = st.text_input("Pergunta", value=pergunta_alvo["pergunta"])
        form_resposta = st.text_area("Resposta", value=pergunta_alvo["resposta"])
        form_email = st.text_input("Email (opcional)", value=pergunta_alvo.get("email", ""))
        form_modelo = st.text_area("Modelo de email sugerido (opcional)", value=pergunta_alvo.get("modelo_email", ""))
    else:
        form_pergunta = st.text_input("Pergunta")
        form_resposta = st.text_area("Resposta")
        form_email = st.text_input("Email (opcional)")
        form_modelo = st.text_area("Modelo de email sugerido (opcional)")

    form_password = st.text_input("Password", type="password")

    if st.button("💾 Guardar"):
        if form_password != "decivil2024":
            st.error("❌ Password inválida.")
        elif not form_pergunta or not form_resposta:
            st.warning("⚠️ Preencha pelo menos a pergunta e a resposta.")
        else:
            nova = {
                "pergunta": form_pergunta.strip(),
                "resposta": form_resposta.strip(),
                "email": form_email.strip(),
                "modelo_email": form_modelo.strip()
            }
            guardar_base_conhecimento(nova)
            st.session_state.perguntas = carregar_base_conhecimento()
            st.success("✅ Pergunta guardada com sucesso!")

# Rodapé
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
