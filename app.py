import streamlit as st
from assistente import gerar_resposta
from preparar_documentos_streamlit import processar_documento

st.set_page_config(page_title="Assistente DECivil", page_icon="📘")

st.title("💬 Assistente DECivil")
st.write("Coloque aqui a sua dúvida relacionada com tarefas administrativas:")

# Campo para pergunta
pergunta = st.text_input("Pergunta:")

# Upload de documentos diversos
st.write("\n**📌 Carregar documentos adicionais (PDF, DOCX, TXT):**")
uploaded_files = st.file_uploader(
    "Seleciona um ou mais ficheiros", 
    type=["pdf", "docx", "txt"], 
    accept_multiple_files=True
)

# Processar documentos
if uploaded_files:
    for uploaded_file in uploaded_files:
        processar_documento(uploaded_file)
    st.success("📄 Documentos processados com sucesso!")

# Campo para colar link de website
st.write("\n**🌐 Adicionar conteúdo de uma página web (URL):**")
url = st.text_input("Introduz o link da página:")

if url:
    try:
        processar_documento(url)
        st.success("🌍 Conteúdo do website processado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao processar o site: {e}")

# Gerar resposta
if pergunta:
    with st.spinner("A pensar na melhor resposta..."):
        try:
            resposta = gerar_resposta(pergunta)
            st.markdown("### 🧐 Resposta:")
            st.markdown(resposta)
        except Exception as e:
            st.error(f"❌ Ocorreu um erro: {e}")
