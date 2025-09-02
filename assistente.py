import os
import json
import numpy as np
import streamlit as st

# OpenAI nova API (>=1.0.0)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# Caminhos de dados
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_EMBEDDINGS_FAQ = "base_vectorizada.json"          # embeddings das perguntas/respostas (FAQ)
CAMINHO_EMBEDDINGS_DOCS = "base_docs_vectorizada.json"    # embeddings de documentos/URLs (opcional)

# ----- Utilitários de leitura/escrita JSON -----
def _ler_json(caminho, default):
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

# ----- Carregadores -----
def carregar_perguntas_frequentes():
    base = _ler_json(CAMINHO_CONHECIMENTO, [])
    perguntas = [p.get("pergunta", "") for p in base if isinstance(p, dict)]
    # Remover vazios e duplicados, mantendo ordem aproximada
    visto = set()
    limpas = []
    for q in perguntas:
        if q and q not in visto:
            visto.add(q)
            limpas.append(q)
    return limpas

def _carregar_faq_e_embeddings():
    conhecimento = _ler_json(CAMINHO_CONHECIMENTO, [])
    emb_faq = _ler_json(CAMINHO_EMBEDDINGS_FAQ, [])
    return conhecimento, emb_faq

def _carregar_docs_embeddings():
    emb_docs = _ler_json(CAMINHO_EMBEDDINGS_DOCS, [])
    return emb_docs

# ----- Similaridade -----
def _cosine_similarity(v1, v2):
    v1, v2 = np.array(v1), np.array(v2)
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))

def _top_k_similares(embedding_consulta, lista_embeddings, k=3):
    if not lista_embeddings:
        return []
    scores = []
    for idx, item in enumerate(lista_embeddings):
        emb = item.get("embedding")
        if not emb:
            continue
        score = _cosine_similarity(embedding_consulta, emb)
        scores.append((idx, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:k]

# ----- Embeddings OpenAI -----
def _get_openai_client():
    if OpenAI is None:
        return None
    # Lê de st.secrets ou variável de ambiente
    api_key = None
    try:
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def _gerar_embedding(texto):
    """
    Gera embedding via OpenAI. Se não houver chave, devolve None (fallback).
    """
    client = _get_openai_client()
    if not client:
        return None
    try:
        # Modelo recomendado atual
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        return resp.data[0].embedding
    except Exception as e:
        # Em caso de erro de API, retorna None para permitir fallback (exato/TF-IDF)
        return None

# ----- Procura exacta na base manual -----
def _procura_exata(conhecimento, pergunta):
    p_norm = pergunta.strip().lower()
    for entrada in conhecimento:
        if entrada.get("pergunta", "").strip().lower() == p_norm:
            return entrada
    return None

# ----- Geração de Resposta -----
def gerar_resposta(pergunta, usar_embedding=False, top_k_docs=2):
    """
    - Tenta resposta exata pela base.
    - Se não encontrar ou se usar_embedding=True, recorre a embeddings:
        * primeiro compara com embeddings de FAQ (para obter resposta + modelo/email)
        * depois, se necessário, usa embeddings de documentos para evidências
    """
    conhecimento, emb_faq = _carregar_faq_e_embeddings()

    # 1) Se há match exato, responde já (modo rápido)
    match = _procura_exata(conhecimento, pergunta)
    if match and not usar_embedding:
        resposta = match.get("resposta", "").strip()
        email = (match.get("email") or "").strip()
        modelo = (match.get("modelo") or match.get("modelo_email") or "").strip()

        partes = []
        if resposta:
            partes.append(resposta)
        if email:
            partes.append(f"**📧 Contacto:** [{email}](mailto:{email})")
        if modelo:
            partes.append("**📨 Modelo de email sugerido:**\n```\n" + modelo + "\n```")
        return "\n\n".join(partes) if partes else "Não encontrei conteúdo para esta pergunta."

    # 2) Embeddings (se pedido ou se não houve match exato)
    emb_q = _gerar_embedding(pergunta)
    if emb_q is None:
        # Sem chave ou falha -> fallback: tentativa simples de contains na base
        for entrada in conhecimento:
            if entrada.get("pergunta", "").lower() in pergunta.lower():
                resposta = entrada.get("resposta", "").strip()
                email = (entrada.get("email") or "").strip()
                modelo = (entrada.get("modelo") or entrada.get("modelo_email") or "").strip()
                partes = []
                if resposta:
                    partes.append(resposta)
                if email:
                    partes.append(f"**📧 Contacto:** [{email}](mailto:{email})")
                if modelo:
                    partes.append("**📨 Modelo de email sugerido:**\n```\n" + modelo + "\n```")
                return "\n\n".join(partes) if partes else "Não encontrei conteúdo para esta pergunta."
        return "Não encontrei uma resposta adequada (e a API de embeddings não está configurada)."

    # 2a) Procurar nas FAQs por similaridade
    top_faq = _top_k_similares(
        emb_q,
        [e for e in emb_faq if isinstance(e, dict) and "embedding" in e],
        k=1
    )
    resposta_principal = ""
    email_principal = ""
    modelo_principal = ""

    if top_faq:
        idx, score = top_faq[0]
        candidato = emb_faq[idx]
        # Embeddings de FAQ devem guardar "pergunta" (texto) para mapear à base
        per_cand = candidato.get("pergunta", "")
        if per_cand:
            ent = _procura_exata(conhecimento, per_cand)
            if ent:
                resposta_principal = ent.get("resposta", "").strip()
                email_principal = (ent.get("email") or "").strip()
                modelo_principal = (ent.get("modelo") or ent.get("modelo_email") or "").strip()

    # 2b) Procurar nos documentos (se houver base)
    emb_docs = _carregar_docs_embeddings()
    evidencias = []
    if emb_docs:
        top_docs = _top_k_similares(
            emb_q,
            [d for d in emb_docs if isinstance(d, dict) and "embedding" in d],
            k=top_k_docs
        )
        for idx, s in top_docs:
            item = emb_docs[idx]
            trecho = item.get("texto", "")
            origem = item.get("origem") or item.get("fonte") or "documento"
            pagina = item.get("pagina")
            # guarda evidências curtas
            if trecho:
                preview = trecho.strip().replace("\n", " ")
                if len(preview) > 400:
                    preview = preview[:400] + "..."
                etiqueta = f"{origem}" + (f", pág. {pagina}" if pagina else "")
                evidencias.append(f"> _{preview}_  \n— _{etiqueta}_")

    # Montagem final
    partes = []
    if resposta_principal:
        partes.append(resposta_principal)
    if email_principal:
        partes.append(f"**📧 Contacto:** [{email_principal}](mailto:{email_principal})")
    if modelo_principal:
        partes.append("**📨 Modelo de email sugerido:**\n```\n" + modelo_principal + "\n```")

    if not partes and evidencias:
        # Se não há resposta de FAQ, devolve evidências dos docs
        partes.append("**Informação relevante encontrada nos documentos:**\n" + "\n\n".join(evidencias))
    elif evidencias:
        partes.append("\n**Fontes relacionadas (dos documentos):**\n" + "\n\n".join(evidencias))

    if not partes:
        return "Não encontrei uma resposta adequada."

    return "\n\n".join(partes)
