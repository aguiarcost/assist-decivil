def gerar_resposta(pergunta):
    pergunta_lower = pergunta.lower()

    # Resposta pré-definida de funcionalidades
    if any(x in pergunta_lower for x in [...]):
        return "..."  # (lista de funcionalidades, como já tens)

    # Tenta encontrar na base manual
    for entrada in base_manual:
        if entrada["pergunta"].lower() in pergunta_lower:
            return f"""..."""  # inclui email e modelo de email

    # Se não encontrar, procura nos documentos (sem email)
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

    return resposta.choices[0].message.content
