# Desafio MBA Engenharia de Software com IA - Full Cycle

Implementacao do desafio de ingestao e busca semantica com Python, LangChain e PostgreSQL + pgvector.

## Objetivo

O projeto entrega:

1. Ingestao de um PDF para um banco vetorial em PostgreSQL (pgvector).
2. Busca semantica via terminal (CLI), respondendo apenas com base no conteudo do PDF.

Se a resposta nao estiver explicitamente no contexto recuperado, o sistema deve responder:

"Nao tenho informacoes necessarias para responder sua pergunta."

## Estrutura do projeto

```text
.
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py
│   ├── search.py
│   └── chat.py
├── document.pdf
└── README.md
```

## Tecnologias usadas

- Python
- LangChain
- PostgreSQL + pgvector
- Docker e Docker Compose

## Dependencias e correcoes de bibliotecas

O arquivo `requirements.txt` foi simplificado para manter apenas pacotes necessarios e faixas de versao compativeis, reduzindo conflitos comuns de dependencias.

## Configuracao

1. Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Preencha o `.env`.

### Exemplo com OpenAI (recomendado para este desafio)

```env
OPENAI_API_KEY=<SUA_CHAVE>
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-5-nano

EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag
PG_VECTOR_COLLECTION_NAME=pdf_chunks
```

### Exemplo com Gemini

```env
GOOGLE_API_KEY=<SUA_CHAVE>
GOOGLE_EMBEDDING_MODEL=models/embedding-001
GOOGLE_LLM_MODEL=gemini-2.5-flash-lite

EMBEDDING_PROVIDER=gemini
LLM_PROVIDER=gemini

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag
PG_VECTOR_COLLECTION_NAME=pdf_chunks
```

## Subindo o banco (Postgres + pgvector)

```bash
docker compose up -d
```

Isso sobe:

- `postgres` com pgvector
- `bootstrap_vector_ext` para criar a extensao `vector`

## Execucao rapida no Windows (1 comando)

Para evitar digitar todos os comandos manualmente, use o script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

Ou via `.bat`:

```bat
.\scripts\run.bat
```

O script faz automaticamente:

1. valida Docker e tenta abrir o Docker Desktop se necessario;
2. sobe o banco com `docker compose up -d`;
3. instala dependencias Python (a menos que voce pule);
4. executa ingestao (a menos que voce pule);
5. inicia o chat CLI.

Opcoes uteis:

```powershell
# Pula instalacao de dependencias
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -SkipInstall

# Pula ingestao
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -SkipIngest

# Pula ambos (abre so o chat)
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -SkipInstall -SkipIngest
```

## Instalacao de dependencias Python

```bash
pip install -r requirements.txt
```

## Ingestao do PDF

O script faz:

1. Leitura do `document.pdf` (ou `PDF_PATH` do `.env`).
2. Split em chunks de 1000 caracteres com overlap de 150.
3. Geracao de embeddings.
4. Persistencia no PostgreSQL com pgvector.

Execucao:

```bash
python src/ingest.py
```

## Busca e Chat no terminal

Executar:

```bash
python src/chat.py
```

Exemplo:

```text
Chat iniciado. Digite sua pergunta ou 'sair' para encerrar.

PERGUNTA: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: O faturamento foi de 10 milhoes de reais.
```

Para perguntas fora do contexto do PDF, a resposta esperada e:

```text
Nao tenho informacoes necessarias para responder sua pergunta.
```

## Prompt aplicado na busca

O script `src/search.py` usa prompt restritivo para garantir:

- resposta apenas com base no contexto recuperado;
- sem invencoes ou conhecimento externo;
- retorno da frase padrao quando faltar informacao explicita.

## Scripts

- `src/ingest.py`: carrega PDF, quebra em chunks, cria embeddings e salva no pgvector.
- `src/search.py`: busca top 10 resultados com `similarity_search_with_score(query, k=10)` e consulta LLM.
- `src/chat.py`: interface CLI de perguntas e respostas.

## Observacoes

- A ingestao pode duplicar dados se executada varias vezes com a mesma `collection`.
- Para limpar a collection antes da ingestao, use `PRE_DELETE_COLLECTION=true` no `.env`.