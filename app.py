# app.py
import os
import json
import base64
import streamlit as st

from assistente import (
    ler_base_conhecimento,
    criar_pergunta,
    editar_pergunta,
    apagar_pergunta,
)

# =========================
# Configuração / Constantes
# =========================
st.set_page_config(
    page_title="Felisberto, Assistente Administrativo ACSUTA",
    layout="centered",
)

st.title("🤖 Felisberto – Assistente Administrativo ACSUTA")

# =========================
# Funções auxiliares
# =========================
@st.cache_data
def _carregar_base():
    """Carrega a base de conhecimento, com cache."""
    return ler_base_conhecimento()


def _refresh_base():
    """Atualiza a cache da base de dados."""
    try:
        st.session_state["_base_cache"] = _carregar_base()
    except Exception as e:
        st.warning("⚠️ Não foi possível carregar a base. A usar fallback local.")
        print("Erro:", e)
        st.session_state["_base_cache"] = []


# =========================
# Interface principal
# =========================
st.sidebar.header("📚 Base de Conhecimento")

if "_base_cache" not in st.session_state:
    _refresh_base()

dados = st.session_state.get("_base_cache", [])

modo = st.sidebar.radio("Modo", ["Consultar", "Adicionar", "Editar", "Apagar"])

# =========================
# CONSULTAR
# =========================
if modo == "Consultar":
    st.subheader("🔍 Consultar Base de Conhecimento")

    termo = st.text_input("Pesquisar por palavra-chave:")
    if termo:
        resultados = [
            item
            for item in dados
            if termo.lower() in item.get("pergunta", "").lower()
            or termo.lower() in item.get("resposta", "").lower()
        ]
    else:
        resultados = dados

    if resultados:
        for item in resultados:
            with st.expander(item.get("pergunta", "Pergunta sem título")):
                st.markdown(item.get("resposta", ""))
                st.caption(f"ID: {item.get('id', '—')}")
    else:
        st.info("Nenhum resultado encontrado.")

# =========================
# ADICIONAR
# =========================
elif modo == "Adicionar":
    st.subheader("➕ Adicionar Pergunta")
    pergunta = st.text_area("Pergunta")
    resposta = st.text_area("Resposta")
    email = st.text_input("Email (opcional)")
    modelo_email = st.text_input("Modelo de email (opcional)")

    if st.button("Gravar"):
        if pergunta and resposta:
            resultado = criar_pergunta(pergunta, resposta, email, modelo_email)
            if resultado is not None:
                st.success("Pergunta adicionada com sucesso!")
                _refresh_base()
        else:
            st.warning("Preencha pelo menos Pergunta e Resposta.")

# =========================
# EDITAR
# =========================
elif modo == "Editar":
    st.subheader("✏️ Editar Pergunta")

    ids = [str(item.get("id")) for item in dados if item.get("id")]
    if ids:
        id_sel = st.selectbox("Selecione o ID da pergunta", ids)
        item = next((i for i in dados if str(i.get("id")) == id_sel), None)

        if item:
            nova_pergunta = st.text_area("Nova pergunta", item.get("pergunta", ""))
            nova_resposta = st.text_area("Nova resposta", item.get("resposta", ""))
            if st.button("Guardar alterações"):
                resultado = editar_pergunta(id_sel, nova_pergunta, nova_resposta)
                if resultado is not None:
                    st.success("Pergunta atualizada!")
                    _refresh_base()
        else:
            st.warning("ID não encontrado.")
    else:
        st.info("Sem registos disponíveis.")

# =========================
# APAGAR
# =========================
elif modo == "Apagar":
    st.subheader("🗑️ Apagar Pergunta")

    ids = [str(item.get("id")) for item in dados if item.get("id")]
    if ids:
        id_sel = st.selectbox("Selecione o ID da pergunta", ids)
        if st.button("Apagar"):
            resultado = apagar_pergunta(id_sel)
            if resultado is not None:
                st.success(f"Pergunta {id_sel} apagada!")
                _refresh_base()
    else:
        st.info("Sem registos disponíveis para apagar.")

# =========================
# Rodapé
# =========================
st.markdown("---")
st.caption("💡 Desenvolvido por ACSUTA · Felisberto AI · v1.0")
