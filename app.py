import streamlit as st
from assistente import gerar_resposta

st.set_page_config(page_title="Assistente DECivil", page_icon="💬")

st.title("💬 Assistente DECivil")
st.write("Coloque aqui a sua dúvida relacionada com pedidos administrativos:")

pergunta = st.text_input("Pergunta:")

if pergunta:
    try:
        resposta = gerar_resposta(pergunta)
        st.markdown("### Resposta:")
        st.markdown(resposta)
    except Exception as e:
        st.error(f"❌ Ocorreu um erro: {str(e)}")
