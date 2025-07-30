import streamlit as st
import json
import os
import openai
from assistente import gerar_resposta
from gerar_embeddings import main as gerar_embeddings
from datetime import datetime

# Caminhos
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"

# Configuração da página
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

# Estilo
st.markdown("""
    <style>
    .stApp {
        background-color: #fff3e0;
    }
    .titulo-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 30px;
    }
    .titulo-container img {
        width: 70px;
        height: auto;
    }
    .titulo-container h1 {
        color: #ef6c00;
        font-size: 2em;
        margin: 0;
    }
    .footer {
        text-align: center;
        color: gray;
        margin-top: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho com avatar
st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Carregar base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Guardar histórico
def guardar_pergunta_no_historico(pergunta):
    registo = {"pergunta": pergunta, "timestamp": datetime.now().isoformat()}
    historico = []
    if os.path.exists(CAMINHO_HISTORICO):
        try:
            with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as f:
                historico = json.load(f)
        except json.JSONDecodeError:
            pass
    historico.append(registo)
    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

# API Key
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
elif os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    st.warning("⚠️ A chave da API não está definida.")

# Interface
base_conhecimento = carregar_base_conhecimento()
perguntas_existentes = sorted({p["pergunta"] for p in base_conhecimento})

col1, col2 = st.columns(2)
with col1:
    pergunta_dropdown = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas_existentes)
with col2:
    pergunta_manual = st.text_input("Ou escreva a sua pergunta:")

pergunta_final = pergunta_manual.strip() if pergunta_manual.strip() else pergunta_dropdown

resposta = ""
if pergunta_final:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_final)
        guardar_pergunta_no_historico(pergunta_final)

if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

# Upload de novas perguntas
st.markdown("---")
st.subheader("📤 Atualizar base de conhecimento")
novo_json = st.file_uploader("Carregar ficheiro JSON com novas perguntas", type="json")
if novo_json:
    try:
        novas_perguntas = json.load(novo_json)
        if isinstance(novas_perguntas, list):
            base_existente = carregar_base_conhecimento()
            todas = {p["pergunta"]: p for p in base_existente}
            for nova in novas_perguntas:
                todas[nova["pergunta"]] = nova
            with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
                json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
            gerar_embeddings()  # Atualiza embeddings
            st.success("✅ Base de conhecimento atualizada.")
            st.rerun()
        else:
            st.error("❌ O ficheiro JSON deve conter uma lista de perguntas.")
    except Exception as e:
        st.error(f"❌ Erro ao ler ficheiro: {e}")

# Rodapé
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
