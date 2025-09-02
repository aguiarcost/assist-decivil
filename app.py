import streamlit as st
import os
from assistente import (
    carregar_perguntas_frequentes,
    gerar_resposta,
    adicionar_pergunta,
    editar_pergunta,
    apagar_pergunta,
    carregar_base,
)

st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

# ---------- Estilo laranja + título com avatar ----------
st.markdown("""
<style>
.stApp { background-color: #fff3e0; }
.titulo-container { display:flex; align-items:center; gap:12px; margin:10px 0 18px 0; }
.titulo-container img { width:72px; height:auto; }
.titulo-container h1 { color:#ef6c00; font-size:2.0rem; margin:0; }
hr { border:none; border-top:1px solid #f0b27a; margin: .8rem 0 1.2rem 0; }

/* espaço extra abaixo do título */
.block-after-title { margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

avatar_local = "felisberto_avatar.png"
avatar_html = f'<img src="{avatar_local}" alt="Felisberto">' if os.path.exists(avatar_local) else ""

st.markdown(f"""
<div class="titulo-container">
  {avatar_html}
  <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
</div>
<div class="block-after-title"></div>
""", unsafe_allow_html=True)

# ---------- Pergunta principal (só dropdown) ----------
st.subheader("Faça a sua pergunta")

perguntas = carregar_perguntas_frequentes()
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

# ---------- Adicionar pergunta (EXPANDER) ----------
with st.expander("➕ Adicionar nova pergunta", expanded=False):
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

st.markdown("---")

# ---------- Editar / Apagar pergunta (EXPANDER) ----------
with st.expander("✏️ Editar ou apagar pergunta", expanded=False):
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

st.markdown("---")
st.markdown("<small>© 2025 AAC</small>", unsafe_allow_html=True)
