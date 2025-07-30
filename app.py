import streamlit as st
import json
import os
import openai
from assistente import gerar_resposta
from gerar_embeddings import main as gerar_embeddings
from datetime import datetime

# Caminhos para os ficheiros de base de conhecimento e histórico
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"

st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

# Estilos e título da aplicação
st.markdown("""
    <style>
    .stApp { background-color: #fff3e0; }
    .titulo-container {
        display: flex; align-items: center; gap: 10px;
        margin-top: 10px; margin-bottom: 30px;
    }
    .titulo-container img { width: 70px; height: auto; }
    .titulo-container h1 {
        color: #ef6c00; font-size: 2em; margin: 0;
    }
    .footer { text-align: center; color: gray; margin-top: 50px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

def carregar_base_conhecimento():
    """Carrega a base de conhecimento (perguntas e respostas) do ficheiro JSON."""
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def guardar_pergunta_no_historico(pergunta):
    """Registra a pergunta feita pelo usuário no histórico, com timestamp."""
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

# Configurar chave da API OpenAI a partir de variável de ambiente
if os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    st.warning("⚠️ A chave da API OpenAI não está definida. Defina a variável de ambiente OPENAI_API_KEY.")

# Interface de Perguntas Frequentes e busca
base_conhecimento = carregar_base_conhecimento()
# Calcular frequência de perguntas já feitas para ordenar dropdown (opcional)
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

# Preparar lista de perguntas existentes, ordenadas por frequência de uso (descrescente)
perguntas_existentes = sorted(
    set(p["pergunta"] for p in base_conhecimento),
    key=lambda x: -frequencia.get(x, 0)
)

# Entrada de pergunta pelo utilizador
col1, col2 = st.columns(2)
with col1:
    pergunta_dropdown = st.selectbox(
        "Escolha uma pergunta frequente:",
        [""] + perguntas_existentes,
        key="dropdown"
    )
with col2:
    pergunta_manual = st.text_input("Ou escreva a sua pergunta:", key="manual")

# Determinar qual pergunta usar (dropdown tem prioridade se algo selecionado)
pergunta_final = pergunta_manual.strip() if pergunta_manual.strip() else pergunta_dropdown
resposta = ""

if pergunta_final:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_final)
        guardar_pergunta_no_historico(pergunta_final)

# Exibir a resposta, se houver
if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    # Mostra apenas o texto da resposta (campo 'resposta' do dicionário)
    if isinstance(resposta, dict) and "resposta" in resposta:
        st.markdown(resposta["resposta"], unsafe_allow_html=True)
    else:
        st.markdown(str(resposta), unsafe_allow_html=True)

# Seção para atualizar a base de conhecimento
st.markdown("---")
st.subheader("📝 Atualizar base de conhecimento")

# Upload de novo ficheiro JSON com perguntas e respostas
novo_json = st.file_uploader("Adicionar ficheiro JSON com novas perguntas", type="json")
if novo_json:
    try:
        novas_perguntas = json.load(novo_json)
        if isinstance(novas_perguntas, list):
            base_existente = carregar_base_conhecimento()
            # Mesclar novas perguntas com as existentes (chave única: texto da pergunta)
            todas = {p["pergunta"]: p for p in base_existente}
            for nova in novas_perguntas:
                todas[nova["pergunta"]] = nova
            with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
                json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
            gerar_embeddings()  # Atualiza embeddings da base de conhecimento
            st.success("✅ Base de conhecimento atualizada com sucesso.")
            st.experimental_rerun()
        else:
            st.error("⚠️ O ficheiro JSON deve conter uma **lista** de objetos de pergunta.")
    except Exception as e:
        st.error(f"Erro ao ler ficheiro JSON: {e}")

# Adicionar nova pergunta manualmente
with st.expander("➕ Adicionar nova pergunta manualmente"):
    nova_pergunta = st.text_input("Nova pergunta")
    nova_resposta = st.text_area("Resposta à pergunta")
    novo_email = st.text_input("Email de contacto (opcional)")
    novo_modelo = st.text_area("Modelo de email sugerido (opcional)")
    if st.button("Guardar pergunta"):
        if nova_pergunta and nova_resposta:
            base_existente = carregar_base_conhecimento()
            todas = {p["pergunta"]: p for p in base_existente}
            # Cria o registro da nova pergunta com campos correspondentes
            todas[nova_pergunta] = {
                "pergunta": nova_pergunta,
                "resposta": nova_resposta,
                "email": novo_email,
                "modelo_email": novo_modelo
            }
            with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
                json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
            gerar_embeddings()  # Recalcula embeddings incluindo a nova pergunta
            st.success("✅ Pergunta adicionada com sucesso à base de conhecimento.")
            st.experimental_rerun()
        else:
            st.warning("⚠️ Preencha pelo menos a **pergunta** e a **resposta** antes de guardar.")

# Rodapé
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 AAC</div>", unsafe_allow_html=True)
