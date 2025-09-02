# app.py
import os
import json
import streamlit as st
from datetime import datetime

# -----------------------------
# Configuração e constantes
# -----------------------------
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="centered")

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
PASSWORD = "decivil2024"

# -----------------------------
# Estilos (laranja + compactos)
# -----------------------------
st.markdown("""
<style>
/* fundo suave */
.stApp { background: #fff7ef; }

/* título laranja e mais compacto */
.app-title { 
  color:#ef6c00; 
  font-weight:800; 
  font-size: 32px; 
  margin: 0 0 4px 0; 
  line-height: 1.1;
}

/* container título + avatar */
.header-wrap {
  display:flex; 
  align-items:center; 
  gap:12px; 
  margin-top:-4px; 
  margin-bottom:10px;
}

/* avatar */
.header-wrap img { 
  width:88px; 
  height:auto; 
  border-radius:8px; 
}

/* separadores mais suaves */
hr { border:0; border-top:1px solid #ffd3ad; margin:14px 0; }

/* labels mais legíveis */
.block-container label, .block-container .st-emotion-cache-16idsys p {
  color:#4a3c2f;
}

/* botões laranja */
.stButton > button {
  background:#ef6c00; border:0; color:white; font-weight:700;
}
.stButton > button:hover { background:#ff7f11; }

/* cabeçalhos de secções */
.section-title { color:#ef6c00; font-weight:800; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Utilitários de Base de Conhecimento
# -----------------------------
def ler_base_conhecimento() -> list:
    """Lê o JSON da base; se não existir ou estiver corrompido, devolve lista vazia."""
    try:
        if os.path.exists(CAMINHO_CONHECIMENTO):
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    # normaliza chaves esperadas
                    norm = []
                    for item in data:
                        if isinstance(item, dict) and "pergunta" in item and "resposta" in item:
                            norm.append({
                                "pergunta": item.get("pergunta", "").strip(),
                                "resposta": item.get("resposta", "").strip(),
                                "email": item.get("email", "").strip(),
                                # Aceita "modelo" ou "modelo_email" e normaliza para "modelo_email"
                                "modelo_email": (item.get("modelo_email") or item.get("modelo") or "").strip()
                            })
                    return norm
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return []

def escrever_base_conhecimento(registos: list) -> None:
    """Escreve (com indentação) a base de conhecimento."""
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(registos, f, ensure_ascii=False, indent=2)

def upsert_pergunta(base: list, nova: dict) -> list:
    """Insere/atualiza pergunta por chave 'pergunta' (evita duplicados)."""
    por_pergunta = {p["pergunta"]: p for p in base if "pergunta" in p}
    por_pergunta[nova["pergunta"]] = nova
    return list(por_pergunta.values())

def apagar_pergunta(base: list, pergunta: str) -> list:
    """Remove a entrada com a 'pergunta' dada."""
    return [p for p in base if p.get("pergunta") != pergunta]

# -----------------------------
# Header com avatar + título
# -----------------------------
def mostrar_header():
    avatar_path = "felisberto_avatar.png"
    avatar_tag = f'<img src="app/static/felisberto_avatar.png" alt="Felisberto"/>'  # fallback se servires estático
    if os.path.exists(avatar_path):
        # preferir path local
        avatar_tag = f'<img src="{avatar_path}" alt="Felisberto"/>'

    st.markdown(f"""
    <div class="header-wrap">
        {avatar_tag}
        <div>
            <div class="app-title">Felisberto, Assistente Administrativo ACSUTA</div>
            <div style="color:#6d5c4c;font-size:12px;margin-top:2px;">
                Ajudo com tarefas administrativas do DECivil.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

mostrar_header()

# -----------------------------
# Estado da sessão (evita “segunda seleção” no dropdown)
# -----------------------------
if "pergunta_final" not in st.session_state:
    st.session_state.pergunta_final = ""
if "modo" not in st.session_state:
    st.session_state.modo = "dropdown"  # "dropdown" ou "manual"

# -----------------------------
# Perguntas & Respostas (topo)
# -----------------------------
base = ler_base_conhecimento()
perguntas_ordenadas = sorted([p["pergunta"] for p in base])

def on_change_dropdown():
    st.session_state.modo = "dropdown"
    st.session_state.pergunta_final = st.session_state.__getattribute__("pergunta_escolhida")

def on_change_manual():
    st.session_state.modo = "manual"
    st.session_state.pergunta_final = st.session_state.__getattribute__("pergunta_manual").strip()

st.markdown("<h4 class='section-title'>❓ Perguntas e respostas</h4>", unsafe_allow_html=True)

col_a, col_b = st.columns([1, 1])

with col_a:
    st.selectbox(
        "Escolha uma pergunta frequente:",
        options=[""] + perguntas_ordenadas,
        key="pergunta_escolhida",
        on_change=on_change_dropdown
    )
with col_b:
    st.text_input(
        "Ou escreva a sua pergunta:",
        key="pergunta_manual",
        on_change=on_change_manual
    )

# Apresentar resposta sem botão
def encontrar_resposta(pergunta_texto: str):
    for item in base:
        if item["pergunta"] == pergunta_texto:
            return item
    return None

pergunta_final = st.session_state.pergunta_final
if pergunta_final:
    entrada = encontrar_resposta(pergunta_final)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("💡 Resposta do assistente")
    if entrada:
        st.markdown(entrada["resposta"] or "_Sem resposta definida._")
        if entrada.get("email"):
            st.markdown(f"**📧 Email de contacto:** [{entrada['email']}](mailto:{entrada['email']})")
        if entrada.get("modelo_email"):
            st.markdown("**✉️ Modelo de email sugerido:**")
            st.code(entrada["modelo_email"], language="text")
    else:
        st.info("Não encontrei essa pergunta na base de conhecimento.")

# -----------------------------
# Criar nova pergunta (com password)
# -----------------------------
st.markdown("<hr>", unsafe_allow_html=True)
with st.expander("➕ Criar nova pergunta"):
    with st.form("form_criar_pergunta", clear_on_submit=False):
        pwd_new = st.text_input("Password (obrigatória)", type="password")
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta", height=160)
        novo_email = st.text_input("Email (opcional)")
        novo_modelo = st.text_area("Modelo de email (opcional)", height=160)
        btn_guardar = st.form_submit_button("💾 Guardar pergunta")

    if btn_guardar:
        if pwd_new != PASSWORD:
            st.error("❌ Password incorreta.")
        elif not nova_pergunta or not nova_resposta:
            st.warning("⚠️ 'Pergunta' e 'Resposta' são obrigatórias.")
        else:
            base = ler_base_conhecimento()
            nova = {
                "pergunta": nova_pergunta.strip(),
                "resposta": nova_resposta.strip(),
                "email": (novo_email or "").strip(),
                "modelo_email": (novo_modelo or "").strip()
            }
            base = upsert_pergunta(base, nova)
            escrever_base_conhecimento(base)
            st.success("✅ Pergunta adicionada/atualizada com sucesso.")
            st.info("🔁 Se o dropdown ainda não mostra a nova pergunta, recarrega a página.")
            # Atualiza memória da sessão
            st.session_state.pergunta_final = nova["pergunta"]

# -----------------------------
# Editar / Apagar pergunta (com password)
# -----------------------------
st.markdown("<hr>", unsafe_allow_html=True)
with st.expander("✏️ Editar ou apagar pergunta existente"):
    if not perguntas_ordenadas:
        st.info("A base de conhecimento está vazia.")
    else:
        with st.form("form_editar", clear_on_submit=False):
            pwd_edit = st.text_input("Password (obrigatória)", type="password")
            alvo = st.selectbox("Escolha a pergunta para editar/apagar:", options=perguntas_ordenadas)
            # Preencher campos com a entrada selecionada
            atual = next((x for x in base if x["pergunta"] == alvo), None) or {}
            edit_resposta = st.text_area("Resposta", value=atual.get("resposta", ""), height=160)
            edit_email = st.text_input("Email (opcional)", value=atual.get("email", ""))
            edit_modelo = st.text_area("Modelo de email (opcional)", value=atual.get("modelo_email", ""), height=160)

            c1, c2 = st.columns(2)
            with c1:
                btn_gravar = st.form_submit_button("💾 Guardar alterações")
            with c2:
                btn_apagar = st.form_submit_button("🗑️ Apagar pergunta")

        if btn_gravar:
            if pwd_edit != PASSWORD:
                st.error("❌ Password incorreta.")
            else:
                base = ler_base_conhecimento()
                nova = {
                    "pergunta": alvo,
                    "resposta": edit_resposta.strip(),
                    "email": (edit_email or "").strip(),
                    "modelo_email": (edit_modelo or "").strip()
                }
                base = upsert_pergunta(base, nova)
                escrever_base_conhecimento(base)
                st.success("✅ Alterações guardadas com sucesso.")
                st.session_state.pergunta_final = alvo

        if btn_apagar:
            if pwd_edit != PASSWORD:
                st.error("❌ Password incorreta.")
            else:
                base = ler_base_conhecimento()
                base = apagar_pergunta(base, alvo)
                escrever_base_conhecimento(base)
                st.success("🗑️ Pergunta apagada.")
                st.session_state.pergunta_final = ""

# -----------------------------
# Download / Upload da base (com password)
# -----------------------------
st.markdown("<hr>", unsafe_allow_html=True)
with st.expander("⬇️⬆️ Download / Upload da base de conhecimento"):
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        pwd_down = st.text_input("Password para download", type="password", key="pwd_down")
        if st.button("⬇️ Download JSON"):
            if pwd_down != PASSWORD:
                st.error("❌ Password incorreta.")
            else:
                base = ler_base_conhecimento()
                st.download_button(
                    label="Descarregar base_conhecimento.json",
                    data=json.dumps(base, ensure_ascii=False, indent=2).encode("utf-8"),
                    file_name=f"base_conhecimento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

    with col_d2:
        pwd_up = st.text_input("Password para upload", type="password", key="pwd_up")
        up = st.file_uploader("Carregar novo ficheiro JSON", type=["json"], key="uploader_json")
        if st.button("⬆️ Substituir base por upload"):
            if pwd_up != PASSWORD:
                st.error("❌ Password incorreta.")
            elif not up:
                st.warning("⚠️ Seleciona um ficheiro JSON.")
            else:
                try:
                    novo = json.load(up)
                    if not isinstance(novo, list):
                        raise ValueError("O JSON deve ser uma lista de objetos.")
                    # normaliza e valida
                    normalizado = []
                    for item in novo:
                        if not isinstance(item, dict):
                            continue
                        if "pergunta" in item and "resposta" in item:
                            normalizado.append({
                                "pergunta": item.get("pergunta", "").strip(),
                                "resposta": item.get("resposta", "").strip(),
                                "email": (item.get("email") or "").strip(),
                                "modelo_email": (item.get("modelo_email") or item.get("modelo") or "").strip()
                            })
                    escrever_base_conhecimento(normalizado)
                    st.success("✅ Base substituída com sucesso.")
                except Exception as e:
                    st.error(f"❌ Erro ao processar JSON: {e}")

# -----------------------------
# Rodapé
# -----------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='font-size:12px;color:#6d5c4c;text-align:center;'>© 2025 AAC</div>",
    unsafe_allow_html=True
)
