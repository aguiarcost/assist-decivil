import streamlit as st
import json
import os
from assistente import gerar_resposta
from datetime import datetime

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"

st.set_page_config(page_title="Felisberto", layout="wide")

@st.cache_data
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@st.cache_data
def carregar_historico():
    if os.path.exists(CAMINHO_HISTORICO):
        with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_pergunta(pergunta):
    historico = carregar_historico()
    historico.append({"pergunta": pergunta, "timestamp": datetime.now().isoformat()})
    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

base_conhecimento = carregar_base_conhecimento()
perguntas = [p["pergunta"] for p in base_conhecimento]

st.image("felisberto_avatar.png", width=80)
st.markdown("<h1 style='color:#ef6c00; margin-top: -10px;'>Felisberto, Assistente Administrativo</h1>", unsafe_allow_html=True)

opcao = st.selectbox("Escolha uma pergunta:", [""] + perguntas, key="pergunta_box")

if opcao:
    resposta = gerar_resposta(opcao)
    guardar_pergunta(opcao)
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta)

# Rodapé
st.markdown("""
<hr style='margin-top: 50px; margin-bottom: 10px;'>
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    © 2025 AAC
</div>
""", unsafe_allow_html=True)
