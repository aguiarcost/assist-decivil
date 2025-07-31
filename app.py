import streamlit as st
import json
import os
from assistente import gerar_resposta
from gerar_embeddings import main as gerar_embeddings
from datetime import datetime

# Caminhos dos ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"

# Configuração da página
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

# Estilo customizado (cor de fundo e rodapé)
st.markdown("""
    <style>
    .stApp {
        background-color: #fff3e0;
    }
    .footer {
        text-align: center;
        color: gray;
        margin-top: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho com avatar e título
col_avatar, col_titulo = st.columns([0.1, 0.9])
with col_avatar:
    st.image("felisberto_avatar.png", width=70)
with col_titulo:
    st.markdown("<h1 style='color: #ef6c00;'>Felisberto, Assistente Administrativo ACSUTA</h1>", unsafe_allow_html=True)

# Carregar base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8-sig") as f:
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
            historico = []
    historico.append(registo)
    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

# Carregar perguntas existentes e calcular frequência (histórico)
base_conhecimento = carregar_base_conhecimento()
frequencia = {}
if os.path.exists(CAMINHO_HISTORICO):
    try:
        with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as f:
            historico = json.load(f)
            for item in historico:
                p = item.get("pergunta")
                if p:
                    frequencia[p] = frequencia.get(p, 0) + 1
    except json.JSONDecodeError:
        pass

perguntas_existentes = sorted(
    {p["pergunta"] for p in base_conhecimento},
    key=lambda x: -frequencia.get(x, 0)
)

# Interface de pergunta do utilizador
col1, col2 = st.columns(2)
with col1:
    pergunta_dropdown = st.selectbox(
        "Escolha uma pergunta frequente:",
        [""] + list(perguntas_existentes),
        key="dropdown"
    )
with col2:
    pergunta_manual = st.text_input("Ou escreva a sua pergunta:", key="manual")

pergunta_final = pergunta_manual.strip() if pergunta_manual.strip() else pergunta_dropdown

# Gerar resposta para a pergunta do utilizador
resposta = ""
if pergunta_final:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_final)
        guardar_pergunta_no_historico(pergunta_final)

if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

# Upload/adição de novas perguntas
st.markdown("---")
st.subheader("📝 Atualizar base de conhecimento")
st.markdown("**Adicionar pergunta manualmente:**")
with st.form("form_pergunta"):
    pergunta_nova = st.text_input("Pergunta:", value="")
    resposta_nova = st.text_area("Resposta:")
    email_nova = st.text_input("Email de contacto (opcional):", value="")
    modelo_nova = st.text_area("Modelo de email sugerido (opcional):")
    submit = st.form_submit_button("Adicionar pergunta")
if submit:
    if not pergunta_nova.strip() or not resposta_nova.strip():
        st.error("⚠️ Por favor preencha tanto a pergunta quanto a resposta.")
    else:
        try:
            base_existente = carregar_base_conhecimento()
            todas = {p["pergunta"]: p for p in base_existente}
            nova_entry = {
                "pergunta": pergunta_nova.strip(),
                "resposta": resposta_nova.strip(),
                "email": email_nova.strip(),
                "modelo_email": modelo_nova.strip()
            }
            todas[nova_entry["pergunta"]] = nova_entry
            with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
                json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
            gerar_embeddings()  # Atualizar embeddings
            st.success("✅ Base de conhecimento atualizada com sucesso.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao adicionar pergunta: {e}")

# Upload de perguntas via ficheiro JSON
novo_json = st.file_uploader("Ou carregar ficheiro JSON com novas perguntas", type="json")
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
            gerar_embeddings()  # Atualizar embeddings
            st.success("✅ Base de conhecimento atualizada com sucesso.")
            st.rerun()
        else:
            st.error("⚠️ O ficheiro JSON deve conter uma lista de perguntas.")
    except Exception as e:
        st.error(f"❌ Erro ao ler ficheiro JSON: {e}")

# Rodapé
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
