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
    # 1) Local
    if os.path.exists("felisberto_avatar.png"):
        return '<img src="felisberto_avatar.png" alt="Felisberto">'
    # 2) RAW GitHub (ajusta URL se precisares)
    raw_url = "https://raw.githubusercontent.com/aguiarcost/assist-decivil/main/felisberto_avatar.png"
    return f'<img src="{raw_url}" alt="Felisberto" onerror="this.style.display=\'none\'">'

st.markdown(f"""
<div class="titulo-container">
  {_avatar_html()}
  <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
</div>
<div class="block-after-title"></div>
""", unsafe_allow_html=True)

# ==================== Password helper (por secção) ====================
ADMIN_PASSWORD_DEFAULT = "decivil2024"

def obter_admin_password_config():
    try:
        if "ADMIN_PASSWORD" in st.secrets:
            return str(st.secrets["ADMIN_PASSWORD"])
    except Exception:
        pass
    return os.getenv("ADMIN_PASSWORD", ADMIN_PASSWORD_DEFAULT)

def valida_pw(input_value: str) -> bool:
    return (input_value or "") == obter_admin_password_config()

# ==================== 1) Perguntas & respostas ====================
st.subheader("Faça a sua pergunta")

perguntas = carregar_perguntas_frequentes()
if not perguntas:
    st.info("Ainda não existem perguntas na base. Use a secção **Adicionar nova pergunta** para criar a primeira.")
pergunta_escolhida = st.selectbox(
    "Escolha uma pergunta frequente:",
    [""] + perguntas,
    key="pergunta_dropdown"
)

if pergunta_escolhida.strip():
    resposta_txt, modelo_txt = gerar_resposta(pergunta_escolhida)
    st.markdown("### 💡 Resposta do assistente")
    st.markdown(resposta_txt, unsafe_allow_html=True)

    if modelo_txt:
        st.markdown("### 📨 Modelo de email sugerido")
        st.code(modelo_txt, language="text")

st.markdown("---")

# ==================== 2) Adicionar nova pergunta (com password) ====================
with st.expander("➕ Adicionar nova pergunta"):
    col_pw, _ = st.columns([1,3])
    with col_pw:
        pw_add = st.text_input("Password (admin)", type="password", key="pw_add")
    autorizado_add = valida_pw(pw_add)

    colA, colB = st.columns([1,1])
    with colA:
        nova_pergunta = st.text_input("Pergunta", key="nova_pergunta")
        novo_email = st.text_input("Email de contacto (opcional)", key="novo_email")
    with colB:
        novo_modelo = st.text_area("Modelo de email (opcional)", height=120, key="novo_modelo")
    nova_resposta = st.text_area("Resposta", height=160, key="nova_resposta")

    btn_add = st.button("💾 Guardar nova pergunta", disabled=not autorizado_add, key="btn_add_nova")
    if not autorizado_add and (nova_pergunta or nova_resposta or novo_email or novo_modelo):
        st.info("Introduza a password para ativar o botão de guardar.")

    if btn_add:
        if not (nova_pergunta or "").strip() or not (nova_resposta or "").strip():
            st.error("A pergunta e a resposta são obrigatórias.")
        else:
            ok, msg = adicionar_pergunta(nova_pergunta, nova_resposta, novo_email, novo_modelo)
            if ok:
                st.success(msg)
                st.experimental_rerun()
            else:
                st.error(msg)

st.markdown("---")

# ==================== 3) Editar / Apagar (com password) ====================
with st.expander("✏️ Editar ou apagar pergunta"):
    col_pw2, _ = st.columns([1,3])
    with col_pw2:
        pw_edit = st.text_input("Password (admin)", type="password", key="pw_edit")
    autorizado_edit = valida_pw(pw_edit)

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
                save_clicked = st.button("💾 Guardar alterações", type="primary", key="btn_save_edit", disabled=not autorizado_edit)
                if not autorizado_edit and (ep != atual.get("pergunta") or er != atual.get("resposta") or ee != atual.get("email") or em != atual.get("modelo")):
                    st.info("Introduza a password para ativar o botão de guardar.")
                if autorizado_edit and save_clicked:
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
                del_clicked = st.button("🗑️ Apagar pergunta", key="btn_delete", disabled=not autorizado_edit)
                if not autorizado_edit and alvo:
                    st.info("Introduza a password para ativar o botão de apagar.")
                if autorizado_edit and del_clicked:
                    ok, msg = apagar_pergunta(alvo)
                    if ok:
                        st.success(msg)
                        st.experimental_rerun()
                    else:
                        st.error(msg)

st.markdown("---")

# ==================== 4) Importar / Exportar (com password) ====================
with st.expander("📦 Importar / Exportar base de conhecimento"):
    col_pw3, _ = st.columns([1,3])
    with col_pw3:
        pw_io = st.text_input("Password (admin)", type="password", key="pw_io")
    autorizado_io = valida_pw(pw_io)

    col_exp, col_imp = st.columns(2)

    with col_exp:
        st.caption("Descarregar uma cópia da base atual:")
        data = exportar_base_bytes()
        st.download_button(
            label="⬇️ Download base_conhecimento.json",
            data=data,
            file_name="base_conhecimento.json",
            mime="application/json",
            key="download_base",
            disabled=not autorizado_io
        )
        if not autorizado_io:
            st.info("Introduza a password para ativar o download.")

    with col_imp:
        st.caption("Importar (substitui a base atual):")
        up = st.file_uploader("Escolher JSON", type="json", key="upload_base", disabled=not autorizado_io)
        if not autorizado_io:
            st.info("Introduza a password para ativar o upload.")
        if autorizado_io and up:
            ok, msg = importar_base_de_bytes(up.read())
            if ok:
                st.success(msg)
                st.experimental_rerun()
            else:
                st.error(msg)

st.markdown("---")
st.markdown("<small>© 2025 AAC</small>", unsafe_allow_html=True)
