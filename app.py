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

# Chave da API
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
elif os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    st.warning("⚠️ A chave da API não está definida.")

@st.cache_data
def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

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

st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background-color: #fff3e0;
    }
    h1 {
        color: #ef6c00;
        display: flex;
        align-items: center;
        gap: 20px;
        margin-top: 0;
        margin-bottom: 10px;
    }
    .avatar-container {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .avatar-container img {
        width: 80px;
        margin-top: 0;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho com imagem
st.markdown(
    """
    <div class="avatar-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Inicializar estado
if "pergunta_final" not in st.session_state:
    st.session_state.pergunta_final = ""
if "resposta" not in st.session_state:
    st.session_state.resposta = ""

# Carregar base e histórico
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

# Perguntas
col1, col2 = st.columns(2)
with col1:
    pergunta_dropdown = st.selectbox(
        "Escolha uma pergunta frequente:",
        [""] + perguntas_existentes,
        key="pergunta_dropdown"
    )
with col2:
    pergunta_manual = st.text_input("Ou escreva a sua pergunta:", key="pergunta_manual")

if pergunta_manual.strip():
    st.session_state.pergunta_final = pergunta_manual.strip()
elif pergunta_dropdown:
    st.session_state.pergunta_final = pergunta_dropdown

if st.session_state.pergunta_final:
    st.session_state.resposta = gerar_resposta(st.session_state.pergunta_final)
    guardar_pergunta_no_historico(st.session_state.pergunta_final)

if st.session_state.resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")

    partes = st.session_state.resposta.split("📧 **Email de contacto:**")
    resposta_principal = partes[0].strip()
    st.markdown(f"**🟠 Resposta:**\n\n{resposta_principal}")

    if len(partes) > 1:
        resto = partes[1].split("📄 **Modelo de email sugerido:**")
        email_contacto = resto[0].strip()
        st.markdown(f"**📧 Email de contacto:** {email_contacto}")

        if len(resto) > 1:
            modelo_email = resto[1].strip()
            st.markdown("**📄 Modelo de email sugerido:**")
            st.code(modelo_email, language="text")

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

# Upload JSON
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
            st.success("✅ Base de conhecimento atualizada. Reinicie a aplicação para ver as novas perguntas.")
        else:
            st.error("⚠️ O ficheiro JSON deve conter uma lista de perguntas.")
    except Exception as e:
        st.error(f"Erro ao ler ficheiro JSON: {e}")

# Adicionar manualmente
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
                "modelo": novo_modelo
            }
            with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
                json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
            st.success("✅ Pergunta adicionada com sucesso.")
        else:
            st.warning("⚠️ Preencha a pergunta e a resposta.")
