# -*- coding: utf-8 -*-
"""
Gera embeddings a partir da base de conhecimento e grava num JSON válido.
Uso:
    export OPENAI_API_KEY="..."
    python gerar_embeddings.py --modelo text-embedding-3-small --saida base_knowledge_vector.json
"""
from __future__ import annotations
import os, json, argparse, datetime as dt
from typing import List, Dict, Any

try:
    from openai import OpenAI
except Exception as e:  # pragma: no cover
    raise SystemExit("Precisa de instalar o pacote 'openai>=1.0.0'.") from e

# Reutiliza o backend para ler dados (Supabase ou JSON)
import assistente as backend

def texto_para_embedding(item: Dict[str, Any]) -> str:
    # Texto conciso que combina pergunta, resposta e email (se houver)
    partes = [item.get("pergunta","").strip(), item.get("resposta","").strip()]
    if item.get("email"):
        partes.append(f"Contacto: {item['email']}")
    return "\n\n".join([p for p in partes if p])

def gerar(modelo: str = "text-embedding-3-small") -> Dict[str, Any]:
    dados = backend.ler_base_conhecimento()
    if not dados:
        raise SystemExit("Base de conhecimento vazia. Adicione registos antes de gerar embeddings.")

    client = OpenAI()  # usa OPENAI_API_KEY do ambiente
    textos = [texto_para_embedding(d) for d in dados]

    # A API permite batch de vários inputs num só pedido
    resp = client.embeddings.create(model=modelo, input=textos)
    embeddings = [r.embedding for r in resp.data]

    assert len(embeddings) == len(dados), "Número de embeddings não coincide com itens."

    items = []
    for d, e in zip(dados, embeddings):
        items.append({
            "id": d.get("id"),
            "pergunta": d.get("pergunta"),
            "embedding": e,
        })

    saida = {
        "model": modelo,
        "created": dt.datetime.utcnow().isoformat() + "Z",
        "count": len(items),
        "items": items,
    }
    return saida

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="text-embedding-3-small", help="Modelo de embeddings (p.ex. text-embedding-3-small)")
    ap.add_argument("--saida", default="base_knowledge_vector.json", help="Ficheiro de saída JSON")
    args = ap.parse_args()

    payload = gerar(args.modelo)
    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Gravado: {args.saida} ({len(payload['items'])} itens).")

if __name__ == "__main__":
    main()
