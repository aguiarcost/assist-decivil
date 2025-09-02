import os
import json
import requests
from io import BytesIO
import streamlit as st
from datetime import datetime

from assistente import (
    carregar_perguntas_frequentes,
    obter_resposta,
    upsert_pergunta,
    apagar_pergunta,
    importar_perguntas,
    exportar_perguntas,
)

# =========================
# Configuração
# =========================
APP_TITLE = "Felisberto, Assistente Administrativo ACSUTA"
ADMIN_PASSWORD = "decivil2024"

# -----------------------------
# Estilos
# -----------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")

st.markdown("""
<style>
.stApp { background: #fff7ef; }

/* título */
.app-title { color:#ef6c00; font-weight:800; font-size: 32px; margin: 0; line-height:1.1; }

/* header com avatar */
.header-wrap { display:flex; align-items:center; gap:16px; margin-top:-4px; margin-bottom:10px; }
.header-wrap img { width:84px; height:auto; border-radius:10px; }

/* separadores */
hr { border:0; border-top:1px solid #ffd3ad; margin:16px 0; }

/* texto */
.block-container label, .block-container p { color:#4a3c2f; }

/* botões */
.stButton > button { background:#ef6c00; border:0; color:white; font-weight:700; }
.stButton > button:hover { background:#ff7f11; }

/* caixas */
.resp-box { background:#fff; border:1px solid #f0e0d0; border-radius:10px; padding:14px 16px; }

/* separadores visuais */
.section-divider { margin:28px 0 12px 0; padding:10px 12px; background:#fff1e3; border:1px solid #ffd3ad; border-radius:10px; color:#a65300; font-weight:800; }
[data-testid="stExpander"] { margin-top:14px; border:1px solid #ffd3ad; border-radius:10px; box-shadow:0 1px 0 rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Avatar + título
# -----------------------------
def carregar_avatar_bytes():
    local_path = "felisberto_avatar.png"
    if os.path.exists(local_path):
        try:
            with open(local_path, "rb") as f:
                return f.read()
        except Exception:
            pass
    try:
        raw_url = "https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png"
        r = requests.get(raw_url, timeout=6)
        if r.ok and r.content:
            return r.content
    except Exception:
        pass
    return None

colA, colB = st.columns([1, 10], vertical_alignment="center")
with colA:
    avatar_bytes = carregar_avatar_bytes()
    if avatar_bytes:
        st.image(BytesIO(avatar_bytes), width=84)
    else:
        st.markdown("🧑‍💼")
with colB:
    st.markdown(f"<div class='app-title'>{APP_TITLE}</div>", unsafe_allow_html=True)

# -----------------------------
# 1) Perguntas & Respostas
# -----------------------------
st.markdown("### ❓ Perguntas frequentes")

base = ler_base_conhecimento()
perguntas = [p["pergunta"] for p in base]
pergunta_sel = st.selectbox("Escolha uma pergunta:", [""] + perguntas, index=0)

if pergunta_sel:
    item = next((x for x in base if x["pergunta"] == pergunta_sel), None)
    if item:
        st.markdown("### 💡 Resposta do assistente")
        st.markdown(f"<div class='resp-box'>{item['resposta']}</div>", unsafe_allow_html=True)

        if item.get("email"):
            st.markdown(f"**📧 Contacto:** [{item['email']}](mailto:{item['email']})")

        if item.get("modelo_email"):
            st.markdown("**✉️ Modelo de email sugerido:**")
            st.code(item["modelo_email"], language="text")
    else:
        st.info("Não encontrei essa pergunta na base de conhecimento.")

# -----------------------------
# 2) Criar nova pergunta
# -----------------------------
st.markdown("<div class='section-divider'>Criar nova pergunta</div>", unsafe_allow_html=True)

with st.expander("➕ Adicionar"):
    pwd_new = st.text_input("Password", type="password", key="pwd_new")
    nova_pergunta = st.text_input("Pergunta", key="nova_pergunta")
    nova_resposta = st.text_area("Resposta", height=140, key="nova_resposta")
    novo_email = st.text_input("Email (opcional)", key="novo_email")
    novo_modelo = st.text_area("Modelo de email (opcional)", height=140, key="novo_modelo")

    if st.button("💾 Guardar nova pergunta"):
        if pwd_new != ADMIN_PASSWORD:
            st.error("🔒 Password incorreta.")
        elif not nova_pergunta or not nova_resposta:
            st.warning("Preenche pelo menos **Pergunta** e **Resposta**.")
        else:
            try:
                nova = {
                    "pergunta": nova_pergunta.strip(),
                    "resposta": nova_resposta.strip(),
                    "email": (novo_email or "").strip(),
                    "modelo_email": (novo_modelo or "").strip()
                }
                upsert_pergunta([], nova)
                st.success("✅ Pergunta criada/atualizada com sucesso. Recarrega a página para ver no dropdown.")
            except Exception as e:
                st.error(f"Erro ao gravar: {e}")

# -----------------------------
# 3) Editar / Apagar pergunta
# -----------------------------
st.markdown("<div class='section-divider'>Editar / Apagar perguntas</div>", unsafe_allow_html=True)

with st.expander("✏️ Gerir perguntas existentes"):
    pwd2 = st.text_input("Password", type="password", key="pwd_edit")
    base2 = ler_base_conhecimento()
    perguntas2 = [p["pergunta"] for p in base2]
    alvo = st.selectbox("Seleciona a pergunta:", [""] + perguntas2, key="alvo_editar")

    if alvo:
        atual = next((x for x in base2 if x["pergunta"] == alvo), None) or {}
        e_resposta = st.text_area("Resposta", value=atual.get("resposta", ""), height=140, key="e_resposta")
        e_email = st.text_input("Email (opcional)", value=atual.get("email", ""), key="e_email")
        e_modelo = st.text_area("Modelo de email (opcional)", value=atual.get("modelo_email", ""), height=140, key="e_modelo")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Guardar alterações"):
                if pwd2 != ADMIN_PASSWORD:
                    st.error("🔒 Password incorreta.")
                else:
                    try:
                        nova = {
                            "pergunta": alvo,
                            "resposta": e_resposta.strip(),
                            "email": (e_email or "").strip(),
                            "modelo_email": (e_modelo or "").strip()
                        }
                        upsert_pergunta([], nova)
                        st.success("✅ Alterações guardadas. Recarrega a página para ver no dropdown.")
                    except Exception as e:
                        st.error(f"Erro ao gravar: {e}")
        with c2:
            if st.button("🗑️ Apagar pergunta"):
                if pwd2 != ADMIN_PASSWORD:
                    st.error("🔒 Password incorreta.")
                else:
                    try:
                        apagar_pergunta([], alvo)
                        st.success("🗑️ Pergunta apagada. Recarrega a página para atualizar o dropdown.")
                    except Exception as e:
                        st.error(f"Erro ao apagar: {e}")

# -----------------------------
# 4) Importar / Exportar base
# -----------------------------
st.markdown("<div class='section-divider'>Importar / Exportar base de conhecimento</div>", unsafe_allow_html=True)

with st.expander("⬇️ Download / ⬆️ Upload JSON"):
    pwd3 = st.text_input("Password", type="password", key="pwd_io")

    # Download
    if st.button("📥 Descarregar JSON"):
        if pwd3 != ADMIN_PASSWORD:
            st.error("🔒 Password incorreta.")
        else:
            try:
                txt = exportar_toda_base_json()
                st.download_button(
                    label="Download base_conhecimento.json",
                    data=txt.encode("utf-8"),
                    file_name="base_conhecimento.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Erro ao gerar JSON: {e}")

    # Upload
    up = st.file_uploader("Carregar ficheiro JSON", type=["json"])
    if st.button("📤 Importar JSON"):
        if pwd3 != ADMIN_PASSWORD:
            st.error("🔒 Password incorreta.")
        elif not up:
            st.warning("Seleciona um ficheiro JSON.")
        else:
            try:
                dados = json.loads(up.read().decode("utf-8"))
                if not isinstance(dados, list):
                    st.error("O JSON deve ser uma lista de objetos.")
                else:
                    from assistente import sb_bulk_import
                    sb_bulk_import(dados)
                    st.success("✅ Base importada com sucesso. Recarrega a página para atualizar.")
            except Exception as e:
                st.error(f"Erro ao importar: {e}")

# -----------------------------
# Rodapé
# -----------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='font-size:12px;color:#6d5c2f;text-align:center;'>© 2025 AAC</div>", unsafe_allow_html=True)
