import streamlit as st
import os
from assistente import gerar_resposta, knowledge_data, knowledge_perguntas, knowledge_embeddings, documents_data, documents_embeddings
import json

st.set_page_config(page_title="Assistente Decivil", page_icon="📘")

st.markdown(
    """
    <div style='display: flex; align-items: center;'>
        <img src='https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png' width='60'>
        <h2 style='margin-left: 10px;'>Felisberto — Assistente Decivil</h2>
    </div>
    <hr style='margin-top:10px;'>
    """,
    unsafe_allow_html=True
)

if "historico" not in st.session_state:
    st.session_state.historico = []

pergunta = st.text_input("Coloca a tua pergunta:", placeholder="Ex: Como posso reservar uma sala?")

if st.button("Perguntar") or (pergunta and st.session_state.get("ultima_pergunta") != pergunta):
    st.session_state.ultima_pergunta = pergunta

    with st.spinner("A pensar..."):
        resposta = gerar_resposta(
            pergunta,
            knowledge_data,
            knowledge_perguntas,
            knowledge_embeddings,
            documents_data,
            documents_embeddings
        )
        st.session_state.historico.append((pergunta, resposta))

if st.session_state.historico:
    st.markdown("### Histórico de Perguntas")
    for idx, (q, r) in enumerate(reversed(st.session_state.historico), 1):
        st.markdown(f"**{idx}. Pergunta:** {q}")
        st.markdown(f"**Resposta:** {r}")
        st.markdown("---")

st.markdown("<br><sub>Powered by OpenAI + Streamlit</sub>", unsafe_allow_html=True)