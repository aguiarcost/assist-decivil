import openai
import os
import json
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity

# Caminhos para os ficheiros
CAMINHO_CONHECIMENTO = "base_conhecimento.json"
CAMINHO_VETORIZADA = "base_vectorizada.json"

# Configurar a chave da API OpenAI se disponível no ambiente
if "OPENAI_API_KEY" in os.environ:
    openai.api_key = os.environ["OPENAI_API_KEY"]

def carregar_dados():
    """Carrega a base de conhecimento e os embeddings de perguntas do ficheiro vetorizado."""
    conhecimento = []
    dados_embed = []
    # Carregar base de conhecimento (perguntas e respostas)
    if os.path.exists(CAMINHO_CONHECIMENTO):
        try:
            with open(CAMINHO_CONHECIMENTO, "r", encoding="utf-8") as f:
                conhecimento = json.load(f)
        except json.JSONDecodeError:
            conhecimento = []
    # Carregar base vetorizada (embeddings)
    if os.path.exists(CAMINHO_VETORIZADA):
        try:
            with open(CAMINHO_VETORIZADA, "r", encoding="utf-8") as f:
                dados_embed = json.load(f)
        except json.JSONDecodeError:
            dados_embed = []
    # Filtrar apenas entradas correspondentes às perguntas da base de conhecimento
    perguntas_embed = [item for item in dados_embed if "pergunta" in item]
    # Construir lista de perguntas e matriz de embeddings
    lista_perguntas = [item["pergunta"] for item in perguntas_embed]
    matriz_embeddings = np.array([item["embedding"] for item in perguntas_embed], dtype=float)
    return conhecimento, lista_perguntas, matriz_embeddings

# Carregar dados iniciais (na importação do módulo)
conhecimento, perguntas_emb, embeddings = carregar_dados()

def gerar_resposta(pergunta_utilizador, base_conhecimento=None, base_vectorizada=None):
    """Gera uma resposta para a pergunta do utilizador, pesquisando na base de conhecimento e nos documentos carregados."""
    global conhecimento, perguntas_emb, embeddings
    # Usar bases fornecidas (se disponíveis) para evitar recarregar ficheiros
    if base_conhecimento is not None and base_vectorizada is not None:
        conhecimento = base_conhecimento
        # Atualizar listas de perguntas e embeddings a partir da base vetorizada fornecida
        perguntas_embed = [item for item in base_vectorizada if "pergunta" in item]
        perguntas_emb = [item["pergunta"] for item in perguntas_embed]
        embeddings = np.array([item["embedding"] for item in perguntas_embed], dtype=float)
    try:
        # Gerar embedding da pergunta do utilizador
        resposta_embed = openai.Embedding.create(input=pergunta_utilizador, model="text-embedding-ada-002")
        embedding_utilizador = np.array(resposta_embed["data"][0]["embedding"], dtype=float).reshape(1, -1)
    except Exception as e:
        return f"❌ Erro ao gerar embedding da pergunta: {e}"
    # Se não há conhecimento ou embeddings carregados, retornar mensagem de erro
    if len(perguntas_emb) == 0 or embeddings.size == 0:
        return "❌ Base de conhecimento vazia ou não carregada."
    # Calcular similaridades com as perguntas conhecidas
    similaridades = cosine_similarity(embedding_utilizador, embeddings)[0]
    indice_max = int(np.argmax(similaridades))
    valor_max = similaridades[indice_max]
    pergunta_proxima = perguntas_emb[indice_max] if perguntas_emb else ""
    resposta_final = None
    # Definir limiares de confiança
    threshold_kb = 0.75
    threshold_doc = 0.7
    if valor_max >= threshold_kb:
        # Encontrar resposta correspondente na base de conhecimento
        for item in conhecimento:
            if item.get("pergunta") == pergunta_proxima:
                resposta_final = item.get("resposta", "")
                modelo_email = item.get("modelo", "")
                if modelo_email:
                    resposta_final += f"\n\n📧 **Modelo de email sugerido:**\n```\n{modelo_email}\n```"
                break
    # Se não encontrou resposta adequada na base de conhecimento, procurar em documentos carregados
    if resposta_final is None or resposta_final.strip() == "":
        # Carregar base vetorizada do ficheiro (caso não tenha sido passada como parâmetro)
        try:
            if base_vectorizada is not None:
                dados_vet = base_vectorizada
            else:
                with open(CAMINHO_VETORIZADA, "r", encoding="utf-8") as f:
                    dados_vet = json.load(f)
        except Exception:
            dados_vet = []
        # Filtrar apenas entradas de documentos (que contêm 'texto')
        docs_vet = [item for item in dados_vet if "texto" in item and "embedding" in item]
        if docs_vet:
            # Calcular similaridade com embeddings dos documentos
            mat_doc_embeddings = np.array([item["embedding"] for item in docs_vet], dtype=float)
            try:
                sim_docs = cosine_similarity(embedding_utilizador, mat_doc_embeddings)[0]
            except Exception:
                sim_docs = []
            if sim_docs.size > 0:
                idx_doc = int(np.argmax(sim_docs))
                max_doc_sim = sim_docs[idx_doc]
                if max_doc_sim >= threshold_doc:
                    doc_encontrado = docs_vet[idx_doc]
                    origem = doc_encontrado.get("origem", "documento")
                    pagina = doc_encontrado.get("pagina", None)
                    texto_trecho = doc_encontrado.get("texto", "")
                    # Opcional: usar modelo de linguagem para gerar resposta a partir do trecho encontrado
                    try:
                        completions = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "Você é um assistente inteligente que responde com base no seguinte contexto."},
                                {"role": "user", "content": f"Contexto do documento ({origem}, página {pagina}): {texto_trecho}\n\nPergunta: {pergunta_utilizador}\nResponda em português de forma clara e concisa."}
                            ],
                            temperature=0
                        )
                        resposta_gerada = completions["choices"][0]["message"]["content"].strip()
                        if resposta_gerada:
                            resposta_final = resposta_gerada
                        else:
                            resposta_final = f"📄 **Informação encontrada em {origem}** (pág. {pagina}):\n{texto_trecho}"
                    except Exception as e:
                        # Em caso de erro na geração da resposta, retornar o trecho diretamente
                        resposta_final = f"📄 **Informação encontrada em {origem}** (pág. {pagina}):\n{texto_trecho}"
    # Se ainda não houver resposta, devolver mensagem padrão e guardar pergunta pendente
    if not resposta_final or resposta_final.strip() == "":
        resposta_final = "❓ Não encontrei informação relevante para responder a essa pergunta."
        # Armazenar pergunta não respondida para aprendizagem futura
        try:
            arquivo_pendentes = "perguntas_pendentes.json"
            pendentes = []
            if os.path.exists(arquivo_pendentes):
                with open(arquivo_pendentes, "r", encoding="utf-8") as f:
                    pendentes = json.load(f)
            pendentes.append({"pergunta": pergunta_utilizador, "timestamp": datetime.now().isoformat()})
            with open(arquivo_pendentes, "w", encoding="utf-8") as f:
                json.dump(pendentes, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return resposta_final
