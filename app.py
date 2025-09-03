import json
import os
import streamlit as st

from assistente import (
    obter_todos,
    obter_perguntas,
    obter_por_pergunta,
    upsert_registo,
    apagar_por_pergunta,
    exportar_json,
    importar_json,
    validar_password,
    gerar_resposta,
)

# ---------------- UI setup / tema ----------------
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

st.markdown(
    """
    <style>
      .stApp { background-color: #fff3e0; }
      .titulo-container {
        display: flex; align-items: center; gap: 14px; margin: 0 0 10px 0;
      }
      .titulo-container img { width: 70px; height: 70px; border-radius: 8px; }
      .titulo-container h1 {
        color: #ef6c00; font-size: 28px; margin: 0; line-height: 1.1;
      }
      .secao {
        background: #ffffff;
        border: 1px solid #ffd9b3;
        border-radius: 12px;
        padding: 16px 16px 10px;
        margin-bottom: 16px;
      }
      .subtle { color:#5f6368; font-size: 13px; margin-top:4px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Avatar + título (usa imagem local)
avatar_path = "felisberto_avatar.png"
avatar_tag = f'<img src="app://{avatar_path}" alt="Avatar">' if os.path.exists(avatar_path) else ""
st.markdown(
    f"""
    <div class="titulo-container">
        {avatar_tag}
        <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- Estado ----------------
if "pergunta_selecionada" not in st.session_state:
    st.session_state.pergunta_selecionada = ""
if "resposta_render" not in st.session_state:
    st.session_state.resposta_render = ""

# ---------------- Secção: Pergunta & Resposta ----------------
with st.container():
    st.markdown('<div class="secao">', unsafe_allow_html=True)

    perguntas = obter_perguntas()
    def _on_change_pergunta():
        p = st.session_state._pergunta_select or ""
        st.session_state.pergunta_selecionada = p
        st.session_state.resposta_render = gerar_resposta(p) if p else ""

    st.selectbox(
        "Perguntas frequentes",
        [""] + perguntas,
        index= ([""] + perguntas).index(st.session_state.pergunta_selecionada)
            if st.session_state.pergunta_selecionada in perguntas else 0,
        key="_pergunta_select",
        on_change=_on_change_pergunta,
    )

    if st.session_state.resposta_render:
        st.markdown("### 💡 Resposta")
        st.markdown(st.session_state.resposta_render, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # fecha .secao

# ---------------- Secção: Criar nova pergunta (com password) ----------------
with st.container():
    st.markdown('<div class="secao">', unsafe_allow_html=True)
    with st.expander("➕ Criar nova pergunta"):
        pw = st.text_input("Password", type="password", key="pw_criar")
        nova_pergunta = st.text_input("Pergunta", key="nova_pergunta")
        nova_resposta = st.text_area("Resposta", key="nova_resposta")
        novo_email = st.text_input("Email (opcional)", key="novo_email")
        novo_modelo = st.text_area("Modelo de email (opcional)", key="novo_modelo")

        if st.button("Guardar nova pergunta"):
            if not validar_password(pw):
                st.error("Password inválida.")
            elif not (nova_pergunta.strip() and nova_resposta.strip()):
                st.warning("Preenche pelo menos Pergunta e Resposta.")
            else:
                upsert_registo(nova_pergunta, nova_resposta, novo_email, novo_modelo)
                st.success("✅ Pergunta criada/atualizada com sucesso.")
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Secção: Editar / Apagar pergunta (com password) ----------------
with st.container():
    st.markdown('<div class="secao">', unsafe_allow_html=True)
    with st.expander("✏️ Editar / Apagar pergunta existente"):
        pw2 = st.text_input("Password", type="password", key="pw_editar")
        todas = obter_todos()
        lista = [""] + [d["pergunta"] for d in todas]
        psel = st.selectbox("Escolhe a pergunta", lista, key="edit_select")

        if psel:
            reg = obter_por_pergunta(psel)
            ed_pergunta = st.text_input("Pergunta", value=reg.get("pergunta", ""), key="ed_pergunta")
            ed_resposta = st.text_area("Resposta", value=reg.get("resposta", ""), key="ed_resposta")
            ed_email = st.text_input("Email (opcional)", value=reg.get("email", ""), key="ed_email")
            ed_modelo = st.text_area("Modelo de email (opcional)", value=reg.get("modelo_email", ""), key="ed_modelo")

            colA, colB = st.columns(2)
            with colA:
                if st.button("💾 Guardar alterações"):
                    if not validar_password(pw2):
                        st.error("Password inválida.")
                    elif not (ed_pergunta.strip() and ed_resposta.strip()):
                        st.warning("Preenche pelo menos Pergunta e Resposta.")
                    else:
                        upsert_registo(ed_pergunta, ed_resposta, ed_email, ed_modelo)
                        st.success("✅ Alterações guardadas.")
                        st.experimental_rerun()
            with colB:
                if st.button("🗑️ Apagar pergunta"):
                    if not validar_password(pw2):
                        st.error("Password inválida.")
                    else:
                        apagar_por_pergunta(psel)
                        st.success("✅ Pergunta apagada.")
                        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Secção: Exportar / Importar (com password) ----------------
with st.container():
    st.markdown('<div class="secao">', unsafe_allow_html=True)
    with st.expander("⬇️⬆️ Exportar / Importar base de conhecimento (JSON)"):
        pw3 = st.text_input("Password", type="password", key="pw_io")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Exportar JSON"):
                if not validar_password(pw3):
                    st.error("Password inválida.")
                else:
                    txt = exportar_json()
                    st.download_button(
                        "Descarregar base_conhecimento.json",
                        data=txt.encode("utf-8"),
                        file_name="base_conhecimento.json",
                        mime="application/json",
                    )
        with col2:
            up = st.file_uploader("Importar JSON", type="json")
            if up is not None and st.button("📤 Importar agora"):
                if not validar_password(pw3):
                    st.error("Password inválida.")
                else:
                    try:
                        conteudo = json.load(up)
                        ok, total = importar_json(conteudo)
                        st.success(f"✅ Importação concluída: {ok}/{total} registos upsert.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro a importar: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Rodapé ----------------
st.markdown("<div class='subtle'>© 2025 AAC</div>", unsafe_allow_html=True)
