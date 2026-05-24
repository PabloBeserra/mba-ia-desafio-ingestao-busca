import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings

load_dotenv()


def _get_env(*names: str, default: str | None = None) -> str | None:
    # Permite fallback entre nomes de variaveis para manter compatibilidade.
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _build_embeddings():
    # Seleciona provedor de embeddings (OpenAI ou Gemini) via .env.
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


def _resolve_pdf_path() -> str:
    # Usa PDF_PATH quando informado; caso contrario, usa ./document.pdf.
    configured = _get_env("PDF_PATH")
    if configured:
        path = Path(configured).expanduser().resolve()
    else:
        path = (Path(__file__).resolve().parent.parent / "document.pdf").resolve()

    if not path.exists():
        raise FileNotFoundError(f"PDF nao encontrado em: {path}")

    return str(path)


def _build_vector_store(embeddings: OpenAIEmbeddings | GoogleGenerativeAIEmbeddings) -> PGVector:
    # Monta conexao com PGVector e aceita variaveis legadas de configuracao.
    database_url = _get_env("DATABASE_URL", "PGVECTOR_URL")
    collection_name = _get_env("PG_VECTOR_COLLECTION_NAME", "PGVECTOR_COLLECTION")

    if not database_url:
        raise RuntimeError("Defina DATABASE_URL (ou PGVECTOR_URL) no arquivo .env.")
    if not collection_name:
        raise RuntimeError("Defina PG_VECTOR_COLLECTION_NAME (ou PGVECTOR_COLLECTION) no arquivo .env.")

    pre_delete = _get_env("PRE_DELETE_COLLECTION", default="false").lower() == "true"

    return PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=database_url,
        use_jsonb=True,
        pre_delete_collection=pre_delete,
    )

def ingest_pdf():
    # 1) Carrega o documento PDF.
    pdf_path = _resolve_pdf_path()
    docs = PyPDFLoader(pdf_path).load()
    if not docs:
        raise RuntimeError("Nenhum conteudo foi carregado do PDF.")

    # 2) Divide o texto em chunks no padrao exigido pelo desafio.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(docs)
    if not chunks:
        raise RuntimeError("Nao foi possivel gerar chunks do PDF.")

    # 3) Gera embeddings e prepara o vetor store.
    embeddings = _build_embeddings()
    vector_store = _build_vector_store(embeddings)

    # 4) Persiste os chunks com IDs unicos no pgvector.
    ids = [str(uuid.uuid4()) for _ in chunks]
    vector_store.add_documents(documents=chunks, ids=ids)

    print(f"Ingestao concluida com sucesso: {len(chunks)} chunks salvos no pgvector.")


if __name__ == "__main__":
    ingest_pdf()