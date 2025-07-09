import json
import openai
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from preparar_documentos_streamlit import processar_documentos
import os

# Chave da API (verifica se está definida nos segredos)
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    st.error("🔐 A chave da API da OpenAI não está definida nos segredos. Por favor, adicione OPENAI_API_KEY ao ficheiro secrets.toml.")

# Base de conhecimento manual
def carregar_base_manual():
    try:
        with open("base_conhecimento.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Base de documentos vetorizados
def carregar_base_docs():
    try:
        with open("base_docs_vectorizada.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Base de histórico de perguntas
def guardar_pergunta_no_historico(pergunta):
    historico_path = "historico_perguntas.json"
    try:
        with open(historico_path, "r", encoding="utf-8") as f:
            historico = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        historico = []

    historico.append({"pergunta": pergunta})
    with open(historico_path, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

# Adicionar novas perguntas à base manual
def adicionar_perguntas_base_manual(novas_perguntas):
    base_manual = carregar_base_manual()
    base_manual.extend(novas_perguntas)
    with open("base_conhecimento.json", "w", encoding="utf-8") as f:
        json.dump(base_manual, f, ensure_ascii=False, indent=2)

base_manual = carregar_base_manual()
base_docs = carregar_base_docs()

# Embedding da pergunta
def gerar_embedding(texto):
    resposta = openai.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return resposta.data[0].embedding

# Encontrar blocos mais relevantes por embedding
def procurar_blocos_embedding(embedding_pergunta, top_n=3):
    if not base_docs:
        return []
    docs_embeddings = np.array([bloco["embedding"] for bloco in base_docs])
    pergunta_vector = np.array(embedding_pergunta).reshape(1, -1)
    similaridades = cosine_similarity(pergunta_vector, docs_embeddings)[0]
    indices_top = np.argsort(similaridades)[-top_n:][::-1]
    return [(base_docs[i], similaridades[i]) for i in indices_top]

# Encontrar blocos por palavras-chave
def procurar_blocos_palavras(pergunta, top_n=2):
    palavras = set(pergunta.lower().split())
    blocos_com_score = []
    for bloco in base_docs:
        texto = bloco["texto"].lower()
        score = sum(1 for p in palavras if p in texto)
        if score > 0:
            blocos_com_score.append((score, bloco))
    blocos_ordenados = sorted(blocos_com_score, key=lambda x: x[0], reverse=True)
    return [bloco for _, bloco in blocos_ordenados[:top_n]]

# Função para reformular a pergunta
def reformular_pergunta(pergunta):
    prompt = f"Reformula de forma mais clara e objetiva a seguinte pergunta: {pergunta}"
    resposta = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return resposta.choices[0].message.content

# Função principal de resposta
def gerar_resposta(pergunta):
    pergunta_lower = pergunta.lower()

    if any(x in pergunta_lower for x in [
        "o que podes fazer", "que sabes fazer", "para que serves",
        "lista de coisas", "ajudas com", "que tipo de", "funcionalidades"
    ]):
        guardar_pergunta_no_historico(pergunta)
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

    for entrada in base_manual:
        if entrada["pergunta"].lower() in pergunta_lower:
            guardar_pergunta_no_historico(pergunta)
            resposta = f"""
**❓ Pergunta:** {entrada['pergunta']}

**💬 Resposta:** {entrada['resposta']}"""
            if entrada.get("email"):
                resposta += f"\n**📧 Email de contacto:** [{entrada['email']}](mailto:{entrada['email']})"
            if entrada.get("modelo_email"):
                resposta += f"\n\n**📜 Modelo de email sugerido:**\n```text\n{entrada['modelo_email']}\n```"
            return resposta

    embedding = gerar_embedding(pergunta)
    blocos_embedding = procurar_blocos_embedding(embedding)
    blocos_keywords = procurar_blocos_palavras(pergunta)
    blocos_relevantes = [b for b, _ in blocos_embedding] + [b for b in blocos_keywords if b not in [be for be, _ in blocos_embedding]]

    if not blocos_relevantes:
        guardar_pergunta_no_historico(pergunta)
        st.info("ℹ️ Não encontrei resposta direta. Queres reformular a pergunta ou explorar os documentos?")

        if st.button("🔄 Reformular pergunta"):
            nova_pergunta = reformular_pergunta(pergunta)
            st.text_input("Sugestão de reformulação:", value=nova_pergunta, key="ref")

        if st.button("Mostrar blocos mais próximos"):
            with st.expander("🔍 Blocos semelhantes encontrados", expanded=True):
                blocos_semelhantes = procurar_blocos_embedding(embedding, top_n=5)
                for bloco, score in blocos_semelhantes:
                    origem = bloco.get("origem", "desconhecida")
                    pagina = bloco.get("pagina", "?")
                    st.markdown(f"**Fonte**: {origem}, página {pagina}, Similaridade: {score:.2f}")
                    st.code(bloco['texto'][:500] + ("..." if len(bloco['texto']) > 500 else ""), language="markdown")

        return "❌ Não encontrei informação suficiente para responder a isso."

    contexto = "\n\n".join([b["texto"] for b in blocos_relevantes])

    prompt = f"""
A pergunta é: \"{pergunta}\"
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

    guardar_pergunta_no_historico(pergunta)

    with st.expander("🔍 Blocos usados para gerar a resposta", expanded=False):
        for bloco, score in blocos_embedding:
            origem = bloco.get("origem", "desconhecida")
            pagina = bloco.get("pagina", "?")
            st.markdown(f"**Fonte**: {origem}, página {pagina}, Similaridade: {score:.2f}")
            st.code(bloco['texto'][:500] + ("..." if len(bloco['texto']) > 500 else ""), language="markdown")

    return resposta_final

# ▶️ Interface Streamlit
st.title("💬 Assistente DECivil")

st.markdown("Coloque aqui a sua dúvida ou escolha uma das perguntas frequentes.")

perguntas_frequentes = [entrada["pergunta"] for entrada in base_manual]
pergunta_selecionada = st.selectbox("Perguntas frequentes:", [""] + perguntas_frequentes)
pergunta_digitada = st.text_input("Ou escreva a sua pergunta:")

pergunta_final = pergunta_digitada or pergunta_selecionada

# 📁 Upload de documentos
st.markdown("---")
st.markdown("### 📂 Carregar novos documentos")
arquivos = st.file_uploader("Carregue ficheiros (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"], accept_multiple_files=True)

if arquivos:
    for arquivo in arquivos:
        processar_documentos(arquivo)
    st.success("Documentos processados com sucesso. Por favor, volte a fazer a pergunta.")
    base_docs = carregar_base_docs()

# ⬆️ Upload de ficheiro com perguntas/respostas
st.markdown("---")
st.markdown("### ➕ Importar novas perguntas para a base de conhecimento")
novo_json = st.file_uploader("Carregue ficheiro JSON com novas perguntas:", type="json")

if novo_json:
    try:
        novas_perguntas = json.load(novo_json)
        if isinstance(novas_perguntas, list):
            adicionar_perguntas_base_manual(novas_perguntas)
            st.success("Perguntas adicionadas com sucesso.")
            base_manual = carregar_base_manual()
        else:
            st.error("O ficheiro JSON deve conter uma lista de objetos com perguntas.")
    except Exception as e:
        st.error(f"Erro ao carregar JSON: {e}")

# 💬 Responder à pergunta
if pergunta_final:
    resposta = gerar_resposta(pergunta_final)
    st.markdown("### 🔄 Resposta:")
    st.markdown(resposta)

