# app.py
import json
import os
import streamlit as st

from assistente import (
    ler_base_conhecimento,
    criar_pergunta,
    editar_pergunta,
    apagar_pergunta,
)

# ---------- Config geral ----------
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="centered")

ADMIN_PASSWORD = "decivil2024"
AVATAR_PATH = "felisberto_avatar.png"

# ---------- Estilo ----------
st.markdown(
    """
    <style>
    .stApp { background: #fff7ef; }
    h1, h2, h3 { color: #ef6c00; }
    .caixa { background: white; border: 1px solid #ffd6b3; border-radius: 12px; padding: 18px 20px; }
    .secao { margin-top: 28px; }
    .resposta-box { background: #fff; border-left: 4px solid #ef6c00; padding: 14px 16px; border-radius: 8px; }
    .subtle { color: #7f8c8d; font-size: 0.9rem; }
    .space-lg { margin-top: 34px; }
    .space-md { margin-top: 18px; }
    .space-sm { margin-top: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header com avatar ----------
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try:
        with open(AVATAR_PATH, "rb") as _:
            st.image(AVATAR_PATH, width=80)
    except Exception:
        st.write("")  # ignora se não existir
with col_titulo:
    st.title("Felisberto, Assistente Administrativo ACSUTA")

st.write("Selecione uma pergunta da lista para ver a resposta. As restantes secções são para manutenção da base de conhecimento (com password).")

# ---------- Estado/base em cache ----------
@st.cache_data(show_spinner=False)
def _carregar_base():
    return ler_base_conhecimento()

def _refresh_base():
    st.session_state["_base_cache"] = _carregar_base()

if "_base_cache" not in st.session_state:
    _refresh_base()

def _map_perguntas(base):
    """Devolve listas sincronizadas: labels (texto) e ids/keys (id ou a própria pergunta)."""
    labels = [b.get("pergunta", "") for b in base]
    keys = [b.get("id") or b.get("pergunta") for b in base]
    return labels, keys

base = st.session_state["_base_cache"]
labels, keys = _map_perguntas(base)

# ---------- Secção: Perguntas & Respostas ----------
st.markdown("### ❓ Perguntas e respostas")
with st.container():
    st.markdown('<div class="caixa">', unsafe_allow_html=True)
    pergunta_sel = st.selectbox("Perguntas frequentes:", ["— selecione —"] + labels, index=0)
    if pergunta_sel != "— selecione —":
        # procurar o registo
        reg = next((x for x in base if x.get("pergunta") == pergunta_sel), None)
        if reg:
            st.markdown('<div class="resposta-box">', unsafe_allow_html=True)
            st.markdown(f"**Resposta:**\n\n{reg.get('resposta','').strip() or '_Sem texto_'}")
            email = (reg.get("email") or "").strip()
            if email:
                st.markdown(f"**Email de contacto:** [{email}](mailto:{email})")
            modelo = (reg.get("modelo_email") or "").strip()
            if modelo:
                st.markdown("**Modelo de email sugerido:**")
                st.code(modelo, language="text")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Não encontrei o registo selecionado.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Distância visual ----------
st.markdown('<div class="space-lg"></div>', unsafe_allow_html=True)

# ---------- Secção: Criar Nova ----------
st.markdown("### ➕ Criar nova pergunta")
with st.expander("Abrir/fechar formulário de criação", expanded=False):
    st.markdown('<div class="caixa">', unsafe_allow_html=True)
    pwd_create = st.text_input("Password de administração", type="password", key="pwd_create")
    nova_pergunta = st.text_input("Pergunta")
    nova_resposta = st.text_area("Resposta", height=140)
    novo_email = st.text_input("Email (opcional)")
    novo_modelo = st.text_area("Modelo de email (opcional)", height=120)

    if st.button("Guardar nova pergunta"):
        if pwd_create != ADMIN_PASSWORD:
            st.error("Password incorreta.")
        elif not nova_pergunta.strip() or not nova_resposta.strip():
            st.warning("A pergunta e a resposta são obrigatórias.")
        else:
            try:
                criar_pergunta(nova_pergunta, nova_resposta, novo_email, novo_modelo)
                st.success("Pergunta criada com sucesso.")
                _refresh_base()
            except Exception as e:
                st.error(f"Erro ao criar: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Distância visual ----------
st.markdown('<div class="space-lg"></div>', unsafe_allow_html=True)

# ---------- Secção: Editar existente ----------
st.markdown("### ✏️ Editar pergunta existente")
with st.expander("Abrir/fechar formulário de edição", expanded=False):
    st.markdown('<div class="caixa">', unsafe_allow_html=True)
    base = st.session_state["_base_cache"]
    labels, keys = _map_perguntas(base)
    idx = st.selectbox("Escolher pergunta para editar:", ["— selecione —"] + labels, index=0, key="edit_select")
    if idx != "— selecione —":
        reg = next((x for x in base if x.get("pergunta") == idx), None)
        if reg:
            edit_pwd = st.text_input("Password de administração", type="password", key="pwd_edit")
            novo_p = st.text_input("Nova pergunta", value=reg.get("pergunta",""))
            novo_r = st.text_area("Nova resposta", value=reg.get("resposta",""), height=140)
            novo_e = st.text_input("Novo email", value=reg.get("email",""))
            novo_m = st.text_area("Novo modelo de email (opcional)", value=reg.get("modelo_email",""), height=120)

            colE1, colE2 = st.columns(2)
            if colE1.button("Guardar alterações"):
                if edit_pwd != ADMIN_PASSWORD:
                    st.error("Password incorreta.")
                elif not novo_p.strip() or not novo_r.strip():
                    st.warning("Pergunta e resposta são obrigatórias.")
                else:
                    try:
                        chave = reg.get("id") or reg.get("pergunta")
                        editar_pergunta(chave, novo_p, novo_r, novo_e, novo_m)
                        st.success("Pergunta atualizada.")
                        _refresh_base()
                    except Exception as e:
                        st.error(f"Erro ao editar: {e}")
            if colE2.button("Apagar esta pergunta"):
                if edit_pwd != ADMIN_PASSWORD:
                    st.error("Password incorreta.")
                else:
                    try:
                        chave = reg.get("id") or reg.get("pergunta")
                        apagar_pergunta(chave)
                        st.success("Pergunta apagada.")
                        _refresh_base()
                    except Exception as e:
                        st.error(f"Erro ao apagar: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Distância visual ----------
st.markdown('<div class="space-lg"></div>', unsafe_allow_html=True)

# ---------- Secção: Download / Upload ----------
st.markdown("### ⬇️⬆️ Exportar / Importar base de conhecimento")
with st.expander("Abrir/fechar exportação e importação", expanded=False):
    st.markdown('<div class="caixa">', unsafe_allow_html=True)

    # Download
    base = st.session_state["_base_cache"]
    json_str = json.dumps(base, ensure_ascii=False, indent=2)
    st.download_button(
        label="⬇️ Descarregar JSON",
        data=json_str.encode("utf-8"),
        file_name="base_conhecimento_export.json",
        mime="application/json",
    )

    # Upload (merge por pergunta)
    up_pwd = st.text_input("Password para importar", type="password", key="pwd_import")
    up_file = st.file_uploader("Carregar ficheiro JSON para importar (merge por pergunta)", type=["json"])
    if up_file is not None:
        try:
            novo_conteudo = json.load(up_file)
            if not isinstance(novo_conteudo, list):
                st.error("O JSON deve conter uma lista de objetos.")
            else:
                if up_pwd != ADMIN_PASSWORD:
                    st.error("Password incorreta.")
                else:
                    # Merge pergunta->registo
                    atual = {x.get("pergunta"): x for x in ler_base_conhecimento()}
                    for item in novo_conteudo:
                        p = (item.get("pergunta") or "").strip()
                        if not p:
                            continue
                        atual[p] = {
                            "pergunta": p,
                            "resposta": (item.get("resposta") or "").strip(),
                            "email": (item.get("email") or "").strip(),
                            "modelo_email": (item.get("modelo_email") or "").strip(),
                        }
                    # Gravar via API, respeitando destinos
                    # estratégia: apagar tudo local e recriar? Aqui vamos atualizar/insert por pergunta
                    for p, payload in atual.items():
                        # tenta editar; se não existir, cria
                        try:
                            editar_pergunta(p, payload["pergunta"], payload["resposta"], payload["email"], payload["modelo_email"])
                        except Exception:
                            criar_pergunta(payload["pergunta"], payload["resposta"], payload["email"], payload["modelo_email"])
                    st.success("Importação concluída.")
                    _refresh_base()
        except json.JSONDecodeError:
            st.error("JSON inválido.")
        except Exception as e:
            st.error(f"Erro a importar: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Rodapé ----------
st.markdown("---")
st.markdown('<div class="subtle">© 2025 AAC</div>', unsafe_allow_html=True)
