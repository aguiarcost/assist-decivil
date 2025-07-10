import streamlit as st
import json
import os
import openai
from preparar_documentos_streamlit import processar_documento
from datetime import datetime
from assistente import gerar_resposta

# Inicialização de variáveis
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"

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

# Upload de novas perguntas/respostas
st.markdown("---")
st.subheader("📝 Atualizar base de conhecimento")
novo_json = st.file_uploader("Adicionar ficheiro JSON com novas perguntas", type="json")
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
            st.success("✅ Base de conhecimento atualizada.")
        else:
            st.error("⚠️ O ficheiro JSON deve conter uma lista de perguntas.")
    except Exception as e:
        st.error(f"Erro ao ler ficheiro JSON: {e}")
