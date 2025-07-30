import streamlit as st
import json
import os
import openai
from assistente import gerar_resposta
from preparar_documentos_streamlit import processar_documento
from gerar_embeddings import main as gerar_embeddings
from datetime import datetime
import glob

# Caminhos
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"
PASTA_DOCUMENTOS = "documentos"
CAMINHO_DOCUMENTOS_PROCESSADOS = "documentos_processados.json"

# Funções de controle de documentos processados
def carregar_documentos_processados():
    if os.path.exists(CAMINHO_DOCUMENTOS_PROCESSADOS):
        try:
            with open(CAMINHO_DOCUMENTOS_PROCESSADOS, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def guardar_documento_processado(nome_ficheiro):
    documentos = carregar_documentos_processados()
    documentos.add(nome_ficheiro)
    with open(CAMINHO_DOCUMENTOS_PROCESSADOS, "w", encoding="utf-8") as f:
        json.dump(list(documentos), f, ensure_ascii=False, indent=2)

# Processar documentos se novos
def processar_documentos_pasta(force_reprocess=False):
    if not os.path.exists(PASTA_DOCUMENTOS):
        os.makedirs(PASTA_DOCUMENTOS)
    documentos = glob.glob(os.path.join(PASTA_DOCUMENTOS, "*"))
    processados = carregar_documentos_processados()

    for doc_path in documentos:
        basename = os.path.basename(doc_path)
        if basename not in processados or force_reprocess:
            try:
                with open(doc_path, "rb") as f:
                    salvos = processar_documento(f)
                guardar_documento_processado(basename)
                st.success(f"✅ Documento {basename} processado com {salvos} blocos.")
            except Exception as e:
                st.error(f"Erro ao processar {basename}: {e}")

# Guarda histórico
def guardar_pergunta_no_historico(pergunta):
    registo = {"pergunta": pergunta, "timestamp": datetime.now().isoformat()}
    if os.path.exists(CAMINHO_HISTORICO):
        try:
            with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as f:
                historico = json.load(f)
        except:
            historico = []
    else:
        historico = []
    historico.append(registo)
    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

# Carregar base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except:
            return []
    return []

# Config pagina
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

# Processamento inicial
if 'initialized' not in st.session_state:
    processar_documentos_pasta()
    st.session_state.initialized = True

# Titulo e estilo
st.markdown("""
    <style>
    .stApp { background-color: #fff3e0; }
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

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Interface
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
    except:
        pass

perguntas_existentes = sorted(set(p["pergunta"] for p in base_conhecimento), key=lambda x: -frequencia.get(x, 0))

col1, col2 = st.columns(2)
with col1:
    pergunta_dropdown = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas_existentes, key="dropdown")
with col2:
    pergunta_manual = st.text_input("Ou escreva a sua pergunta:", key="manual")

pergunta_final = pergunta_manual.strip() if pergunta_manual.strip() else pergunta_dropdown
resposta = ""
if pergunta_final:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_final, use_documents=True)
        guardar_pergunta_no_historico(pergunta_final)

if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

st.markdown("---")
st.subheader("📎 Adicionar documentos ou links")
col3, col4 = st.columns(2)
with col3:
    ficheiro = st.file_uploader("Upload de ficheiro (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
    if ficheiro:
        try:
            processar_documento(ficheiro)
            guardar_documento_processado(ficheiro.name)
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
            gerar_embeddings()
            st.success("✅ Base de conhecimento atualizada.")
            st.rerun()
        else:
            st.error("⚠️ O ficheiro JSON deve conter uma lista de perguntas.")
    except Exception as e:
        st.error(f"Erro ao ler ficheiro JSON: {e}")

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
            gerar_embeddings()
            st.success("✅ Pergunta adicionada com sucesso.")
            st.rerun()
        else:
            st.warning("⚠️ Preencha pelo menos a pergunta e a resposta.")

st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
