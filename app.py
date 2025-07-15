import streamlit as st
import json
import os
import openai
from assistente import gerar_resposta
from preparar_documentos_streamlit import processar_documento
from datetime import datetime

# Inicialização de variáveis
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"

# Chave da API (ambiente ou local)
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
elif os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    st.warning("⚠️ A chave da API não está definida.")

# Função auxiliar: carregar base de conhecimento
@st.cache_data
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Função auxiliar: guardar histórico
def guardar_pergunta_no_historico(pergunta):
    registo = {"pergunta": pergunta, "timestamp": datetime.now().isoformat()}
    if os.path.exists(CAMINHO_HISTORICO):
        try:
            with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as f:
                historico = json.load(f)
        except json.JSONDecodeError:
            historico = []
    else:
        historico = []
    historico.append(registo)
    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

# Interface
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background-color: #fff3e0;
    }
    </style>
""", unsafe_allow_html=True)

# Título com imagem ao lado
col_avatar, col_titulo = st.columns([1, 8])
with col_avatar:
    st.image("felisberto_avatar.png", width=80)
with col_titulo:
    st.markdown("# Felisberto, Assistente Administrativo ACSUTA")
