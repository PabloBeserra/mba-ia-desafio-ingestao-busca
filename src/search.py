import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

load_dotenv()

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def _get_env(*names: str, default: str | None = None) -> str | None:
  # Procura a primeira variavel definida entre os nomes informados.
  for name in names:
    value = os.getenv(name)
    if value:
      return value
  return default


def _build_embeddings():
  # Define o mecanismo de embedding usado para vetorizar perguntas e documentos.
  provider = _get_env("EMBEDDING_PROVIDER", default="openai").lower()

  if provider == "gemini":
    api_key = _get_env("GOOGLE_API_KEY")
    if not api_key:
      raise RuntimeError("Defina GOOGLE_API_KEY para usar embeddings do Gemini.")

    model = _get_env("GOOGLE_EMBEDDING_MODEL", default="models/embedding-001")
    return GoogleGenerativeAIEmbeddings(model=model, google_api_key=api_key)

  api_key = _get_env("OPENAI_API_KEY")
  if not api_key:
    raise RuntimeError("Defina OPENAI_API_KEY para usar embeddings da OpenAI.")

  model = _get_env("OPENAI_EMBEDDING_MODEL", "OPENAI_MODEL", default="text-embedding-3-small")
  return OpenAIEmbeddings(model=model, api_key=api_key)


def _build_llm():
  # Define a LLM de resposta conforme provedor configurado no .env.
  provider = _get_env("LLM_PROVIDER", default="openai").lower()

  if provider == "gemini":
    api_key = _get_env("GOOGLE_API_KEY")
    if not api_key:
      raise RuntimeError("Defina GOOGLE_API_KEY para usar LLM do Gemini.")

    model = _get_env("GOOGLE_LLM_MODEL", default="gemini-2.5-flash-lite")
    return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0)

  api_key = _get_env("OPENAI_API_KEY")
  if not api_key:
    raise RuntimeError("Defina OPENAI_API_KEY para usar LLM da OpenAI.")

  model = _get_env("OPENAI_LLM_MODEL", default="gpt-5-nano")
  return ChatOpenAI(model=model, api_key=api_key, temperature=0)


def _get_vector_store(embeddings: OpenAIEmbeddings | GoogleGenerativeAIEmbeddings) -> PGVector:
  # Configura acesso a collection vetorial no Postgres/pgvector.
  database_url = _get_env("DATABASE_URL", "PGVECTOR_URL")
  collection_name = _get_env("PG_VECTOR_COLLECTION_NAME", "PGVECTOR_COLLECTION")

  if not database_url:
    raise RuntimeError("Defina DATABASE_URL (ou PGVECTOR_URL) no arquivo .env.")
  if not collection_name:
    raise RuntimeError("Defina PG_VECTOR_COLLECTION_NAME (ou PGVECTOR_COLLECTION) no arquivo .env.")

  return PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=database_url,
    use_jsonb=True,
  )


def search_prompt(question: str):
  # Valida entrada para evitar chamada de busca com pergunta vazia.
  if not question or not question.strip():
    raise ValueError("Pergunta invalida. Informe um texto nao vazio.")

  # Instancia os componentes de retrieval + geracao de resposta.
  embeddings = _build_embeddings()
  vector_store = _get_vector_store(embeddings)
  llm = _build_llm()

  # Recupera os 10 trechos mais relevantes para a pergunta.
  results = vector_store.similarity_search_with_score(question, k=10)
  contexto = "\n\n".join(doc.page_content.strip() for doc, _ in results if doc.page_content.strip())

  # Sem contexto recuperado, aplica resposta padrao de fora de contexto.
  if not contexto:
    return "Não tenho informações necessárias para responder sua pergunta."

  # Envia prompt restritivo para garantir resposta somente pelo contexto.
  prompt = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=question)
  response = llm.invoke(prompt)

  if isinstance(response.content, str):
    return response.content.strip()

  return str(response.content).strip()