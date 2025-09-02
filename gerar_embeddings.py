"""
Uso:
    python gerar_embeddings.py

- Lê base_conhecimento.json (lista de objetos com 'pergunta', 'resposta', 'email', 'modelo')
- Gera embeddings para cada 'pergunta' e guarda em base_vectorizada.json
"""

import os
import json
import sys
from time import sleep

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

CAMINHO_CONH = "base_conhecimento.json"
CAMINHO_SAIDA = "base_vectorizada.json"

def _ler_json(caminho, default):
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def main():
    if OpenAI is None:
        print("❌ Falha: biblioteca openai>=1.0.0 não instalada.")
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Define OPENAI_API_KEY no ambiente antes de correr este script.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    base = _ler_json(CAMINHO_CONH, [])
    if not base:
        print("⚠️ base_conhecimento.json está vazia ou ausente.")
        sys.exit(0)

    saida = []
    for item in base:
        pergunta = item.get("pergunta", "").strip()
        if not pergunta:
            continue
        try:
            resp = client.embeddings.create(
                model="text-embedding-3-small",
                input=pergunta
            )
            emb = resp.data[0].embedding
            saida.append({"pergunta": pergunta, "embedding": emb})
            print(f"✅ OK: {pergunta}")
            sleep(0.1)
        except Exception as e:
            print(f"❌ Erro a gerar embedding: {pergunta}\n{e}")

    with open(CAMINHO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"🎯 Embeddings guardados em {CAMINHO_SAIDA}")

if __name__ == "__main__":
    main()
