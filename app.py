import os
import json
import streamlit as st
from datetime import datetime
from assistente import (
    ler_base_conhecimento,
    sb_upsert,
    sb_delete_by_pergunta,
    exportar_toda_base_json,
    sb_bulk_import,
    PASSWORD,
)

# =========================
# Configuração & Estilos
# =========================
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

APP_TITLE = "Felisberto, Assistente Administrativo ACSUTA"

st.markdown(
    """
    <style>
    .stApp { background: #fff7ef; }
    .felis-title { color:#ef6c00; font-weight:800; font-size: 32px; margin:0; line-height:1.1; }
    .felis-header { display:flex; align-items:center; gap:12px; margin-top:-4px; margin-bottom:10px; }
    .felis-avatar { width:84px; height:auto; border-radius:10px; }
    hr { border:0; border-top:1px solid #ffd3ad; margin:16px 0; }
    .resp-box { background:#fff; border:1px solid #f0e0d0; border-radius:10px; padding:14px 16px; }
    .section-title {
      margin: 28px 0 8px 0; padding: 10px 12px; background:#fff1e3;
      border:1px solid #ffd3ad; border-radius:10px; color:#a65300; font-weight:800;
    }
    .spacer { height: 8px; }
    [data-testid="stExpander"] {
      margin-top: 10px; border: 1px solid #ffd3ad; border-radius: 10px;
      box-shadow: 0 1px 0 rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Header com avatar
# =========================
st.markdown("<div class='felis-header'>", unsafe_allow_html=True)
avatar_path = "felisberto_avatar.png"
if os.path.exists(avatar_path):
    st.image(avatar_path, width=84)
else:
    st.markdown("🧑‍💼")  # fallback

st.markdown(f"<h1 class='felis-title'>{APP_TITLE}</h1></div>", unsafe_allow_html=True)

# =========================
# Perguntas & Respostas
# =========================
st.markdown("<div class='section-title'>📋 Perguntas frequentes</div>", unsafe_allow_html=True)

# lê dados (com cache interna do módulo)
base = ler_base_conhecimento()
perguntas = [p["pergunta"] for p in base]

col_q, = st.columns(1)
with col_q:
    pergunta_sel = st.selectbox("Escolha uma pergunta:", [""] + perguntas, index=0)

# resposta dinâmica
if pergunta_sel:
    entrada = next((x for x in base if x["pergunta"] == pergunta_sel), None)
    if entrada:
        st.markdown("### 💡 Resposta do assistente")
        st.markdown(f"<div class='resp-box'>{entrada['resposta']}</div>", unsafe_allow_html=True)

        if (entrada.get("email") or "").strip():
            st.markdown("**📧 Contacto:** " + f"[{entrada['email']}](mailto:{entrada['email']})")

        if (entrada.get("modelo_email") or "").strip():
            st.markdown("**✉️ Modelo de email sugerido:**")
            st.code(entrada["modelo_email"], language="text")

# dar mais “respiro” antes da área admin
st.markdown("<div class='spacer'></div><div class='spacer'></div>", unsafe_allow_html=True)

# =========================
# Criar nova pergunta (expander)
# =========================
with st.expander("➕ Criar nova pergunta"):
    with st.form("form_criar", clear_on_submit=False):
        pwd_new = st.text_input("Password", type="password")
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta", height=140)
        novo_email = st.text_input("Email (opcional)")
        novo_modelo = st.text_area("Modelo de email (opcional)", height=140)
        salvar = st.form_submit_button("💾 Guardar")

    if salvar:
        if pwd_new != PASSWORD:
            st.error("🔒 Password incorreta.")
        elif not nova_pergunta or not nova_resposta:
            st.warning("⚠️ Preenche pelo menos Pergunta e Resposta.")
        else:
            try:
                sb_upsert(nova_pergunta, nova_resposta, novo_email, novo_modelo)
                st.success("✅ Pergunta criada/atualizada com sucesso.")
                st.rerun()  # atualiza dropdown imediatamente
            except Exception as e:
                st.error(f"Erro: {e}")

# =========================
# Editar / Apagar pergunta (expander)
# =========================
with st.expander("✏️ Editar ou apagar pergunta existente"):
    base2 = ler_base_conhecimento()
    perguntas2 = [p["pergunta"] for p in base2]

    if not perguntas2:
        st.info("Base de conhecimento vazia.")
    else:
        alvo = st.selectbox("Pergunta a editar:", [""] + perguntas2, key="sel_edit")
        atual = next((x for x in base2 if x["pergunta"] == alvo), None) or {}

        with st.form("form_editar", clear_on_submit=False):
            pwd_edit = st.text_input("Password", type="password", key="pwd_edit")
            e_resposta = st.text_area("Resposta", value=atual.get("resposta", ""), height=140)
            e_email = st.text_input("Email (opcional)", value=atual.get("email", ""), key="e_email")
            e_modelo = st.text_area("Modelo de email (opcional)", value=atual.get("modelo_email", ""), height=140, key="e_modelo")

            c1, c2 = st.columns(2)
            with c1:
                btn_gravar = st.form_submit_button("💾 Guardar alterações")
            with c2:
                btn_apagar = st.form_submit_button("🗑️ Apagar")

        if btn_gravar:
            if pwd_edit != PASSWORD:
                st.error("🔒 Password incorreta.")
            elif not alvo or not e_resposta:
                st.warning("⚠️ Pergunta e resposta são obrigatórias.")
            else:
                try:
                    sb_upsert(alvo, e_resposta, e_email, e_modelo)
                    st.success("✅ Alterações guardadas.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        if btn_apagar:
            if pwd_edit != PASSWORD:
                st.error("🔒 Password incorreta.")
            elif not alvo:
                st.warning("⚠️ Seleciona uma pergunta para apagar.")
            else:
                try:
                    sb_delete_by_pergunta(alvo)
                    st.success("🗑️ Pergunta apagada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# =========================
# Importar / Exportar JSON (expander)
# =========================
with st.expander("⬇️ Download / ⬆️ Upload da base de conhecimento"):
    pwd_io = st.text_input("Password", type="password", key="pwd_io")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("📥 Descarregar JSON"):
            if pwd_io != PASSWORD:
                st.error("🔒 Password incorreta.")
            else:
                try:
                    txt = exportar_toda_base_json()
                    st.download_button(
                        label="Download base_conhecimento.json",
                        data=txt.encode("utf-8"),
                        file_name=f"base_conhecimento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Erro ao exportar: {e}")

    with col_d2:
        up = st.file_uploader("Carregar JSON", type=["json"], key="uploader_json")
        if st.button("📤 Importar JSON"):
            if pwd_io != PASSWORD:
                st.error("🔒 Password incorreta.")
            elif not up:
                st.warning("⚠️ Seleciona um ficheiro JSON.")
            else:
                try:
                    dados = json.loads(up.read().decode("utf-8"))
                    sb_bulk_import(dados)
                    st.success("✅ Base importada com sucesso.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao importar: {e}")

# =========================
# Rodapé
# =========================
st.markdown("---")
st.markdown("<div style='font-size:12px;color:#6d5c2f;text-align:center;'>© 2025 AAC</div>", unsafe_allow_html=True)
