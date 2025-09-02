import json
import os
from datetime import datetime

import streamlit as st
from supabase import create_client, Client

# =========================
# Configurações
# =========================
APP_TITLE = "Felisberto, Assistente Administrativo ACSUTA"
ADMIN_PASSWORD = "decivil2024"  # password pedida em cada secção admin

TABLE_NAME = "base_conhecimento"  # nome da tua tabela no Supabase

# =========================
# Streamlit base
# =========================
st.set_page_config(page_title=APP_TITLE, layout="wide")

# Estilo laranja e layout do cabeçalho com avatar à esquerda
st.markdown(
    """
    <style>
      .stApp { background: #fff7ef; }
      h1.felis-title {
        color: #ef6c00;
        margin: 0;
        line-height: 1.1;
      }
      .felis-header {
        display: flex; align-items: center; gap: 16px; margin: 6px 0 14px 0;
      }
      .felis-avatar { width: 84px; height: 84px; border-radius: 10px; }
      .section-card {
        background: #fff; padding: 18px 20px; border-radius: 12px;
        box-shadow: 0 1px 6px rgba(0,0,0,.06);
      }
      .divider-space { margin: 26px 0; }
      .label-small { color:#666; font-size: 12px; margin: -6px 0 8px; }
      .resp-box {
        background:#fff; border: 1px solid #f0e0d0; border-radius:10px; padding:14px 16px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Cabeçalho com avatar
left, right = st.columns([1, 10])
with left:
    # Certifica-te que o ficheiro existe na raiz do repositório
    st.image("felisberto_avatar.png", use_column_width=False, width=84, caption=None)

with right:
    st.markdown(f"<div class='felis-header'><h1 class='felis-title'>{APP_TITLE}</h1></div>", unsafe_allow_html=True)

# Pequeno espaço visual entre a área de Q&A e as áreas administrativas
st.markdown("<div class='divider-space'></div>", unsafe_allow_html=True)


# =========================
# Funções Supabase
# =========================
@st.cache_resource
def _sb_client() -> Client:
    # Lê do Streamlit Secrets (NÃO coloques no GitHub)
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        st.error("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY não definidas nos secrets.")
        st.stop()
    return create_client(url, key)

def sb_list_all() -> list[dict]:
    """Lista todas as Q&A ordenadas por pergunta."""
    sb = _sb_client()
    res = sb.table(TABLE_NAME).select("*").order("pergunta").execute()
    dados = res.data or []
    out = []
    for r in dados:
        out.append({
            "id": r.get("id"),
            "pergunta": (r.get("pergunta") or "").strip(),
            "resposta": (r.get("resposta") or "").strip(),
            "email": (r.get("email") or "").strip(),
            "modelo_email": (r.get("modelo_email") or "").strip(),
            "created_at": r.get("created_at"),
        })
    return out

def sb_upsert(pergunta: str, resposta: str, email: str, modelo_email: str):
    """Upsert por pergunta (unique)"""
    sb = _sb_client()
    payload = {
        "pergunta": (pergunta or "").strip(),
        "resposta": (resposta or "").strip(),
        "email": (email or "").strip(),
        "modelo_email": (modelo_email or "").strip(),
        "created_at": datetime.utcnow().isoformat()
    }
    sb.table(TABLE_NAME).upsert(payload, on_conflict="pergunta").execute()

def sb_delete_by_pergunta(pergunta: str):
    sb = _sb_client()
    sb.table(TABLE_NAME).delete().eq("pergunta", pergunta.strip()).execute()

def sb_bulk_import(items: list[dict]):
    """Importar lista de Q&A (substitui por pergunta/unique)."""
    sb = _sb_client()
    rows = []
    for it in items:
        rows.append({
            "pergunta": (it.get("pergunta") or "").strip(),
            "resposta": (it.get("resposta") or "").strip(),
            "email": (it.get("email") or "").strip(),
            "modelo_email": (it.get("modelo_email") or it.get("modelo") or "").strip(),
            "created_at": datetime.utcnow().isoformat()
        })
    if rows:
        # upsert em lote
        sb.table(TABLE_NAME).upsert(rows, on_conflict="pergunta").execute()


# =========================
# 1) Perguntas & Respostas
# =========================
st.subheader("📋 Perguntas frequentes")
with st.container():
    base = sb_list_all()
    perguntas = [p["pergunta"] for p in base]
    pergunta_sel = st.selectbox("Escolha uma pergunta:", [""] + perguntas, index=0)

    if pergunta_sel:
        item = next((x for x in base if x["pergunta"] == pergunta_sel), None)
        if item:
            st.markdown("<div class='label-small'>Resposta</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='resp-box'>{item['resposta']}</div>", unsafe_allow_html=True)

            if item.get("email"):
                st.markdown("**Email de contacto:** " + f"[{item['email']}](mailto:{item['email']})")

            if item.get("modelo_email"):
                st.markdown("**Modelo de email sugerido:**")
                st.code(item["modelo_email"], language="text")

# separação visual maior para as secções admin
st.markdown("<div class='divider-space'></div>", unsafe_allow_html=True)


# =========================
# 2) Criar nova pergunta (com password)
# =========================
with st.expander("➕ Criar nova pergunta"):
    pwd = st.text_input("Password", type="password")
    colA, colB = st.columns([1, 1])

    with colA:
        nova_pergunta = st.text_input("Pergunta")
        nova_resposta = st.text_area("Resposta", height=140)
    with colB:
        novo_email = st.text_input("Email (opcional)")
        novo_modelo = st.text_area("Modelo de email (opcional)", height=140)

    if st.button("Guardar nova pergunta"):
        if pwd != ADMIN_PASSWORD:
            st.error("🔒 Password incorreta.")
        elif not nova_pergunta or not nova_resposta:
            st.warning("Preenche pelo menos **Pergunta** e **Resposta**.")
        else:
            try:
                sb_upsert(nova_pergunta, nova_resposta, novo_email, novo_modelo)
                st.success("✅ Pergunta criada/atualizada com sucesso.")
            except Exception as e:
                st.error(f"Erro ao gravar: {e}")


# =========================
# 3) Editar / Apagar existente (com password)
# =========================
with st.expander("✏️ Editar / Apagar pergunta existente"):
    pwd2 = st.text_input("Password", type="password", key="pwd_edit")
    base2 = sb_list_all()
    perguntas2 = [p["pergunta"] for p in base2]
    alvo = st.selectbox("Seleciona a pergunta a editar:", [""] + perguntas2)

    if alvo:
        atual = next((x for x in base2 if x["pergunta"] == alvo), None)
        if atual:
            col1, col2 = st.columns([1, 1])
            with col1:
                e_pergunta = st.text_input("Pergunta", value=atual["pergunta"], key="e_pergunta")
                e_resposta = st.text_area("Resposta", value=atual["resposta"], height=140, key="e_resposta")
            with col2:
                e_email = st.text_input("Email (opcional)", value=atual["email"], key="e_email")
                e_modelo = st.text_area("Modelo de email (opcional)", value=atual["modelo_email"], height=140, key="e_modelo")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Guardar alterações"):
                    if pwd2 != ADMIN_PASSWORD:
                        st.error("🔒 Password incorreta.")
                    else:
                        try:
                            sb_upsert(e_pergunta, e_resposta, e_email, e_modelo)
                            st.success("✅ Alterações guardadas.")
                        except Exception as e:
                            st.error(f"Erro ao gravar: {e}")
            with c2:
                if st.button("🗑️ Apagar esta pergunta"):
                    if pwd2 != ADMIN_PASSWORD:
                        st.error("🔒 Password incorreta.")
                    else:
                        try:
                            sb_delete_by_pergunta(atual["pergunta"])
                            st.success("✅ Pergunta apagada.")
                        except Exception as e:
                            st.error(f"Erro ao apagar: {e}")

# separação visual
st.markdown("<div class='divider-space'></div>", unsafe_allow_html=True)

# =========================
# 4) Importar / Exportar base (com password)
# =========================
with st.expander("⬇️ Download / ⬆️ Upload da base de conhecimento (JSON)"):
    pwd3 = st.text_input("Password", type="password", key="pwd_io")

    # Download
    if st.button("📥 Descarregar JSON"):
        if pwd3 != ADMIN_PASSWORD:
            st.error("🔒 Password incorreta.")
        else:
            try:
                data = sb_list_all()
                txt = json.dumps(
                    [
                        {
                            "pergunta": d["pergunta"],
                            "resposta": d["resposta"],
                            "email": d["email"],
                            "modelo_email": d["modelo_email"],
                        }
                        for d in data
                    ],
                    ensure_ascii=False, indent=2
                )
                st.download_button(
                    label="Download base_conhecimento.json",
                    data=txt.encode("utf-8"),
                    file_name="base_conhecimento.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Erro ao gerar JSON: {e}")

    # Upload
    up = st.file_uploader("Carregar ficheiro JSON", type=["json"])
    if up and st.button("📤 Importar JSON"):
        if pwd3 != ADMIN_PASSWORD:
            st.error("🔒 Password incorreta.")
        else:
            try:
                dados = json.loads(up.read().decode("utf-8"))
                if not isinstance(dados, list):
                    st.error("O JSON deve ser uma lista de objetos.")
                else:
                    sb_bulk_import(dados)
                    st.success("✅ Base importada com sucesso.")
            except Exception as e:
                st.error(f"Erro ao importar: {e}")

# Rodapé
st.markdown("---")
st.markdown("<small>© 2025 AAC</small>", unsafe_allow_html=True)
