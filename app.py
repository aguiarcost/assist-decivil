import streamlit as st
from assistente import gerar_resposta, carregar_perguntas_frequentes

st.set_page_config(page_title="Assistente DECivil", layout="centered")

# Título
st.markdown("<h1 style='color:#FF914D;'>Assistente DECivil</h1>", unsafe_allow_html=True)
st.write("Escolha uma pergunta frequente ou escreva a sua dúvida:")

# Carregar perguntas frequentes
perguntas = carregar_perguntas_frequentes()
pergunta_escolhida = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas)

# Caixa para escrever pergunta personalizada
pergunta_livre = st.text_input("Ou escreva a sua pergunta:")

# Determinar pergunta final
pergunta_final = pergunta_livre.strip() if pergunta_livre.strip() else pergunta_escolhida

# Mostrar resposta se houver pergunta
if pergunta_final:
    with st.spinner("A pensar..."):
        resposta, modelo_email = gerar_resposta(pergunta_final, usar_embedding=bool(pergunta_livre.strip()))
    if resposta:
        st.markdown("### 💡 Resposta do assistente")
        st.markdown(resposta, unsafe_allow_html=True)
        if modelo_email:
            st.markdown("### 📧 Modelo de email")
            st.code(modelo_email, language="text")
    else:
        st.warning("❌ Não foi possível gerar uma resposta.")

# Rodapé
st.markdown("---")
st.markdown("<small>© 2025 AAC</small>", unsafe_allow_html=True)
