# -*- coding: utf-8 -*-
"""
Extrai texto de PDFs/DOCX/TXT/HTML numa pasta e cria um 'base_conhecimento.json' com pares (pergunta,resposta).
Heurística simples: usa o nome do ficheiro (sem extensão) como 'pergunta' e o conteúdo extraído como 'resposta'.

Uso:
    python preparar_documentos_streamlit.py --pasta ./documentos --saida base_conhecimento.json
"""
from __future__ import annotations
import os, json, argparse
from pathlib import Path

def _ler_txt(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def _ler_docx(p: Path) -> str:
    try:
        import docx  # python-docx
    except Exception as e:
        raise SystemExit("Precisa de 'python-docx' para ler DOCX.") from e
    doc = docx.Document(str(p))
    return "\n".join([para.text for para in doc.paragraphs])

def _ler_pdf(p: Path) -> str:
    try:
        import fitz  # pymupdf
    except Exception as e:
        raise SystemExit("Precisa de 'pymupdf' para ler PDF.") from e
    texto = []
    with fitz.open(str(p)) as doc:
        for page in doc:
            texto.append(page.get_text())
    return "\n".join(texto)

def _ler_html(p: Path) -> str:
    try:
        from bs4 import BeautifulSoup
    except Exception as e:
        raise SystemExit("Precisa de 'beautifulsoup4' para ler HTML.") from e
    html = p.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")

def extrair_para_base(pasta: str) -> list:
    base = []
    pasta = Path(pasta)
    for p in pasta.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        try:
            if ext in [".txt", ".md"]:
                conteudo = _ler_txt(p)
            elif ext in [".docx"]:
                conteudo = _ler_docx(p)
            elif ext in [".pdf"]:
                conteudo = _ler_pdf(p)
            elif ext in [".html", ".htm"]:
                conteudo = _ler_html(p)
            else:
                continue
            pergunta = p.stem.replace("_"," ").replace("-"," ").strip().capitalize()
            if not pergunta:
                pergunta = f"Informação do documento {p.name}"
            base.append({
                "pergunta": pergunta,
                "resposta": conteudo.strip(),
                "email": "",
                "modelo_email": ""
            })
        except Exception as e:
            print(f"[ignorado] {p}: {e}")
    return base

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", default="documentos", help="Pasta de entrada com ficheiros")
    ap.add_argument("--saida", default="base_conhecimento.json", help="Ficheiro JSON de saída")
    args = ap.parse_args()

    itens = extrair_para_base(args.pasta)
    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False, indent=2)
    print(f"Gravado {args.saida} com {len(itens)} itens.")

if __name__ == "__main__":
    main()
