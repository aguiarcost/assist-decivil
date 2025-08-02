import streamlit as st
from assistente import (
    carregar_base_conhecimento,
    guardar_base_conhecimento,
    gerar_resposta,
    gerar_embedding
)
import os
import json

st.set_page_config(page_title="Assistente ACSUTA", layout="wide")

st.markdown("## 🤖 Felisberto, Assistente Administrativo ACSUTA")
st.markdown("---")

# Carrega base
base = carregar_base_conhecimento()

# Frequência histórica para ordenação (opcional)
frequencia = {}
try:
    with open("historico_perguntas.json", "r", encoding="utf-8") as f:
        historico = json.load(f)
        for item in historico:
            p = item.get("pergunta")
            if p:
                frequencia[p] = frequencia.get(p, 0) + 1
except:
    pass

perguntas_existentes = sorted(
    set(p["pergunta"] for p in base),
    key=lambda x: -frequencia.get(x, 0)
)

# Dropdown de perguntas
pergunta_dropdown = st.selectbox("Escolha uma pergunta existente:", [""] + perguntas_existentes)

# Geração da resposta
if pergunta_dropdown:
    with st.spinner("A pensar..."):
        resposta = gerar_resposta(pergunta_dropdown)
        if resposta:
            st.markdown("### 💬 Resposta")
            st.markdown(resposta, unsafe_allow_html=True)
        else:
            st.warning("Não foi possível gerar uma resposta.")

st.markdown("---")
st.markdown("### ➕ Inserir nova pergunta")
com_nova = st.checkbox("Quero adicionar uma nova pergunta")

if com_nova:
    with st.form("formulario_novo"):
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta")
        email = st.text_input("Email (opcional)")
        modelo_email = st.text_area("Modelo de email sugerido (opcional)")
        password = st.text_input("Password de autorização", type="password")
        submeter = st.form_submit_button("Guardar pergunta")

        if submeter:
            if password != "decivil2024":
                st.error("🔒 Password incorreta.")
            elif not nova_pergunta or not nova_resposta:
                st.warning("⚠️ A pergunta e resposta são obrigatórias.")
            else:
                base = carregar_base_conhecimento()
                base = [p for p in base if p["pergunta"].strip().lower() != nova_pergunta.strip().lower()]
                base.append({
                    "pergunta": nova_pergunta.strip(),
                    "resposta": nova_resposta.strip(),
                    "email": email.strip(),
                    "modelo_email": modelo_email.strip()
                })
                guardar_base_conhecimento(base)
                st.success("✅ Pergunta adicionada com sucesso. A app será recarregada.")
                st.rerun()
