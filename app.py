import streamlit as st
import json
import os
import openai
from assistente import gerar_resposta
from preparar_documentos_streamlit import processar_documento
from datetime import datetime

# ... (manter o resto igual, adicionar abaixo do input de pergunta)

use_documents = st.checkbox("Buscar também em documentos adicionados (RAG)", value=True)

# Gerar resposta
resposta = ""
if pergunta_final:
    resposta = gerar_resposta(pergunta_final, use_documents=use_documents)
    guardar_pergunta_no_historico(pergunta_final)

# Mostrar resposta (igual)

# Novo: Display de histórico
with st.expander("📜 Histórico de perguntas"):
    if os.path.exists(CAMINHO_HISTORICO):
        with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as f:
            historico = json.load(f)
            for item in reversed(historico[-10:]):  # Últimas 10
                st.write(f"{item['timestamp']}: {item['pergunta']}")

# ... (resto igual)
