import streamlit as st
from assistente import (
    carregar_base_conhecimento,
    gerar_resposta,
    adicionar_pergunta_supabase,
    atualizar_pergunta_supabase,
)

st.set_page_config(page_title="Felisberto, Assistente ACSUTA", layout="wide")

# Estilo (mantido, mas limpo)
st.markdown("""
    <style>
    /* [Estilo original mantido] */
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache por 5 min
def get_perguntas_ordenadas():
    perguntas = carregar_base_conhecimento()
    return sorted([p["pergunta"] for p in perguntas])

perguntas_ordenadas = get_perguntas_ordenadas()

st.markdown("## ❓ Perguntas Frequentes")

pergunta_selecionada = st.selectbox("Escolha uma pergunta:", [""] + perguntas_ordenadas)

if pergunta_selecionada:
    resposta = gerar_resposta(pergunta_selecionada)
    st.markdown("### 💬 Resposta")
    st.markdown(resposta, unsafe_allow_html=True)

st.markdown("---")
st.markdown("## ➕ Inserir nova pergunta")

with st.expander("Adicionar nova pergunta"):
    nova_pergunta = st.text_input("Pergunta")
    nova_resposta = st.text_area("Resposta")
    novo_email = st.text_input("Email de contacto (opcional)")
    novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
    password = st.text_input("Password de administrador", type="password")
    if st.button("Guardar nova pergunta"):
        if not nova_pergunta or not nova_resposta:
            st.warning("⚠️ Pergunta e resposta são obrigatórias.")
        else:
            sucesso = adicionar_pergunta_supabase(nova_pergunta, nova_resposta, novo_email, novo_modelo, password)
            if sucesso:
                st.success("✅ Nova pergunta adicionada com sucesso.")
                st.cache_data.clear()  # Limpa cache
            else:
                st.error("❌ Password incorreta ou erro ao adicionar.")

# [Seção de edição similar, com hash check via função]

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
