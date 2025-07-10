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
CODIGO_AUTORIZACAO = "decivil2024"

# Chave da API (ambiente ou Streamlit Cloud)
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
elif os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    st.warning("⚠️ A chave da API não está definida.")

# Função auxiliar: carregar perguntas frequentes
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

# Interface principal
st.set_page_config(page_title="Assistente DECivil", layout="wide")
st.title("📘 Assistente Administrativo DECivil")

# Colunas para perguntas
col1, col2 = st.columns(2)

base_conhecimento = carregar_base_conhecimento()
frequencia = {}

# Construir dicionário de frequência de uso
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

# Ordenar perguntas por frequência de uso
perguntas_existentes = sorted(
    set(p["pergunta"] for p in base_conhecimento),
    key=lambda x: -frequencia.get(x, 0)
)

with col1:
    pergunta_dropdown = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas_existentes)
with col2:
    pergunta_manual = st.text_input("Ou escreva a sua pergunta:")

pergunta_final = pergunta_manual.strip() if pergunta_manual.strip() else pergunta_dropdown

resposta = ""
if pergunta_final:
    resposta = gerar_resposta(pergunta_final)
    guardar_pergunta_no_historico(pergunta_final)

# Mostrar a resposta logo após a pergunta, e não após uploads
if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta)

# Secção de upload de documentos
st.markdown("---")
st.subheader("📎 Adicionar documentos ou links")
col3, col4 = st.columns(2)

with col3:
    ficheiro = st.file_uploader("Upload de ficheiro (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
    if ficheiro:
        try:
            processar_documento(ficheiro)
            st.success("✅ Documento processado com sucesso.")
        except Exception as e:
            st.error(f"Erro: {e}")

with col4:
    url = st.text_input("Ou insira um link para processar conteúdo:")
    if st.button("📥 Processar URL") and url:
        try:
            processar_documento(url)
            st.success("✅ Conteúdo do link processado com sucesso.")
        except Exception as e:
            st.error(f"Erro: {e}")

# Secção de inserção manual de novas perguntas
st.markdown("---")
with st.expander("🛠️ Inserir nova pergunta manualmente"):
    with st.form("form_nova_pergunta"):
        codigo = st.text_input("Código de autorização:", type="password")
        nova_pergunta = st.text_input("Pergunta:")
        nova_resposta = st.text_area("Resposta:")
        novo_email = st.text_input("Email de contacto (opcional):")
        modelo_email = st.text_area("Modelo de email sugerido (opcional):")
        submeter = st.form_submit_button("💾 Adicionar à base de conhecimento")

        if submeter:
            if codigo != CODIGO_AUTORIZACAO:
                st.error("❌ Código de autorização incorreto.")
            elif not nova_pergunta or not nova_resposta:
                st.warning("⚠️ Por favor preencha pergunta e resposta.")
            else:
                base = carregar_base_conhecimento()
                todas = {p["pergunta"]: p for p in base}
                todas[nova_pergunta] = {
                    "pergunta": nova_pergunta,
                    "resposta": nova_resposta,
                    "email": novo_email,
                    "modelo_email": modelo_email
                }
                with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
                    json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
                st.success("✅ Nova pergunta adicionada com sucesso.")
