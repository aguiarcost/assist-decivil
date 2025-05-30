import streamlit as st
import openai
import json

# Lê a chave da OpenAI dos segredos (válido na cloud e localmente)
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Carregar a base de conhecimento
with open("base_conhecimento.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

# Função para gerar a resposta usando o novo SDK da OpenAI (>= v1.0)
def gerar_resposta(pergunta):
    prompt = f"""
    Estás a ajudar docentes e investigadores do DECivil a tratarem de assuntos administrativos
    sem recorrer ao secretariado, sempre que possível. Usa apenas esta base de conhecimento:

    {json.dumps(dados, indent=2)}

    Pergunta: {pergunta}
    Responde com:
    - uma explicação simples
    - o contacto de email
    - e um modelo de email sugerido, se aplicável.
    """

    resposta = client.chat.completions.create(
        model="gpt-4",  # ou "gpt-3.5-turbo"
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return resposta.choices[0].message.content

# Interface do utilizador em Streamlit
st.title("💬 Assistente DECivil")
st.write("Coloque aqui a sua dúvida relacionada com pedidos administrativos:")

pergunta = st.text_input("Pergunta:")

if pergunta:
    resposta = gerar_resposta(pergunta)
    st.markdown("### Resposta:")
    st.markdown(resposta)
