import streamlit as st
from assistente import gerar_resposta
from preparar_documentos_streamlit import processar_pdf

st.set_page_config(page_title="Assistente DECivil", page_icon="📘")

st.title("💬 Assistente DECivil")
st.write("Coloque aqui a sua dúvida relacionada com tarefas administrativas:")

# Campo para pergunta
pergunta = st.text_input("Pergunta:")

# Campo para upload de documentos
st.write("\n**📌 Carregar documentos adicionais (PDF):**")
uploaded_files = st.file_uploader("Seleciona um ou mais ficheiros PDF", type=["pdf"], accept_multiple_files=True)

# Processar e guardar documentos
if uploaded_files:
    for uploaded_file in uploaded_files:
        processar_pdf(uploaded_file)
    st.success("Documentos processados com sucesso!")

# Gerar resposta
if pergunta:
    with st.spinner("A pensar na melhor resposta..."):
        try:
            resposta = gerar_resposta(pergunta)
            st.markdown("### 🧐 Resposta:")
            st.markdown(resposta)
        except Exception as e:
            st.error(f"❌ Ocorreu um erro: {e}")
