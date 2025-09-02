import streamlit as st
import json, os
from datetime import datetime

from assistente import (
    gerar_resposta,
    carregar_perguntas_frequentes,
)

from preparar_documentos_streamlit import processar_documento

# ----------------- Config -----------------
st.set_page_config(page_title="Felisberto, Assistente Administrativo ACSUTA", layout="wide")

CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_HISTORICO = "historico_perguntas.json"
CAMINHO_VETORIZADA = "base_vectorizada.json"
CAMINHO_LOG = "edicoes_log.json"

# CSS tema laranja + título com avatar
st.markdown("""
<style>
.stApp { background-color: #fff3e0; }
.titulo-container { display:flex; align-items:center; gap:12px; margin:10px 0 18px 0; }
.titulo-container img { width:72px; height:auto; }
.titulo-container h1 { color:#ef6c00; font-size:2.0rem; margin:0; }
hr { border: none; border-top: 1px solid #f0b27a; margin: 0.8rem 0 1.2rem 0; }
</style>
""", unsafe_allow_html=True)

# Avatar + Título (usa ficheiro local; se não existir, mostra sem avatar)
avatar_path = "felisberto_avatar.png"
avatar_html = f'<img src="app/{avatar_path}" alt="Avatar">' if os.path.exists(f"app/{avatar_path}") else (f'<img src="{avatar_path}" alt="Avatar">' if os.path.exists(avatar_path) else "")
st.markdown(f"""
<div class="titulo-container">
  {avatar_html}
  <h1>Felisberto, Assistente Administrativo ACSUTA</h1>
</div>
""", unsafe_allow_html=True)

# ----------------- Helpers JSON -----------------
def _ler_json(caminho, default):
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def _escrever_json(caminho, conteudo):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)

def _guardar_no_historico(pergunta):
    registo = {"pergunta": pergunta, "timestamp": datetime.now().isoformat()}
    historico = _ler_json(CAMINHO_HISTORICO, [])
    historico.append(registo)
    _escrever_json(CAMINHO_HISTORICO, historico)

# ----------------- Zona de Perguntas -----------------
st.subheader("Faça a sua pergunta")

# Perguntas frequentes (ordenadas por frequência de uso)
base_conhecimento = _ler_json(CAMINHO_CONHECIMENTO, [])
frequencia = {}
for item in _ler_json(CAMINHO_HISTORICO, []):
    p = item.get("pergunta")
    if p:
        frequencia[p] = frequencia.get(p, 0) + 1

perguntas_frequentes = carregar_perguntas_frequentes()
perguntas_frequentes = sorted(perguntas_frequentes, key=lambda x: -frequencia.get(x, 0))

col1, col2 = st.columns(2)
with col1:
    drop = st.selectbox("Escolha uma pergunta frequente:", [""] + perguntas_frequentes, key="pergunta_dropdown")
with col2:
    livre = st.text_input("Ou escreva a sua pergunta:", key="pergunta_livre")

pergunta_final = (livre or "").strip() if (livre or "").strip() else (drop or "").strip()

# Botão para submeter e forçar refresh consistente
if st.button("🔎 Obter resposta", type="primary"):
    if pergunta_final:
        with st.spinner("A pensar..."):
            usar_embedding = bool((livre or "").strip())
            resposta_md = gerar_resposta(pergunta_final, usar_embedding=usar_embedding)
            _guardar_no_historico(pergunta_final)
            st.session_state["ultima_resposta"] = resposta_md
            st.session_state["ultima_pergunta"] = pergunta_final
    else:
        st.warning("Escreva uma pergunta ou escolha uma das perguntas frequentes.")

# Mostrar a resposta estável
if "ultima_resposta" in st.session_state and st.session_state.get("ultima_pergunta"):
    st.markdown("### 💡 Resposta do assistente")
    st.markdown(st.session_state["ultima_resposta"], unsafe_allow_html=True)

st.markdown("---")

# ----------------- Upload de Documentos / URLs -----------------
st.subheader("📎 Adicionar documentos ou links")
col3, col4 = st.columns(2)

