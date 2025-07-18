from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import os

CAMINHO_CONHECIMENTO = "base_conhecimento.json"

def carregar_base_conhecimento():
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def gerar_resposta(pergunta_usuario):
    base = carregar_base_conhecimento()
    if not base:
        return "⚠️ Base de conhecimento não encontrada ou vazia."

    perguntas = [item["pergunta"] for item in base]
    vectorizer = TfidfVectorizer().fit_transform(perguntas + [pergunta_usuario])
    vetor_pergunta = vectorizer[-1]
    vetores_base = vectorizer[:-1]

    similaridades = cosine_similarity(vetor_pergunta, vetores_base).flatten()
    idx_mais_proximo = similaridades.argmax()

    if similaridades[idx_mais_proximo] < 0.3:
        return "🤷‍♂️ Desculpe, não encontrei uma resposta adequada."

    entrada = base[idx_mais_proximo]
    resposta = entrada.get("resposta", "").strip()
    modelo_email = entrada.get("modelo", "").strip()
    contacto = entrada.get("email", "").strip()

    resposta_final = f"### 🧾 Resposta:\n\n{resposta}"

    if modelo_email:
        resposta_final += f"""\n\n---\n### 📧 Modelo de email sugerido:
```plaintext
{modelo_email}
```"""

    if contacto:
        resposta_final += f"\n\n📮 **Contacto sugerido:** `{contacto}`"

    return resposta_final


