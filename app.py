import streamlit as st
from assistente import gerar_resposta
from preparar_documentos_streamlit import processar_pdf

st.set_page_config(page_title="Assistente DECivil", page_icon="💬")

st.title("💬 Assistente DECivil")
st.write("Coloque aqui a sua dúvida relacionada com pedidos administrativos ou documentos disponíveis:")

# Expansor com sugestões de perguntas
with st.expander("📌 Exemplos de perguntas que pode fazer"):
    st.markdown("""
- Como reservo uma sala?
- Onde pedir estacionamento?
- Quem trata do Wi-Fi para reuniões?
- Como registar um convidado externo?
- A quem peço uma declaração?
- O que sabes fazer?
""")

# Expansor para carregar e processar novos documentos PDF
with st.expander("📥 Adicionar novo documento PDF"):
    uploaded_file = st.file_uploader("Carrega um PDF para adicionar à base de conhecimento", type="pdf")
    if uploaded_file is not None:
        if st.button("🔄 Processar documento"):
            num_paginas = processar_pdf(uploaded_file)
            st.success(f"✅ Documento processado com sucesso ({num_paginas} páginas vetorizadas).")

# Campo de pergunta
pergunta = st.text_input("Pergunta:")

# Geração da resposta
if pergunta:
    resposta = gerar_resposta(pergunta)
    st.markdown("### 📌 Resposta:")
    st.markdown(resposta)
