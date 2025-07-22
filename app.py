import streamlit as st
import json
import os
import openai
from assistente import gerar_resposta
from preparar_documentos_streamlit import processar_documento
from gerar_embeddings import main as gerar_embeddings
from datetime import datetime
import glob  # Novo: Para listar arquivos na pasta

# Inicialização de variáveis
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"
PASTA_DOCUMENTOS = "documentos"  # Novo: Pasta com documentos a processar automaticamente

# Configuração da página
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

# Estilo customizado
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
    </style>
""", unsafe_allow_html=True)

# Cabeçalho com avatar e título
st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Leitura da base de conhecimento
@st.cache_data
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Guardar histórico de perguntas
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

# Configurar chave OpenAI
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
elif os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    st.warning("⚠️ A chave da API não está definida.")

# Novo: Processar documentos da pasta "documentos" automaticamente na inicialização
def processar_documentos_pasta():
    if not os.path.exists(PASTA_DOCUMENTOS):
        os.makedirs(PASTA_DOCUMENTOS)  # Cria a pasta se não existir
    documentos = glob.glob(os.path.join(PASTA_DOCUMENTOS, "*"))  # Lista todos os arquivos na pasta
    processados = []  # Para evitar reprocessar se já feito
    if os.path.exists("base_documents_vector.json"):
        with open("base_documents_vector.json", "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                processados = [item['origem'] for item in data]
            except json.JSONDecodeError:
                pass
    for doc_path in documentos:
        if doc_path not in processados:
            try:
                with open(doc_path, "rb") as f:
                    processar_documento(f)  # Processa o arquivo como file_uploader faria
                st.success(f"✅ Documento {os.path.basename(doc_path)} processado automaticamente.")
            except Exception as e:
                st.error(f"Erro ao processar {os.path.basename(doc_path)}: {e}")

# Chama a função de processamento automático ao iniciar a app
if not st.session_state.get("documentos_processados", False):
    processar_documentos_pasta()
    st.session_state["documentos_processados"] = True

# Interface de pergunta
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
    set(p["pergunta"] for p in base_conhecimento),
    key=lambda x: -frequencia.get(x, 0)
)

col1, col2 = st.columns(2)
with col1:
    pergunta_dropdown = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas_existentes, key="dropdown")
with col2:
    pergunta_manual = st.text_input("Ou escreva a sua pergunta:", key="manual")

# Determinar pergunta final
pergunta_final = pergunta_manual.strip() if pergunta_manual.strip() else pergunta_dropdown

# Gerar resposta (sempre com RAG nos documentos)
resposta = ""
if pergunta_final:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_final, use_documents=True)  # Forçado para True
        guardar_pergunta_no_historico(pergunta_final)

# Mostrar resposta
if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

# Upload de documentos
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

# Atualização manual da base de conhecimento
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
            gerar_embeddings()  # Atualizar embeddings
            st.success("✅ Base de conhecimento atualizada.")
            st.experimental_rerun()  # Refresh para atualizar dropdown
        else:
            st.error("⚠️ O ficheiro JSON deve conter uma lista de perguntas.")
    except Exception as e:
        st.error(f"Erro ao ler ficheiro JSON: {e}")

# Adição manual de nova pergunta
with st.expander("➕ Adicionar nova pergunta manualmente"):
    nova_pergunta = st.text_input("Nova pergunta")
    nova_resposta = st.text_area("Resposta à pergunta")
    novo_email = st.text_input("Email de contacto (opcional)")
    novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
    if st.button("Guardar pergunta"):
        if nova_pergunta and nova_resposta:
            base_existente = carregar_base_conhecimento()
            todas = {p["pergunta"]: p for p in base_existente}
            todas[nova_pergunta] = {
                "pergunta": nova_pergunta,
                "resposta": nova_resposta,
                "email": novo_email,
                "modelo_email": novo_modelo
            }
            with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
                json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
            gerar_embeddings()  # Atualizar embeddings
            st.success("✅ Pergunta adicionada com sucesso.")
            st.experimental_rerun()  # Refresh para atualizar dropdown
        else:
            st.warning("⚠️ Preencha pelo menos a pergunta e a resposta.")

# Rodapé com data e autor
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>© 2025 AAC</p>", unsafe_allow_html=True)
