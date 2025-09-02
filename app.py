import streamlit as st
import os
from assistente import (
    carregar_perguntas_frequentes,
    gerar_resposta,
    adicionar_pergunta,
    editar_pergunta,
    apagar_pergunta,
    carregar_base,
    exportar_base_bytes,
    importar_base_de_bytes,
)

st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

# ==================== Estilo & Título (avatar) ====================
st.markdown("""
<style>
.stApp { background-color: #fff3e0; }
.titulo-container { display:flex; align-items:center; gap:12px; margin:10px 0 12px 0; }
.titulo-container img { width:72px; height:auto; }
.titulo-container h1 { color:#ef6c00; font-size:2.0rem; margin:0; }
.block-after-title { margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

def _avatar_html():
    # 1) tenta local
    if os.path.exists("felisberto_avatar.png"):
        return '<img src="felisberto_avatar.png" alt="Felisberto">'
    # 2) tenta URL raw do GitHub (ajusta se mudares o repo/branch)
    raw_url = "https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png"
    # onerror: esconde se falhar
    return f'<img src="{raw_url}" alt="Felisberto" onerror="this.style.display=\'none\'">'

st.markdown(f"""
<div class="titulo-container">
  {_avatar_html()}
  <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
</div>
<div class="block-after-title"></div>
""", unsafe_allow_html=True)

# ==================== Password Admin (default = decivil2024) ====================
ADMIN_PASSWORD_DEFAULT = "decivil2024"

def obter_admin_password_config():
    """Prioridade: secrets['ADMIN_PASSWORD'] > env ADMIN_PASSWORD > default."""
    try:
        if "ADMIN_PASSWORD" in st.secrets:
            return str(st.secrets["ADMIN_PASSWORD"])
    except Exception:
        pass
    pw = os.getenv("ADMIN_PASSWORD")
    if pw:
        return pw
    return ADMIN_PASSWORD_DEFAULT

def pedir_autenticacao():
    pw_input = st.text_input("🔐 Password de administração", type="password", key="admin_pw_input")
    if pw_input:
        if pw_input == obter_admin_password_config():
            st.session_state["is_admin"] = True
            st.success("Sessão admin ativa.")
        else:
            st.session_state["is_admin"] = False
            st.error("Password incorreta.")
    return st.session_state.get("is_admin", False)

# Painel rápido de administração
st.markdown("#### Administração")
if not st.session_state.get("is_admin", False):
    pedir_autenticacao()
else:
    col_ok1, col_ok2 = st.columns([3,1])
    with col_ok1:
        st.success("Admin ligado.")
    with col_ok2:
        if st.button("Terminar sessão admin"):
            st.session_state["is_admin"] = False
            st.experimental_rerun()

st.markdown("---")

# ==================== Pergunta principal (dropdown sem botão) ====================
st.subheader("Faça a sua pergunta")

perguntas = carregar_perguntas_frequentes()
if not perguntas:
    st.info("Ainda não existem perguntas na base. Vá a **Adicionar nova pergunta (admin)** para criar a primeira.")
pergunta_escolhida = st.selectbox(
    "Escolha uma pergunta frequente:",
    [""] + perguntas,
    key="pergunta_dropdown"
)

if pergunta_escolhida.strip():
    resposta_md = gerar_resposta(pergunta_escolhida)
    st.markdown("### 💡 Resposta do assistente")
    st.markdown(resposta_md, unsafe_allow_html=True)

st.markdown("---")

# ==================== Import/Export (admin) ====================
with st.expander("📦 Importar / Exportar base de conhecimento (admin)", expanded=False):
    if st.session_state.get("is_admin"):
        col_exp, col_imp = st.columns(2)
        with col_exp:
            st.caption("Descarregar uma cópia da base atual:")
            data = exportar_base_bytes()
            st.download_button(
                label="⬇️ Download base_conhecimento.json",
                data=data,
                file_name="base_conhecimento.json",
                mime="application/json",
                key="download_base"
            )
        with col_imp:
            st.caption("Importar (substitui a base atual):")
            up = st.file_uploader("Escolher JSON", type="json", key="upload_base")
            if up:
                ok, msg = importar_base_de_bytes(up.read())
                if ok:
                    st.success(msg)
                    st.experimental_rerun()
                else:
                    st.error(msg)
    else:
        st.info("Área reservada. Introduza a password para administrar.")

st.markdown("---")

# ==================== Adicionar (admin) ====================
with st.expander("➕ Adicionar nova pergunta (admin)", expanded=False):
    if st.session_state.get("is_admin"):
        colA, colB = st.columns([1,1])
        with colA:
            nova_pergunta = st.text_input("Pergunta", key="nova_pergunta")
            novo_email = st.text_input("Email de contacto (opcional)", key="novo_email")
        with colB:
            novo_modelo = st.text_area("Modelo de email (opcional)", height=120, key="novo_modelo")
        nova_resposta = st.text_area("Resposta", height=160, key="nova_resposta")

        if st.button("💾 Guardar nova pergunta"):
            if not (nova_pergunta or "").strip() or not (nova_resposta or "").strip():
                st.error("A pergunta e a resposta são obrigatórias.")
            else:
                ok, msg = adicionar_pergunta(nova_pergunta, nova_resposta, novo_email, novo_modelo)
                if ok:
                    st.success(msg)
                    st.experimental_rerun()
                else:
                    st.error(msg)
    else:
        st.info("Área reservada. Introduza a password para administrar.")

st.markdown("---")

# ==================== Editar / Apagar (admin) ====================
with st.expander("✏️ Editar ou apagar pergunta (admin)", expanded=False):
    if st.session_state.get("is_admin"):
        base = carregar_base()
        lista = [it["pergunta"] for it in base]
        alvo = st.selectbox("Escolha a pergunta a editar:", [""] + lista, key="editar_alvo")

        if alvo:
            atual = next((it for it in base if it["pergunta"] == alvo), None)
            if atual:
                ep = st.text_input("Pergunta", value=atual.get("pergunta", ""), key="ep")
                er = st.text_area("Resposta", value=atual.get("resposta", ""), key="er", height=160)
                ee = st.text_input("Email", value=atual.get("email", ""), key="ee")
                em = st.text_area("Modelo de email (opcional)", value=atual.get("modelo", ""), key="em", height=120)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("💾 Guardar alterações", type="primary"):
                        if not ep.strip():
                            st.error("A pergunta não pode ficar vazia.")
                        else:
                            ok, msg = editar_pergunta(alvo, ep, er, ee, em)
                            if ok:
                                st.success(msg)
                                st.experimental_rerun()
                            else:
                                st.error(msg)
                with c2:
                    with st.popover("🗑️ Apagar pergunta"):
                        st.write("Esta ação é irreversível.")
                        conf = st.checkbox("Confirmo que quero apagar.")
                        if st.button("Apagar definitivamente", disabled=not conf):
                            ok, msg = apagar_pergunta(alvo)
                            if ok:
                                st.success(msg)
                                st.experimental_rerun()
                            else:
                                st.error(msg)
    else:
        st.info("Área reservada. Introduza a password para administrar.")

st.markdown("---")
st.markdown("<small>© 2025 AAC</small>", unsafe_allow_html=True)
