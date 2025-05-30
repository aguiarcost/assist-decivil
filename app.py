import streamlit as st
from assistente import gerar_resposta
from preparar_documentos_streamlit import processar_documentos
import json

st.set_page_config(page_title="Assistente DECivil", page_icon="📘")
st.title("💬 Assistente DECivil")
st.write("Coloque aqui a sua dúvida ou selecione uma pergunta da lista:")

# Carregar perguntas da base de conhecimento
try:
    with open("base_conhecimento.json", "r", encoding="utf-8") as f:
        base_manual = json.load(f)
    perguntas_sugeridas = [item["pergunta"] for item in base_manual]
except:
    perguntas_sugeridas = []

# Dropdown com perguntas da base
pergunta_selecionada = st.selectbox("🔽 Perguntas frequentes:", [""] + perguntas_sugeridas)

# Campo de input livre
pergunta_livre = st.text_input("✍️ Ou escreva a sua pergunta:")

# Escolher qual pergunta usar
pergunta_final = pergunta_livre or pergunta_selecionada

# Upload de documentos
st.write("\n**📎 Carregar documentos adicionais (PDF, DOCX, TXT):**")
uploaded_files = st.file_uploader(
    "Seleciona um ou mais ficheiros", 
    type=["pdf", "docx", "txt"], 
    accept_multiple_files=True
)

if uploaded_files:
    for f in uploaded_files:
        processar_documentos(f)
    st.success("Documentos processados com sucesso!")

# Gerar resposta
if pergunta_final:
    with st.spinner("A pensar na melhor resposta..."):
        try:
            resposta = gerar_resposta(pergunta_final)
            st.markdown("### 🧐 Resposta:")
            st.markdown(resposta)
        except Exception as e:
            st.error(f"❌ Ocorreu um erro: {e}")

