import openai
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Carrega base vectorizada
with open("base_vectorizada.json", "r", encoding="utf-8") as f:
    base = json.load(f)

def gerar_resposta(pergunta):
    pergunta_limpa = pergunta.strip().lower()

    if pergunta_limpa in ["", "ajuda", "menu", "o que sabes fazer", "o que sabes fazer?"]:
        return """
🧾 Posso ajudar com os seguintes pedidos administrativos no DECivil:

- 📅 Reservar salas (gop@tecnico.ulisboa.pt)
- 🚗 Pedidos de estacionamento (estacionamento@tecnico.ulisboa.pt)
- 🧑‍💻 Apoio informático (apoiotecnico@civil.tecnico.ulisboa.pt)
- 📧 Aumento de quota de email (dsi@tecnico.ulisboa.pt)
- 🌐 Acesso Wi-Fi para reuniões (dsi@tecnico.ulisboa.pt)
- 👤 Registo de convidados externos (https://si.tecnico.ulisboa.pt/servicos/autenticacao-e-acesso/pessoa-externa-convidado/)
- ☎️ Comunicação de avarias em telefones (nucleo.comunicacoes@tecnico.ulisboa.pt)
- 📄 Pedidos de declarações (nudi.declaracoes@drh.tecnico.ulisboa.pt)
- 🖨️ Fotocópia de exames (na reprografia ou pelo próprio docente)

Podes escrever, por exemplo:  
👉 "Quero reservar uma sala"  
👉 "Preciso de uma declaração"
"""

    # Gerar embedding da pergunta
    resposta_emb = openai.embeddings.create(
        input=pergunta,
        model="text-embedding-3-small"
    ).data[0].embedding

    textos = [item["texto"] for item in base]
    embeddings = [item["embedding"] for item in base]

    sims = cosine_similarity([resposta_emb], embeddings)[0]
    top_idxs = sims.argsort()[-3:][::-1]
    contexto = "\n\n".join([textos[i] for i in top_idxs])

    prompt = f"""
Estás a ajudar docentes e investigadores do DECivil a tratarem de assuntos administrativos,
sem recorrer ao secretariado. Usa apenas o seguinte contexto:

{contexto}

Pergunta: {pergunta}
Responde com:
- uma explicação simples
- o contacto de email, se aplicável
- e um modelo de email sugerido, se fizer sentido.
"""

    resposta = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return resposta.choices[0].message.content
