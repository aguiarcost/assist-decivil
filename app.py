import streamlit as st
from assistente import gerar_resposta
from preparar_documentos_streamlit import preparar_documentos

with st.expander("⚙️ Gerar base de documentos PDF"):
    if st.button("🔄 Preparar documentos agora"):
        total = preparar_documentos()
        st.success(f"{total} blocos vetorizados com sucesso.")

st.set_page_config(page_title="Assistente DECivil", page_icon="🏛️")
st.title("💬 Assistente DECivil")
st.write("Coloque aqui a sua dúvida relacionada com tarefas administrativas no DECivil.")

st.info("💡 Sugestão: pode escrever 'quero reservar uma sala', 'preciso de uma declaração' ou 'o que sabes fazer?'")

# Bloco com exemplos úteis para quem abre a app
with st.expander("📌 Exemplos de perguntas que pode fazer"):
    st.markdown("""
- Como reservo uma sala?
- Onde pedir estacionamento?
- Quem trata do Wi-Fi para reuniões?
- Como registo um convidado externo?
- A quem peço uma declaração?
- O que sabes fazer?
""")

# Campo de entrada da pergunta
pergunta = st.text_input("❓ Escreva a sua pergunta:")

# Processa e mostra a resposta
if pergunta:
    try:
        resposta = gerar_resposta(pergunta)
        st.markdown("### ✅ Resposta:")
        st.markdown(resposta)
    except Exception as e:
        st.error(f"❌ Ocorreu um erro: {e}")