with col3:
    ficheiro = st.file_uploader("Ficheiro (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"], key="uploader_docs")
    if ficheiro:
        try:
            processar_documento(ficheiro)
            st.success("✅ Documento processado com sucesso.")
        except Exception as e:
            st.error(f"Erro ao processar documento: {e}")

with col4:
    url = st.text_input("Ou insira um link para processar conteúdo:", key="url_input")
    if st.button("📥 Processar URL"):
        if url.strip():
            try:
                processar_documento(url.strip())
                st.success("✅ Conteúdo do link processado com sucesso.")
            except Exception as e:
                st.error(f"Erro ao processar URL: {e}")
        else:
            st.warning("Insira um link válido.")

st.markdown("---")

# ----------------- Atualizar Base via JSON + Adicionar Manualmente -----------------
st.subheader("📝 Atualizar/Adicionar perguntas")

# Upload JSON (lista de perguntas)
novo_json = st.file_uploader("Adicionar ficheiro JSON com novas perguntas", type="json", key="uploader_json")
if novo_json:
    try:
        novas = json.load(novo_json)
        if isinstance(novas, list):
            atual = _ler_json(CAMINHO_CONHECIMENTO, [])
            by_q = {p.get("pergunta", ""): p for p in atual if isinstance(p, dict)}
            for item in novas:
                q = (item.get("pergunta") or "").strip()
                if not q:
                    continue
                # Normalizar campos
                by_q[q] = {
                    "pergunta": q,
                    "resposta": (item.get("resposta") or "").strip(),
                    "email": (item.get("email") or "").strip(),
                    "modelo": (item.get("modelo") or item.get("modelo_email") or "").strip()
                }
            _escrever_json(CAMINHO_CONHECIMENTO, list(by_q.values()))
            st.success("✅ Base de conhecimento atualizada (JSON).")
        else:
            st.error("O ficheiro JSON deve conter uma lista de objetos.")
    except Exception as e:
        st.error(f"Erro ao ler ficheiro JSON: {e}")

with st.expander("➕ Adicionar pergunta manualmente"):
    npq = st.text_input("Pergunta nova", key="nova_pergunta")
    nrs = st.text_area("Resposta", key="nova_resposta")
    nem = st.text_input("Email (opcional)", key="novo_email")
    nmd = st.text_area("Modelo de email (opcional)", key="novo_modelo")

    if st.button("💾 Guardar nova pergunta"):
        if not (npq or "").strip() or not (nrs or "").strip():
            st.error("Preenche pelo menos a pergunta e a resposta.")
        else:
            atual = _ler_json(CAMINHO_CONHECIMENTO, [])
            # evitar duplicados
            if any((e.get("pergunta", "").strip().lower() == npq.strip().lower()) for e in atual):
                st.error("Já existe uma pergunta idêntica.")
            else:
                atual.append({
                    "pergunta": npq.strip(),
                    "resposta": (nrs or "").strip(),
                    "email": (nem or "").strip(),
                    "modelo": (nmd or "").strip()
                })
                _escrever_json(CAMINHO_CONHECIMENTO, atual)
                st.success("✅ Pergunta adicionada.")
                st.experimental_rerun()

st.markdown("---")

# ----------------- Editor: pesquisar, editar e APAGAR pergunta -----------------
st.subheader("✏️ Editar ou apagar pergunta")

def _log_acao(acao, antes=None, depois=None):
    reg = _ler_json(CAMINHO_LOG, [])
    reg.append({
        "timestamp": datetime.now().isoformat(),
        "acao": acao,
        "antes": antes,
        "depois": depois
    })
    _escrever_json(CAMINHO_LOG, reg)

def _remover_dos_embeddings(pergunta_alvo):
    if not os.path.exists(CAMINHO_VETORIZADA):
        return
    base_vec = _ler_json(CAMINHO_VETORIZADA, [])
    if not isinstance(base_vec, list):
        return
    filtrada = []
    for item in base_vec:
        if isinstance(item, dict) and item.get("pergunta"):
            if item.get("pergunta") == pergunta_alvo:
                continue
        filtrada.append(item)
    _escrever_json(CAMINHO_VETORIZADA, filtrada)

