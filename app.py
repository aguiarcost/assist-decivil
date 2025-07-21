import streamlit as st
import json
import os
import openai
from assistente import gerar_resposta
from preparar_documentos_streamlit import processar_documento
from datetime import datetime

# Inicialização de variáveis e caminhos
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"

# Configuração da página
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

# Estilo customizado
st.markdown("""
    <style>
    .stApp { background-color: #fff3e0; }
    .titulo-container { display: flex; align-items: center; gap: 10px;
                         margin-top: 10px; margin-bottom: 30px; }
    .titulo-container img { width: 70px; height: auto; }
    .titulo-container h1 { color: #ef6c00; font-size: 2em; margin: 0; }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho com avatar e título
st.markdown("""
    <div class="titulo-container">
        <img src="https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png" alt="Felisberto Avatar">
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
""", unsafe_allow_html=True)

# Funções auxiliares
@st.cache_data
def carregar_base_conhecimento():
    """Carrega a base de conhecimento a partir do ficheiro JSON."""
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

@st.cache_data
def carregar_base_vectorizada():
    """Carrega a base vetorizada (embeddings). Gera o ficheiro se não existir."""
    base_conhecimento = carregar_base_conhecimento()
    if os.path.exists("base_vectorizada.json"):
        try:
            with open("base_vectorizada.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Se o ficheiro existir mas estiver corrompido, regenerar
            os.remove("base_vectorizada.json")
    # Caso não exista, gerar os embeddings para a base de conhecimento
    lista_embeddings = []
    for item in base_conhecimento:
        pergunta = item.get("pergunta")
        if pergunta:
            try:
                resp = openai.Embedding.create(input=pergunta, model="text-embedding-ada-002")
            except Exception as e:
                st.error(f"Erro ao gerar embedding para a pergunta \"{pergunta}\": {e}")
                continue
            embed = resp["data"][0]["embedding"]
            lista_embeddings.append({ "pergunta": pergunta, "embedding": embed })
    # Guardar embeddings gerados no ficheiro para reutilização futura
    with open("base_vectorizada.json", "w", encoding="utf-8") as f:
        json.dump(lista_embeddings, f, ensure_ascii=False, indent=2)
    return lista_embeddings

def guardar_pergunta_no_historico(pergunta):
    """Regista a pergunta realizada no histórico local, com timestamp."""
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

# Configurar chave da API OpenAI de forma segura
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
elif os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    st.warning("⚠️ A chave da API OpenAI não está definida nos segredos ou variáveis de ambiente.")

# Carregar bases de conhecimento e vetorizada
base_conhecimento = carregar_base_conhecimento()
base_vectorizada = carregar_base_vectorizada()

# Preparar lista de perguntas existentes, ordenadas por frequência no histórico
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
    {p["pergunta"] for p in base_conhecimento if "pergunta" in p},
    key=lambda x: -frequencia.get(x, 0)
)

# Interface de pergunta
col1, col2 = st.columns(2)
def limpar_texto():
    st.session_state.manual = ""
def limpar_dropdown():
    st.session_state.dropdown = ""

with col1:
    pergunta_dropdown = st.selectbox(
        "Escolha uma pergunta frequente:",
        [""] + list(perguntas_existentes),
        key="dropdown",
        on_change=limpar_texto
    )
with col2:
    pergunta_manual = st.text_input(
        "Ou escreva a sua pergunta:",
        key="manual",
        on_change=limpar_dropdown
    )

# Determinar pergunta final a enviar
pergunta_final = pergunta_manual.strip() if pergunta_manual.strip() else pergunta_dropdown

# Gerar resposta e apresentar
resposta = ""
if pergunta_final:
    resposta = gerar_resposta(pergunta_final, base_conhecimento=base_conhecimento, base_vectorizada=base_vectorizada)
    guardar_pergunta_no_historico(pergunta_final)

if resposta:
    st.markdown("---")
    st.subheader("💡 Resposta do assistente")
    st.markdown(resposta, unsafe_allow_html=True)

# Upload de documentos ou conteúdo
st.markdown("---")
st.subheader("📎 Adicionar documentos ou links")
col3, col4 = st.columns(2)
with col3:
    ficheiro = st.file_uploader("Upload de ficheiro (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
    if ficheiro:
        try:
            processar_documento(ficheiro)
            st.success("✅ Documento processado com sucesso.")
            st.cache_data.clear()  # Limpar cache para incluir novo conteúdo
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro: {e}")
with col4:
    url = st.text_input("Ou insira um link para processar conteúdo:")
    if st.button("📥 Processar URL") and url:
        try:
            processar_documento(url)
            st.success("✅ Conteúdo do link processado com sucesso.")
            st.cache_data.clear()
            st.experimental_rerun()
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
            existentes_set = {p["pergunta"] for p in base_existente if "pergunta" in p}
            todas = {p["pergunta"]: p for p in base_existente if "pergunta" in p}
            novas_adicionadas = []
            for nova in novas_perguntas:
                # Só adicionar/atualizar entradas válidas com pergunta e resposta
                if "pergunta" in nova and "resposta" in nova:
                    todas[nova["pergunta"]] = nova
                    if nova["pergunta"] not in existentes_set:
                        novas_adicionadas.append(nova["pergunta"])
            # Gravar base de conhecimento atualizada
            with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
                json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
            # Gerar embeddings para novas perguntas e adicionar à base vetorizada
            if novas_adicionadas:
                try:
                    with open("base_vectorizada.json", "r", encoding="utf-8") as f:
                        dados_vec = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    dados_vec = []
                for pergunta in novas_adicionadas:
                    try:
                        resp = openai.Embedding.create(input=pergunta, model="text-embedding-ada-002")
                        emb = resp["data"][0]["embedding"]
                        dados_vec.append({ "pergunta": pergunta, "embedding": emb })
                    except Exception as e:
                        st.error(f"Erro ao gerar embedding para \"{pergunta}\": {e}")
                with open("base_vectorizada.json", "w", encoding="utf-8") as f:
                    json.dump(dados_vec, f, ensure_ascii=False, indent=2)
            st.success("✅ Base de conhecimento atualizada.")
            # Atualizar dados em memória do assistente
            try:
                import assistente
                assistente.conhecimento, assistente.perguntas_emb, assistente.embeddings = assistente.carregar_dados()
            except Exception:
                pass
            st.cache_data.clear()
            st.experimental_rerun()
        else:
            st.error("⚠️ O ficheiro JSON deve conter uma lista de perguntas.")
    except Exception as e:
        st.error(f"Erro ao ler ficheiro JSON: {e}")

# Adição manual de nova pergunta
with st.expander("➕ Adicionar nova pergunta manualmente"):
    nova_pergunta = st.text_input("Nova pergunta", key="nova_pergunta")
    nova_resposta = st.text_area("Resposta à pergunta", key="nova_resposta")
    novo_email = st.text_input("Email de contacto (opcional)", key="novo_email")
    novo_modelo = st.text_area("Modelo de email sugerido (opcional)", key="novo_modelo")
    if st.button("Guardar pergunta"):
        if nova_pergunta and nova_resposta:
            base_existente = carregar_base_conhecimento()
            existentes_set = {p["pergunta"] for p in base_existente if "pergunta" in p}
            todas = {p["pergunta"]: p for p in base_existente if "pergunta" in p}
            todas[nova_pergunta] = {
                "pergunta": nova_pergunta,
                "resposta": nova_resposta,
                "email": novo_email,
                "modelo": novo_modelo
            }
            # Gravar base de conhecimento atualizada
            with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
                json.dump(list(todas.values()), f, ensure_ascii=False, indent=2)
            # Gerar e guardar embedding da nova pergunta se for realmente nova
            if nova_pergunta not in existentes_set:
                try:
                    with open("base_vectorizada.json", "r", encoding="utf-8") as f:
                        dados_vec = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    dados_vec = []
                try:
                    resp = openai.Embedding.create(input=nova_pergunta, model="text-embedding-ada-002")
                    emb = resp["data"][0]["embedding"]
                    dados_vec.append({ "pergunta": nova_pergunta, "embedding": emb })
                    with open("base_vectorizada.json", "w", encoding="utf-8") as f:
                        json.dump(dados_vec, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    st.error(f"Erro ao gerar embedding para \"{nova_pergunta}\": {e}")
            st.success("✅ Pergunta adicionada com sucesso.")
            # Atualizar dados em memória do assistente
            try:
                import assistente
                assistente.conhecimento, assistente.perguntas_emb, assistente.embeddings = assistente.carregar_dados()
            except Exception:
                pass
            st.cache_data.clear()
            st.experimental_rerun()
        else:
            st.warning("⚠️ Preencha pelo menos a pergunta e a resposta.")

# Rodapé com data e autor
st.markdown("<hr style='margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>© 2025 AAC</p>", unsafe_allow_html=True)
