# -*- coding: utf-8 -*-
import io
import json
from typing import List, Dict, Any
import streamlit as st
import os
import difflib

import assistente as backend

st.set_page_config(page_title="Assist-Decivil", page_icon="🧑‍💼", layout="wide")

# Cabeçalho com avatar (se existir)
avatar_path = os.path.join(os.path.dirname(__file__), "assets", "felisberto_avatar.png")
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists(avatar_path):
        st.image(avatar_path, width=96)
with col_title:
    st.title("Assist-Decivil")
    st.caption("Gestão de base de conhecimento + geração de e-mails — v2")

# Estado de sessão (admin)
if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False

def _is_admin() -> bool:
    return bool(st.session_state.admin_ok)

def _check_admin(pwd: str) -> bool:
    ok = (pwd or "") == (backend.PASSWORD or "")
    st.session_state.admin_ok = ok
    return ok

# Funções utilitárias
@st.cache_data(show_spinner=False)
def _load_base() -> List[Dict[str, Any]]:
    return backend.ler_base_conhecimento()

def _reload():
    _load_base.clear()  # type: ignore
    _load_base()

def _filtrar(busca: str, dados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    b = (busca or "").strip().lower()
    if not b:
        return dados
    # procura direta em pergunta/resposta
    res = [d for d in dados if b in (d.get("pergunta","").lower()) or b in (d.get("resposta","").lower())]
    # se muito curto, devolve já
    if len(res) >= 1 or len(b) < 3:
        return res
    # fuzzy match por pergunta
    perguntas = [d.get("pergunta","") for d in dados]
    candidatos = difflib.get_close_matches(b, [p.lower() for p in perguntas], n=10, cutoff=0.6)
    final = []
    for d in dados:
        if d.get("pergunta","").lower() in candidatos:
            final.append(d)
    return final or res

abas = st.tabs(["🔎 Consultar", "🗂️ Gerir Base", "⬆️ Importar / ⬇️ Exportar", "🧠 Embeddings"])

# --- Consultar ---
with abas[0]:
    st.subheader("Pesquisar")
    q = st.text_input("O que procura?", placeholder="ex.: Como posso reservar uma sala?")
    dados = _load_base()
    filtrados = _filtrar(q, dados) if q else dados

    st.write(f"Encontrados: **{len(filtrados)}** registos")
    for item in filtrados:
        with st.expander(item.get("pergunta","(sem título)")):
            st.markdown(item.get("resposta","").strip() or "_Sem resposta._")
            if item.get("email"):
                st.write("**Email:** ", item.get("email"))
            if item.get("modelo_email"):
                st.text_area("Modelo de email", value=item.get("modelo_email","").strip(), height=140)

# --- Gerir Base ---
with abas[1]:
    st.subheader("Administração")
    if not _is_admin():
        pwd = st.text_input("Password de administração", type="password")
        if st.button("Entrar", type="primary"):
            if _check_admin(pwd):
                st.success("Sessão iniciada.")
            else:
                st.error("Password incorreta.")
        st.stop()

    dados = _load_base()
    ids = [d.get("id") for d in dados]
    labels = [f'{d.get("pergunta","(sem título)")[:70]}… [{d.get("id","")[:8]}]' for d in dados]
    idx = st.selectbox("Selecionar registo para editar (opcional)", options=list(range(len(dados))), format_func=lambda i: labels[i] if labels else "", index=None, placeholder="— novo registo —")

    if idx is None:
        item = {"pergunta":"", "resposta":"", "email":"", "modelo_email":""}
    else:
        item = dict(dados[idx])

    with st.form("form_registo", clear_on_submit=False):
        pergunta = st.text_input("Pergunta", value=item.get("pergunta",""))
        resposta = st.text_area("Resposta", value=item.get("resposta",""), height=200)
        email = st.text_input("Email (contacto)", value=item.get("email",""))
        modelo_email = st.text_area("Modelo de email (opcional)", value=item.get("modelo_email",""), height=160)
        c1, c2, c3 = st.columns(3)
        submitted = c1.form_submit_button("Guardar", type="primary")
        if idx is not None:
            apagar = c2.form_submit_button("Apagar", type="secondary")
        else:
            apagar = False

    if submitted:
        backend.sb_upsert(pergunta, resposta, email, modelo_email)
        st.success("Registo guardado.")
        _reload()

    if apagar and idx is not None:
        try:
            backend.sb_delete_by_pergunta(item.get("pergunta",""))
            st.success("Registo apagado.")
            _reload()
        except Exception as e:
            st.error(f"Erro ao apagar: {e}")

# --- Importar/Exportar ---
with abas[2]:
    st.subheader("Exportar")
    b = backend.exportar_toda_base_json()
    st.download_button("Descarregar base em JSON", b, file_name="base_conhecimento.export.json", mime="application/json")

    st.subheader("Importar")
    st.caption("Importe uma lista de objetos com os campos: pergunta, resposta, email, modelo_email. (Opcionalmente com 'id').")
    up = st.file_uploader("Escolha um ficheiro JSON", type=["json"])
    if up is not None:
        try:
            raw = up.read()
            n = backend.sb_bulk_import(raw)
            st.success(f"Importados {n} registos.")
            _reload()
        except Exception as e:
            st.error(f"Falhou importação: {e}")

# --- Embeddings ---
with abas[3]:
    st.subheader("Geração de embeddings")
    st.write("""
Para gerar o ficheiro **base_knowledge_vector.json** com embeddings, execute no terminal:
```bash
export OPENAI_API_KEY="...a_tua_chave..."
python gerar_embeddings.py --modelo text-embedding-3-small --saida base_knowledge_vector.json
```
O script usa Supabase se estiver configurado; caso contrário, usa o ficheiro `base_conhecimento.json`.
""")
    # Mostra estado do ficheiro local (se existir)
    from pathlib import Path
    vec_path = Path(backend.VECTOR_JSON_PATH)
    if vec_path.exists():
        st.info(f"Ficheiro de embeddings encontrado: {vec_path} ({vec_path.stat().st_size} bytes)")
    else:
        st.warning("Ainda não existe ficheiro de embeddings. Use o comando acima para o gerar.")