base_atual = _ler_json(CAMINHO_CONHECIMENTO, [])
lista_perguntas = sorted({e.get("pergunta", "") for e in base_atual if isinstance(e, dict) and e.get("pergunta")})

if not lista_perguntas:
    st.info("Ainda não há perguntas na base para editar.")
else:
    termo = st.text_input("🔎 Pesquisar na base (filtra por texto):", key="pesquisa_editor")
    opcoes = [p for p in lista_perguntas if (termo or "").lower() in p.lower()] if termo else list(lista_perguntas)

    alvo = st.selectbox("Escolha a pergunta a editar/apagar:", opcoes, key="editar_select")

    entrada = next((e for e in base_atual if e.get("pergunta") == alvo), None)
    if entrada:
        ep = st.text_input("Pergunta", value=entrada.get("pergunta", ""), key="editar_pergunta")
        er = st.text_area("Resposta", value=entrada.get("resposta", ""), key="editar_resposta", height=180)
        ee = st.text_input("Email", value=entrada.get("email", ""), key="editar_email")
        em = st.text_area("Modelo (opcional)", value=entrada.get("modelo", "") or entrada.get("modelo_email", ""), key="editar_modelo", height=150)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Guardar alterações", type="primary", use_container_width=True):
                if not ep.strip():
                    st.error("A pergunta não pode ficar vazia.")
                else:
                    # evitar duplicados se mudou o texto
                    if ep.strip().lower() != alvo.strip().lower():
                        if any((e.get("pergunta", "").strip().lower() == ep.strip().lower()) for e in base_atual):
                            st.error("Já existe uma pergunta idêntica.")
                            st.stop()
                    antes = {
                        "pergunta": entrada.get("pergunta"),
                        "resposta": entrada.get("resposta"),
                        "email": entrada.get("email"),
                        "modelo": entrada.get("modelo") or entrada.get("modelo_email")
                    }
                    for i, it in enumerate(base_atual):
                        if it is entrada:
                            base_atual[i] = {
                                "pergunta": ep.strip(),
                                "resposta": (er or "").strip(),
                                "email": (ee or "").strip(),
                                "modelo": (em or "").strip()
                            }
                            break
                    _escrever_json(CAMINHO_CONHECIMENTO, base_atual)
                    _log_acao("editar", antes=antes, depois=base_atual[i])
                    st.success("✅ Alterações guardadas.")
                    st.experimental_rerun()

        with c2:
            with st.expander("⚠️ Apagar pergunta"):
                st.warning("Esta ação é irreversível.")
                conf = st.checkbox("Confirmo que quero apagar.")
                if st.button("🗑️ Apagar pergunta", use_container_width=True, disabled=not conf):
                    _log_acao("apagar", antes={
                        "pergunta": entrada.get("pergunta"),
                        "resposta": entrada.get("resposta"),
                        "email": entrada.get("email"),
                        "modelo": entrada.get("modelo") or entrada.get("modelo_email")
                    })
                    nova = [e for e in base_atual if e is not entrada]
                    _escrever_json(CAMINHO_CONHECIMENTO, nova)
                    _remover_dos_embeddings(alvo)
                    st.success("🗑️ Pergunta apagada.")
                    st.experimental_rerun()

st.markdown("---")
with st.expander("🗄️ Histórico de edições"):
    log = _ler_json(CAMINHO_LOG, [])
    if not log:
        st.write("Sem registos.")
    else:
        for item in reversed(log[-100:]):
            st.write(f"**{item['acao'].upper()}** — {item['timestamp']}")
            if item.get("antes"):
                st.code(json.dumps(item["antes"], ensure_ascii=False, indent=2), language="json")
            if item.get("depois"):
                st.code(json.dumps(item["depois"], ensure_ascii=False, indent=2), language="json")
            st.markdown("---")

# Rodapé
st.markdown("---")
st.markdown("<small>© 2025 AAC</small>", unsafe_allow_html=True)
