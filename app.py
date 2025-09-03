# app.py
import os
import json
import base64
import streamlit as st
from assistente import (
    ler_base_conhecimento,
    encontrar_perguntas_semelhantes,
)

# =========================
# Configuração / Constantes
# =========================
st.set_page_config(
    page_title="Felisberto, Assistente Administrativo ACSUTA",
    layout="centered",
)

AVATAR_FILENAME = "felisberto_avatar.png"

# =========================
# Estilos
# =========================
st.markdown(
    """
    <style>
      .stApp { background: #fff7ef; }
      h1 { color: #ef6c00; font-size: 2.2rem; margin-bottom: 0.5rem; }
      h2, h3 { color: #ef6c00; font-size: 1.2rem; margin-top: 1rem; }
      .header-flex { display:flex; align-items:center; gap:14px; }
      .title-tight { margin: 0; padding: 0; line-height: 1.1; }
      .resposta-box { background:#fff; border-left: 4px solid #ef6c00; padding:14px 16px; border-radius:8px; margin-bottom: 16px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Header com avatar
# =========================
def _avatar_html() -> str:
    try:
        root = os.path.dirname(__file__)
    except NameError:
        root = os.getcwd()

    avatar_path = os.path.join(root, AVATAR_FILENAME)
    if os.path.exists(avatar_path):
        with open(avatar_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"""
          <div class="header-flex">
              <img src="data:image/png;base64,{b64}" alt="avatar" width="72" />
              <h1 class="title-tight">Felisberto, Assistente Administrativo ACSUTA</h1>
          </div>
        """
    return '<h1 class="title-tight">Felisberto, Assistente Administrativo ACSUTA</h1>'

st.markdown(_avatar_html(), unsafe_allow_html=True)

# =========================
# Secção principal: Pergunta com correspondência aproximada
# =========================
st.markdown("## ❓ Perguntas e respostas")
base = ler_base_conhecimento()
perguntas = [r.get("pergunta", "") for r in base if r.get("pergunta")]

entrada = st.selectbox("Escreva ou escolha uma pergunta:",
                       options=perguntas,
                       index=0,
                       placeholder="Digite aqui...",
                       key="entrada_combo")

if entrada:
    semelhantes = encontrar_perguntas_semelhantes(entrada)
    if semelhantes:
        for p in semelhantes:
            reg = next((x for x in base if x.get("pergunta") == p), None)
            if reg:
                st.markdown(f"<div class='resposta-box'><strong>{p}</strong><br>{reg['resposta']}</div>", unsafe_allow_html=True)
    else:
        st.warning("Não encontrei nenhuma pergunta semelhante.")

st.markdown("---")
st.markdown("<small>© 2025 AAC</small>", unsafe_allow_html=True)
