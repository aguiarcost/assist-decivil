import json
import openai
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from preparar_documentos_streamlit import processar_documentos

# Chave da API
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Base de conhecimento manual
with open("base_conhecimento.json", "r", encoding="utf-8") as f:
    base_manual = json.load(f)

# Base de documentos vetorizados
try:
    with open("base_docs_vectorizada.json", "r", encoding="utf-8") as f:
        base_docs = json.load(f)
except FileNotFoundError:
    base_docs = []

# Embedding da pergunta
def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

# Encontrar blocos mais relevantes
def procurar_blocos_relevantes(embedding_pergunta, top_n=5):
    if not base_docs:
        return []

    docs_embeddings = np.array([bloco["embedding"] for bloco in base_docs])
    pergunta_vector = np.array(embedding_pergunta).reshape(1, -1)
    similaridades = cosine_similarity(pergunta_vector, docs_embeddings)[0]
    indices_top = np.argsort(similaridades)[-top_n:][::-1]
    return [base_docs[i] for i in indices_top]

# Função principal de resposta
def gerar_resposta(pergunta):
    pergunta_lower = pergunta.lower()

    # Lista de funcionalidades
    if any(x in pergunta_lower for x in [
        "o que podes fazer", "que sabes fazer", "para que serves",
        "lista de coisas", "ajudas com", "que tipo de", "funcionalidades"
    ]):
        return """
**📌 Posso ajudar-te com várias tarefas administrativas no DECivil:**

✅ **Informações rápidas**:
- Como reservar salas (GOP)
- Pedidos de estacionamento
- Apoio informático e acesso Wi-Fi
- Registo de convidados no sistema
- Declarações e contactos com a DRH
- Comunicação de avarias

📄 **Consulta de documentos administrativos**, como:
- Regulamentos
- Orientações internas
- Notas informativas

📨 **Sugestões de modelos de email prontos a enviar**

Podes perguntar, por exemplo:
- "Como faço para reservar uma sala?"
- "Quem trata de avarias no telefone?"
- "Dá-me um exemplo de email para pedir estacionamento"
"""

    # Verificar se corresponde a uma pergunta manual
    for entrada in base_manual:
        if entrada["pergunta"].lower() in pergunta_lower:
            return f"""
**❓ Pergunta:** {entrada['pergunta']}

**💬 Resposta:** {entrada['resposta']}

**📧 Email de contacto:** [{entrada['email']}](mailto:{entrada['email']})

**📝 Modelo de email sugerido:**
```text
{entrada['modelo_email']}
```
"""

    # Caso não exista na base manual, procurar nos documentos
    embedding = gerar_embedding(pergunta)
    blocos_relevantes = procurar_blocos_relevantes(embedding)

    if not blocos_relevantes:
        return "❌ Não encontrei informação suficiente para responder a isso."

    contexto = "\n\n".join([b["texto"] for b in blocos_relevantes])

    prompt = f"""
A pergunta é: "{pergunta}"
Com base no seguinte conteúdo, responde de forma direta e clara:

{contexto}

Se não encontrares resposta, diz que não tens informação suficiente.
"""

    resposta = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    resposta_final = resposta.choices[0].message.content

    # DEBUG: Apresentar blocos relevantes se a resposta for vaga
    if "não tenho informação" in resposta_final.lower() or "não encontrei" in resposta_final.lower():
        with st.expander("🔍 Blocos mais relevantes encontrados", expanded=False):
            for bloco in blocos_relevantes:
                st.markdown(f"**Fonte**: {bloco['origem']}, página {bloco['pagina']}")
                st.code(bloco['texto'][:500] + "...", language="markdown")

    return resposta_final
