# app.py
import os
import json
import requests
from io import BytesIO
import streamlit as st
from datetime import datetime

# -----------------------------
# Configuração
# -----------------------------
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="centered")
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
PASSWORD = "decivil2024"

# -----------------------------
# Estilos (laranja + respiração visual)
# -----------------------------
st.markdown("""
<style>
.stApp { background: #fff7ef; }

/* título laranja */
.app-title { color:#ef6c00; font-weight:800; font-size: 32px; margin: 0; line-height:1.1; }

/* header com avatar */
.header-wrap { display:flex; align-items:center; gap:12px; margin-top:-4px; margin-bottom:8px; }
.header-wrap img { width:84px; height:auto; border-radius:10px; }

/* separadores */
hr { border:0; border-top:1px solid #ffd3ad; margin:16px 0; }

/* rótulos e texto */
.block-container label, .block-container p { color:#4a3c2f; }

/* botões laranja */
.stButton > button { background:#ef6c00; border:0; color:white; font-weight:700; }
.stButton > button:hover { background:#ff7f11; }

/* cabeçalho das secções */
.section-title { color:#ef6c00; font-weight:800; margin-top:6px; }

/* separador visual de administração */
.section-divider { 
  margin: 26px 0 12px 0; 
  padding: 10px 12px; 
  background:#fff1e3; 
  border:1px solid #ffd3ad; 
  border-radius:10px; 
  color:#a65300; 
  font-weight:800; 
}

/* dar leve destaque aos expanders */
[data-testid="stExpander"] { 
  margin-top: 12px; 
  border: 1px solid #ffd3ad; 
  border-radius: 10px; 
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Utilitários de Base de Conhecimento
# -----------------------------
def ler_base_conhecimento() -> list:
    """Lê o JSON da base; se não existir ou estiver corrompido, devolve lista vazia normalizada."""
    try:
        if os.path.exists(CAMINHO_CONHECIMENTO):
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    norm = []
                    for item in data:
                        if isinstance(item, dict) and "pergunta" in item and "resposta" in item:
                            norm.append({
                                "pergunta": item.get("pergunta", "").strip(),
                                "resposta": item.get("resposta", "").strip(),
                                "email": (item.get("email") or "").strip(),
                                "modelo_email": (item.get("modelo_email") or item.get("modelo") or "").strip()
                            })
                    return norm
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return []

def escrever_base_conhecimento(registos: list) -> None:
    with open(CAMINHO_CONHECIMENTO, "w", encoding="utf-8") as f:
        json.dump(registos, f, ensure_ascii=False, indent=2)

def upsert_pergunta(base: list, nova: dict) -> list:
    """Insere/atualiza por 'pergunta' (evita duplicados)."""
    por_pergunta = {p["pergunta"]: p for p in base if "pergunta" in p}
    por_pergunta[nova["pergunta"]] = nova
    return list(por_pergunta.values())

def apagar_pergunta(base: list, pergunta: str) -> list:
    return [p for p in base if p.get("pergunta") != pergunta]

# -----------------------------
# Avatar + título (robusto: local → GitHub → fallback)
# -----------------------------
def carregar_avatar_bytes():
    # 1) local
    local_path = "felisberto_avatar.png"
    if os.path.exists(local_path):
        try:
            with open(local_path, "rb") as f:
                return f.read()
        except Exception:
            pass
    # 2) URL raw GitHub (ajusta se o branch/caminho for diferente)
    try:
        raw_url = "https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png"
        r = requests.get(raw_url, timeout=6)
        if r.ok and r.content:
            return r.content
    except Exception:
        pass
    # 3) nada
    return None

colA, colB = st.columns([1, 8], vertical_alignment="center")
with colA:
    _bytes = carregar_avatar_bytes()
    if _bytes:
        st.image(BytesIO(_bytes), width=84)
    else:
        st.markdown("🧑‍💼")  # fallback simples
with colB:
    st.markdown("<div class='app-title'>Felisberto, Assistente Administrativo ACSUTA</div>", unsafe_allow_html=True)

# -----------------------------
# Perguntas & Respostas (apenas dropdown)
# -----------------------------
base = ler_base_conhecimento()
perguntas_ordenadas = sorted([p["pergunta"] for p in base])

st.markdown("### ❓ Perguntas frequentes")
pergunta_escolhida = st.selectbox(
    "Escolha uma pergunta frequente:",
    [""] + perguntas_ordenadas,
    key="pergunta_escolhida"
)

if pergunta_escolhida.strip():
    entrada = next((p for p in base if p["pergunta"] == pergunta_escolhida), None)
    st.markdown("### 💡 Resposta do assistente")
    if entrada:
        st.markdown(entrada["resposta"] or "_Sem resposta definida._")
        if entrada.get("email"):
            st.markdown(f"**📧 Contacto:** [{entrada['email']}](mailto:{entrada['email']})")
        if entrada.get("modelo_email"):
            st.markdown("**✉️ Modelo de email sugerido:**")
            st.code(entrada["modelo_email"], language="text")
    else:
        st.info("Não encontrei essa pergunta na base de conhecimento.")

# separador visual grande antes da área de administração
st.markdown("<div class='section-divider'>Administração</div>", unsafe_allow_html=True)

# -----------------------------
# Criar nova pergunta (com password)
# -----------------------------
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

# -----------------------------
# Editar / Apagar pergunta (com password)
# -----------------------------
with st.expander("✏️ Editar ou apagar pergunta existente"):
    if not perguntas_ordenadas:
        st.info("A base de conhecimento está vazia.")
    else:
        # (re)carregar para refletir alterações recentes
        base_live = ler_base_conhecimento()
        opcoes = sorted([p["pergunta"] for p in base_live])

        with st.form("form_editar", clear_on_submit=False):
            pwd_edit = st.text_input("Password (obrigatória)", type="password")
            alvo = st.selectbox("Escolha a pergunta:", options=opcoes)

            atual = next((x for x in base_live if x["pergunta"] == alvo), None) or {}
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
                base_now = ler_base_conhecimento()
                nova = {
                    "pergunta": alvo,
                    "resposta": edit_resposta.strip(),
                    "email": (edit_email or "").strip(),
                    "modelo_email": (edit_modelo or "").strip()
                }
                base_now = upsert_pergunta(base_now, nova)
                escrever_base_conhecimento(base_now)
                st.success("✅ Alterações guardadas com sucesso.")

        if btn_apagar:
            if pwd_edit != PASSWORD:
                st.error("❌ Password incorreta.")
            else:
                base_now = ler_base_conhecimento()
                base_now = apagar_pergunta(base_now, alvo)
                escrever_base_conhecimento(base_now)
                st.success("🗑️ Pergunta apagada.")

# -----------------------------
# Download / Upload da base (com password)
# -----------------------------
with st.expander("⬇️⬆️ Download / Upload da base de conhecimento"):
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        pwd_down = st.text_input("Password para download", type="password", key="pwd_down")
        if st.button("⬇️ Download JSON"):
            if pwd_down != PASSWORD:
                st.error("❌ Password incorreta.")
            else:
                base_now = ler_base_conhecimento()
                st.download_button(
                    label="Descarregar base_conhecimento.json",
                    data=json.dumps(base_now, ensure_ascii=False, indent=2).encode("utf-8"),
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
