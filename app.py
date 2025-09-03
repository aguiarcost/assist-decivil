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

ADMIN_PASSWORD = "decivil2024"
AVATAR_FILENAME = "felisberto_avatar.png"   # colocar na raiz do projeto

# =========================
# Estilos
# =========================
st.markdown(
    """
    <style>
      .stApp { background: #fff7ef; }

      /* Títulos */
      h1 {
        color: #ef6c00;
        font-size: 2.4rem;
        margin-bottom: 0.6rem;
      }
      h2 {
        color: #ef6c00;
        font-size: 1.3rem;
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
      }
      h3 {
        color: #ef6c00;
        font-size: 1.1rem;
        margin-top: 1rem;
        margin-bottom: 0.3rem;
      }

      /* Header com avatar + título */
      .header-flex {
        display: flex;
        align-items: center;
        gap: 14px;
      }
      .title-tight {
        margin: 0;
        padding: 0;
        line-height: 1.1;
      }

      /* Caixas brancas */
      .caixa {
        background: #fff;
        border: 1px solid #ffd6b3;
        border-radius: 12px;
        padding: 18px 20px;
      }
      .resposta-box {
        background: #fff;
        border-left: 4px solid #ef6c00;
        padding: 14px 16px;
        border-radius: 8px;
        margin-top: 12px;
        margin-bottom: 20px;
      }

      /* Espaçamentos verticais */
      .space-xl { margin-top: 36px; }
      .space-lg { margin-top: 28px; }
      .space-md { margin-top: 18px; }

      .subtle { color: #7f8c8d; font-size: 0.9rem; }
      .separador-visual { height: 26px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Header com avatar
# =========================
def _avatar_html() -> str:
    """Mostra o avatar se existir; caso contrário, mostra só o título."""
    # Em alguns ambientes __file__ pode não existir
    try:
        root = os.path.dirname(__file__)
    except NameError:
        root = os.getcwd()

    avatar_path = os.path.join(root, AVATAR_FILENAME)
    if os.path.exists(avatar_path):
        try:
            with open(avatar_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"""
              <div class="header-flex">
                  <img src="data:image/png;base64,{b64}" alt="avatar" width="72" style="margin-top:-4px" />
                  <h1 class="title-tight">Felisberto, Assistente Administrativo ACSUTA</h1>
              </div>
            """
        except Exception:
            pass  # se falhar leitura, cai no fallback abaixo

    return '<h1 class="title-tight">Felisberto, Assistente Administrativo ACSUTA</h1>'

st.markdown(_avatar_html(), unsafe_allow_html=True)
st.write(
    "Selecione uma pergunta da lista para ver a resposta. As secções abaixo permitem **criar**, "
    "**editar/apagar** e **exportar/importar** a base de conhecimento (cada uma protegida por password)."
)

# =========================
# Cache e helpers
# =========================
@st.cache_data(show_spinner=False)
def _carregar_base():
    """Lê a base de conhecimento do backend (ficheiro/Supabase, conforme assistente.py)."""
    return ler_base_conhecimento()

def _refresh_base():
    st.session_state["_base_cache"] = _carregar_base()

if "_base_cache" not in st.session_state:
    _refresh_base()

def _labels_e_chaves(base):
    labels = [r.get("pergunta", "") for r in base]
    chaves = [r.get("id") or r.get("pergunta") for r in base]
    return labels, chaves

# =========================
# Secção: Perguntas & Respostas
# =========================
st.markdown("### ❓ Perguntas e respostas")

base = st.session_state["_base_cache"]
labels, chaves = _labels_e_chaves(base)

# Selectbox com valor inicial em branco (string vazia)
pergunta_sel = st.selectbox("Perguntas frequentes:", [""] + labels, index=0, key="faq_select")

# Só prossegue se foi feita uma seleção válida
if pergunta_sel.strip():
    reg = next((x for x in base if x.get("pergunta") == pergunta_sel), None)

    if reg:
        #st.markdown('<div class="resposta-box">', unsafe_allow_html=True)
        st.markdown(f"**Resposta**\n\n{(reg.get('resposta') or '').strip() or '_Sem texto_'}")

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

# Separação visual grande
st.markdown('<div class="space-xl"></div>', unsafe_allow_html=True)

# =========================
# Secção: Criar nova pergunta
# =========================
st.markdown("### ➕ Criar nova pergunta")
with st.expander("Abrir/fechar formulário de criação", expanded=False):
 #   st.markdown('<div class="caixa">', unsafe_allow_html=True)

    pwd_create = st.text_input("Password de administração", type="password", key="pwd_create")
    nova_pergunta = st.text_input("Pergunta")
    nova_resposta = st.text_area("Resposta", height=140)
    novo_email = st.text_input("Email (opcional)")
    novo_modelo = st.text_area("Modelo de email (opcional)", height=120)

    if st.button("Guardar nova pergunta", key="btn_criar"):
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

# Separação visual média
st.markdown('<div class="space-lg"></div>', unsafe_allow_html=True)

# =========================
# Secção: Editar / Apagar
# =========================
st.markdown("### ✏️ Editar pergunta existente")
with st.expander("Abrir/fechar formulário de edição", expanded=False):
 #   st.markdown('<div class="caixa">', unsafe_allow_html=True)

    base = st.session_state["_base_cache"]
    labels, chaves = _labels_e_chaves(base)
    alvo = st.selectbox("Escolher pergunta:", ["— selecione —"] + labels, index=0, key="edit_select")

    if alvo != "— selecione —":
        reg = next((x for x in base if x.get("pergunta") == alvo), None)
        if reg:
            pwd_edit = st.text_input("Password de administração", type="password", key="pwd_edit")

            novo_p = st.text_input("Nova pergunta", value=reg.get("pergunta", ""), key="nova_pergunta_edit")
            novo_r = st.text_area("Nova resposta", value=reg.get("resposta", ""), height=140, key="nova_resposta_edit")
            novo_e = st.text_input("Novo email", value=reg.get("email", ""), key="novo_email_edit")
            novo_m = st.text_area("Novo modelo de email (opcional)", value=reg.get("modelo_email", ""), height=120, key="novo_modelo_edit")

            col1, col2 = st.columns(2)

            if col1.button("Guardar alterações", key="btn_guardar_edicao"):
                if pwd_edit != ADMIN_PASSWORD:
                    st.error("Password incorreta.")
                elif not novo_p.strip() or not novo_r.strip():
                    st.warning("Pergunta e resposta são obrigatórias.")
                else:
                    try:
                        chave_reg = reg.get("id") or reg.get("pergunta")
                        editar_pergunta(chave_reg, novo_p, novo_r, novo_e, novo_m)
                        st.success("Pergunta atualizada.")
                        _refresh_base()
                    except Exception as e:
                        st.error(f"Erro ao editar: {e}")

            if col2.button("Apagar esta pergunta", type="secondary", key="btn_apagar"):
                if pwd_edit != ADMIN_PASSWORD:
                    st.error("Password incorreta.")
                else:
                    try:
                        chave_reg = reg.get("id") or reg.get("pergunta")
                        apagar_pergunta(chave_reg)
                        st.success("Pergunta apagada.")
                        _refresh_base()
                    except Exception as e:
                        st.error(f"Erro ao apagar: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

# Separação visual
st.markdown('<div class="space-lg"></div>', unsafe_allow_html=True)

# =========================
# Secção: Exportar / Importar
# =========================
st.markdown("### ⬇️⬆️ Exportar / Importar base de conhecimento")
with st.expander("Abrir/fechar exportação e importação", expanded=False):
#    st.markdown('<div class="caixa">', unsafe_allow_html=True)

    base = st.session_state["_base_cache"]
    json_str = json.dumps(base, ensure_ascii=False, indent=2)
    st.download_button(
        "⬇️ Descarregar JSON",
        data=json_str.encode("utf-8"),
        file_name="base_conhecimento_export.json",
        mime="application/json",
    )

    up_pwd = st.text_input("Password para importar", type="password", key="pwd_import")
    up_file = st.file_uploader("Carregar ficheiro JSON (lista de objetos)", type=["json"])

    if up_file is not None:
        try:
            novo_conteudo = json.loads(up_file.read().decode("utf-8"))
        except Exception:
            st.error("JSON inválido. Verifique o ficheiro.")
            novo_conteudo = None

        if novo_conteudo is not None:
            if not isinstance(novo_conteudo, list):
                st.error("O JSON deve conter uma lista de objetos.")
            elif up_pwd != ADMIN_PASSWORD:
                st.error("Password incorreta.")
            else:
                # Merge por pergunta (atualiza existentes, cria novos)
                atual_map = {x.get("pergunta"): x for x in ler_base_conhecimento()}
                for item in novo_conteudo:
                    p = (item.get("pergunta") or "").strip()
                    if not p:
                        continue
                    atual_map[p] = {
                        "pergunta": p,
                        "resposta": (item.get("resposta") or "").strip(),
                        "email": (item.get("email") or "").strip(),
                        "modelo_email": (item.get("modelo_email") or "").strip(),
                    }

                # Aplica alterações
                criados, editados = 0, 0
                for p, payload in atual_map.items():
                    try:
                        # tenta editar: se não existir, a tua função deve sinalizar
                        editar_pergunta(
                            p, payload["pergunta"], payload["resposta"], payload["email"], payload["modelo_email"]
                        )
                        editados += 1
                    except Exception:
                        try:
                            criar_pergunta(
                                payload["pergunta"], payload["resposta"], payload["email"], payload["modelo_email"]
                            )
                            criados += 1
                        except Exception:
                            pass

                st.success(f"Importação concluída. Atualizados: {editados}, Criados: {criados}.")
                _refresh_base()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# Rodapé
# =========================
st.markdown("---")
st.markdown('<div class="subtle">© 2025 AAC</div>', unsafe_allow_html=True)
