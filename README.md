<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Research_Copilot-000000?style=for-the-badge&logoColor=white">
  <img alt="Research Copilot" src="https://img.shields.io/badge/Research_Copilot-ffffff?style=for-the-badge&logoColor=black">
</picture>

**Async AI research reports from your PDFs + live web search**

Queue a query · Agent plans, retrieves, cites · Poll until `completed`

[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-orange?style=flat-square)](https://langchain-ai.github.io/langgraph)
[![Groq](https://img.shields.io/badge/Groq-qwen_27b-F55036?style=flat-square)](src/research_copilot_server/dependencies/model.py)
[![Tavily](https://img.shields.io/badge/Tavily-advanced_search-1a1a2e?style=flat-square)](src/research_copilot_server/services/workflow.py)
[![pgvector](https://img.shields.io/badge/pgvector-VECTOR(384)-336791?style=flat-square&logo=postgresql&logoColor=white)](src/research_copilot_server/models/documents.py)
[![Inngest](https://img.shields.io/badge/Inngest-jobs-5B5BD6?style=flat-square)](src/research_copilot_server/inngest/index.py)
[![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white)](pyproject.toml)

</div>

---

## What it does

Submit a natural-language query with `POST /research/`, upload domain PDFs with `POST /document`, and get back a structured report with `title`, `summary`, `content`, plus persisted `web` + `document` citations. A LangGraph agent (`planner → researcher ⇄ tools → writer`) does the work in the background via Inngest — HTTP returns `201 { status: queued }` in milliseconds, you poll `GET /research/{id}` until `completed` or `failed`.

Or skip the agent entirely: upload PDFs first to build a local pgvector knowledge base, then ask queries that fuse `knowledge_search` (your docs) with `web_search` (Tavily, advanced depth).

---

## Architecture

```mermaid
graph TB
    subgraph Client["Client"]
        UI["Frontend / curl<br/>POST query + PDF<br/>poll GET /research/:id"]
    end

    subgraph API["FastAPI :8000 — src/research_copilot_server/main.py"]
        Routes["API routes<br/>research.py / document.py / health.py"]
        Svc["Services<br/>research.py / document.py<br/>retrieval.py / workflow.py"]
        Repo["Repositories<br/>research.py / document.py"]
    end

    subgraph Jobs["Inngest"]
        Fn["process_research<br/>trigger: research/requested<br/>retries = 2"]
    end

    subgraph Agent["LangGraph Agent — services/workflow.py"]
        Planner["planner<br/>Groq plain prompt"]
        Researcher["researcher + ToolNode<br/>Groq bind_tools"]
        Writer["writer<br/>with_structured_output"]
    end

    subgraph Data["Managed data services"]
        PG[("Postgres 16 + pgvector :5433<br/>research / reports<br/>sources / documents")]
        RD[("Redis :6379<br/>compose only")]
    end

    subgraph ExtAI["External + local AI"]
        Groq["Groq Chat API<br/>qwen/qwen3.8-27b, max 900 tokens"]
        Tavily["Tavily Search API<br/>advanced depth, top-5"]
        Embed["BGE-small-en-v1.5<br/>local, 384-dim"]
    end

    UI -->|POST /research {query}| Routes
    UI -->|POST /document PDF| Routes
    UI -->|GET /research/:id poll| Routes
    Routes --> Svc
    Svc --> Repo
    Repo <--> PG
    Svc -->|INSERT queued + send event| Fn
    Svc -->|encode chunks| Embed
    Fn -->|mark-processing| PG
    Fn -->|ainvoke| Planner
    Planner --> Researcher
    Researcher -->|web_search| Tavily
    Researcher -->|knowledge_search| PG
    PG -.->|top-k chunks| Researcher
    Researcher --> Writer
    Writer --> Groq
    Planner --> Groq
    Fn -->|save report + sources| PG
```

HTTP is thin (validate → CRUD → enqueue). All LLM / search cost lives in Inngest steps so requests never block. Postgres is the single source of truth — jobs, vectors, reports, and citations all live there. Redis ships in `docker-compose.yaml` for future queue/caching; current job transport is Inngest.

---

## Research Status Flow

```mermaid
stateDiagram-v2
    [*] --> queued : POST /research/
    queued --> processing : mark-processing step
    processing --> completed : save-research-report
    processing --> failed : on_failure hook
    completed --> [*]
    failed --> [*]
    created --> processing : legacy initial value
    queued --> failed : research_id missing (non-retriable)
```

`ResearchStatus` (`models/research.py:11`): `queued | created | processing | failed | completed`. Normal path is `queued → processing → completed`. `error_message` is set only on `failed` by `_mark_failed`.

---

## Core Pipeline — Step by Step

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant C as Client
    participant A as FastAPI
    participant DB as Postgres
    participant I as Inngest process_research
    participant G as LangGraph workflow
    participant T as Tavily
    participant L as Groq LLM

    User->>C: Ask "Tradeoffs of pgvector vs dedicated vector DBs?"
    C->>A: POST /research/ {query}
    A->>DB: INSERT research(status=queued)
    A->>I: send research/requested {research_id}
    A-->>C: 201 {id, status: queued}
    Note over I,DB: Steps are independently retryable (retries=2)
    I->>DB: UPDATE status=processing (mark-processing)
    I->>G: workflow.ainvoke({query, messages:[], search_count:0})
    G->>L: planner — "Create a clear plan..."
    G->>L: researcher — tool-bound prompt + plan
    loop Until no tool_calls OR search_count = 3
        G->>T: web_search (advanced, max 5 → top-3 compacted)
        G->>DB: knowledge_search (cosine top-k)
        DB-->>G: chunks {content, metadata, similarity}
        G->>L: researcher reviews evidence, calls tools again or answers
    end
    G->>L: writer — evidence → {title, summary, content}
    G-->>I: {title, summary, content, sources[]}
    I->>DB: INSERT report + sources, status=completed
    C->>A: GET /research/:id (poll)
    A->>DB: SELECT research
    A-->>C: {status: completed}
    alt any step throws
        I->>DB: status=failed + error_message
    end
```

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant C as Client
    participant A as POST /document
    participant P as services/document.py
    participant E as BGE-small-en-v1.5
    participant DB as Postgres

    User->>C: Drop paper.pdf
    C->>A: POST /document (multipart file)
    A->>A: reject if not .pdf (400)
    A->>P: process_pdf_document(filename, bytes)
    P->>P: fitz.open → page.get_text per page
    P->>P: RecursiveCharacterTextSplitter(1000 / 150)
    loop each chunk
        P->>E: encode(chunk) → 384 floats
        P->>DB: bulk INSERT documents{content, metadata, embedding}
    end
    A-->>C: 201 {filename, saved_chunk_count, chunks[]}
    Note over P,DB: Empty PDFs return saved_chunk_count: 0 — no error
```

---

## Project Structure

```
research-copilot-server/
├── src/research_copilot_server/
│   ├── main.py                   # FastAPI(), mount routers, create_all + inngest serve
│   ├── api/routes/
│   │   ├── research.py           # POST / GET / GET :id / PUT :id / DELETE :id
│   │   ├── document.py           # POST /document — PDF-only guard, returns chunks
│   │   └── health.py             # GET / + GET /health
│   ├── config/db.py              # Base, engine, SessionLocal, get_db (DATABASE_URL)
│   ├── models/
│   │   ├── research.py           # Research + ResearchStatus, 1-1 report, 1-N sources
│   │   ├── research_reports.py   # ResearchReport(title, summary, content, research_id)
│   │   ├── research_source.py    # ResearchSource(title, url, web|document, metadata)
│   │   └── documents.py          # Document(content, metadata JSON, VECTOR(384))
│   ├── schema/
│   │   ├── research.py           # user_query_body/response, update_research_body
│   │   └── report.py             # model_output (LLM) + research_report_response (API)
│   ├── repository/               # DB only — no HTTP, no LLM
│   │   ├── research.py           # select / update / delete with SQLAlchemy 2.0
│   │   └── document.py           # bulk insert + cosine_distance vector search
│   ├── services/                 # Business logic + orchestration
│   │   ├── research.py           # create (QUEUED + inngest send), get/update/delete
│   │   ├── document.py           # fitz → split → BGE embed → repository
│   │   ├── retrieval.py          # query embed (normalized) → JSON top-k
│   │   ├── workflow.py           # StateGraph, tools, planner/researcher/writer
│   │   └── llm.py                # legacy simple prompt helper (off hot path)
│   ├── dependencies/
│   │   ├── model.py              # shared ChatGroq(GROQ_MODEL, max_tokens=900)
│   │   └── prompt.py             # user_query_prompt_template
│   └── inngest/index.py          # client + process_research + on_failure handler
├── alembic/versions/             # 8 migrations: pgvector → research → docs → reports → sources
├── docker-compose.yaml           # pgvector/pgvector:pg16 (:5433) + redis:7-alpine (:6379)
├── pyproject.toml                # uv, Python >=3.13
└── tests/                        # empty — see Roadmap
```

Dependency direction: `routes → services → repository → models`. Routes never touch the DB directly; repositories never touch the LLM.

---

## Data Types

The Pydantic schemas are the **API contract**; the SQLAlchemy models are the **persistence contract**; `model_output` is the **LLM contract** that locks `writer` output to a shape the DB can store.

```python
# schema/research.py — HTTP in/out
class user_query_body(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)

class user_query_response(BaseModel):
    id: int
    query: str
    status: ResearchStatus          # queued|created|processing|failed|completed
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class update_research_body(BaseModel):
    status: ResearchStatus
```

```python
# schema/report.py — LLM structured output (writer node)
class model_output(BaseModel):
    content: str = Field(description="Relevant response of the user query")
    title: str
    summary: str
```

```python
# models/research.py + research_source.py + documents.py — DB enums
class ResearchStatus(str, Enum):
    QUEUED = "queued"
    CREATED = "created"
    PROCESSING = "processing"
    FAILED = "failed"
    COMPLETED = "completed"

class SourceType(str, Enum):
    WEB = "web"
    DOCUMENT = "document"

# documents.document_metadata: {"source": filename, "page": N}
# documents.embedding: VECTOR(384) | None  (NULL rows skipped in search)
# research_sources.source_metadata: JSON, default {}
```

```python
# services/workflow.py — agent state (LangGraph)
class ResearchState(TypedDict):
    query: str
    plan: str
    research: str
    messages: Annotated[list, add_messages]
    search_count: int
    title: str
    summary: str
    content: str
    sources: list[dict]  # {title, url|None, source_type, metadata}
```

---

## Environment Variables

Copy to `.env` at repo root (`load_dotenv()` runs in `config/db.py`, `workflow.py`, `dependencies/model.py`).

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg2://postgres:postgres@localhost:5433/research_copilot` |
| `GROQ_API_KEY` | Groq API key (planner / researcher / writer) |
| `TAVILY_API_KEY` | Tavily API key — if absent, `web_search` returns `{"error": ...}` instead of raising |
| `GROQ_MODEL` | Model id, defaults to `qwen/qwen3.8-27b` |
| `REDIS_URL` | `redis://localhost:6379/0` — compose parity, not read by code yet |
| `INNGEST_DEV` | `1` for local Inngest dev server |
| `PYTHONPATH` | `src` so `research_copilot_server.*` resolves |

> Do not commit `.env` — rotate any keys that were ever committed to history.

---

## Local Development

### Prerequisites

- Python 3.13+, `uv`
- Docker (Postgres + Redis)
- Groq + Tavily keys

### Setup

```bash
# Install deps
uv sync

# Start Postgres (:5433) + Redis (:6379)
docker compose up -d

# Migrate (enables pgvector, creates all 4 tables)
uv run alembic upgrade head

# Start API (:8000)
$env:PYTHONPATH="src"; $env:INNGEST_DEV="1"
uv run python -m uvicorn research_copilot_server.main:app --reload --port 8000

# Inngest dev server (second terminal) — bridges jobs to FastAPI
docker run --rm -p 8288:8288 inngest/inngest inngest dev \
  -u http://host.docker.internal:8000/api/inngest --no-discovery
```

Open: API `http://localhost:8000` · docs `http://localhost:8000/docs` · Inngest `http://localhost:8288`.

```bash
# Smoke test
curl http://localhost:8000/health
curl -X POST http://localhost:8000/research/ -H "Content-Type: application/json" -d '{"query":"Impact of pgvector on RAG apps?"}'
curl -X POST http://localhost:8000/document -F "file=@paper.pdf"
curl http://localhost:8000/research/1
```

---

## Production Deployment

No prod guide ships yet — current target is a single VM / container host:

```
1. Provision Postgres 16 + pgvector (or managed PG with vector ext) + Redis.
2. Set DATABASE_URL (psycopg driver), GROQ_API_KEY, TAVILY_API_KEY, GROQ_MODEL.
3. Run `alembic upgrade head` — do NOT rely on Base.metadata.create_all in prod.
4. Run uvicorn with workers: `uvicorn research_copilot_server.main:app --host 0.0.0.0 --port 8000`.
5. Point hosted Inngest at https://<api>/api/inngest (remove INNGEST_DEV).
6. Put a reverse proxy + HTTPS in front; add auth before exposing /research.
```

---

## Key Implementation Notes

<details>
<summary><strong>Why Inngest, not Celery/RQ</strong></summary>

`POST /research/` only inserts a `queued` row and fires `research/requested` (`services/research.py:10`). The durable steps (`mark-processing → run-workflow → save-report`, each with its own `SessionLocal`) live in `inngest/index.py:120` with `retries=2`. No broker code to maintain, each step replays independently, and `on_failure` maps any crash to `failed + error_message` without the client ever hanging.

</details>

<details>
<summary><strong>Tool-loop guard — MAX_SEARCH_COUNT = 3</strong></summary>

`should_continue` (`workflow.py:231`) only routes `researcher → tools` when the last message has `tool_calls` **and** `search_count < 3`. `tools → increment_search_count → researcher` is the only cycle; otherwise `researcher → writer → END`. A runaway LLM cannot loop forever or burn unbounded Tavily/Groq calls.

</details>

<details>
<summary><strong>Context windows are hard-capped at 6000 chars</strong></summary>

`_research_context` keeps the last 6000 chars of `tool + ai` messages for the writer; `_messages_for_model` keeps the human query plus newest evidence ≤ 6000 chars (truncating the oldest overflow). Web hits are pre-sliced (`content[:500]`, top-3), doc hits (`content[:800]`, top-2). This is what keeps `max_tokens=900` outputs grounded instead of truncated mid-JSON.

</details>

<details>
<summary><strong>Sources are extracted, deduped, then persisted</strong></summary>

`researcher` JSON-parses every `tool` message: `{results: [...]}` → `_web_source_from_item` (`title/url/web`), plain lists → `_document_source_from_result` (`title from metadata.source/document`). Dedup key is `(type, url, title, metadata-JSON)`. `_save_report` (`inngest/index.py:73`) appends them as `ResearchSource` rows alongside the `ResearchReport` in one commit.

</details>

<details>
<summary><strong>BGE-small 384-dim — ingest vs query asymmetry is intentional</strong></summary>

Ingest (`document.py:39`) stores raw `model.encode(chunk).tolist()`; query (`retrieval.py:15`) uses `normalize_embeddings=True` so cosine distance is a true angular match. Similarity returned is `round(1 - distance, 4)`. Migration `c5ec45a97157` pins `VECTOR(384)` — switching embedding models requires a migration + re-embed.

</details>

<details>
<summary><strong>Tavily degrades gracefully without a key</strong></summary>

If `TAVILY_API_KEY` is unset, `tavily_client` is `None` and `web_search` returns `{"error": "TAVILY_API_KEY is not configured"}` as tool evidence instead of raising (`workflow.py:41`). The agent still answers from local docs. Check tool evidence for that string before assuming "no web results".

</details>

<details>
<summary><strong>Sync SQLAlchemy inside async routes is the scaling bottleneck</strong></summary>

`config/db.py` uses `psycopg2` + `sessionmaker` (blocking) while routes/services are `async`. Fine for MVP concurrency, but each DB call blocks the event loop. The fix is `asyncpg` + `AsyncSession` + `async get_db` — `asyncpg` is already in `pyproject.toml` as a hint.

</details>

<details>
<summary><strong>create_all + Alembic both exist — pick Alembic in prod</strong></summary>

`main.py:15` runs `Base.metadata.create_all(bind=engine)` on every boot, while `alembic/versions/` holds 8 ordered migrations. Keep `create_all` for throwaway dev only; in any shared env run `alembic upgrade head` and remove the call so schema drift is versioned.

</details>

---

## Tech Stack

| | Technology | Why |
|---|---|---|
| **API** | FastAPI + Uvicorn | Async routes, Pydantic validation, `/docs` for free |
| **ORM** | SQLAlchemy 2.0 (`mapped_column`) | Typed models, `select/update/delete` constructs in repositories |
| **Migrations** | Alembic | Ordered `pgvector → research → documents → reports → sources` history |
| **Vector DB** | Postgres 16 + pgvector `VECTOR(384)` | One DB for jobs + vectors; `cosine_distance` ordered search, no extra service |
| **Embeddings** | `sentence-transformers:BAAI/bge-small-en-v1.5` | Local, fast, 384-dim matches the column; normalized on query |
| **Agent** | LangGraph `StateGraph` | Explicit `planner/researcher/tools/writer` graph with a countable loop |
| **LLM** | LangChain-Groq (`qwen/qwen3.8-27b`) | Cheap structured output (`with_structured_output(model_output)`) with retry |
| **Web search** | Tavily (`advanced` depth) | Answer + snippets with URLs that map 1:1 to `ResearchSource(web)` |
| **PDF** | PyMuPDF (`fitz`) + `RecursiveCharacterTextSplitter(1000/150)` | Per-page text that survives scanned-layout gaps; overlap preserves context |
| **Jobs** | Inngest | Durable steps + retries + failure hook, no broker to run |
| **Infra** | Docker Compose + `uv` | `pgvector/pg16` + `redis:7-alpine` locally; reproducible Python >=3.13 env |

---

## Product Limits

| Constraint | Value |
|---|---|
| Query length | 3–500 chars (`user_query_body`) |
| Document type | PDF only (`400` otherwise) |
| Chunking | 1000 chars / 150 overlap per page |
| Embedding dim | 384 (`VECTOR(384)` — model change = migration) |
| Retrieval | top-5 SQL, top-2 passed to LLM (`content[:800]`) |
| Web search | max 5 hits → top-3 to LLM (`content[:500]`), `include_answer=True` |
| Agent loop | max 3 tool rounds, 6000-char evidence window |
| Writer | `max_tokens=900`, `{title, summary, content}` only |
| Job retries | 2 (Inngest), missing id = non-retriable |
| Report read | DB only — no `GET /report` endpoint yet |

---

## Scripts

```bash
uv sync                                        # install deps
docker compose up -d                           # Postgres + Redis
uv run alembic upgrade head                    # migrate
uv run alembic revision --autogenerate -m "msg" # new migration
$env:PYTHONPATH="src"; uv run python -m uvicorn research_copilot_server.main:app --reload --port 8000
docker run --rm -p 8288:8288 inngest/inngest inngest dev -u http://host.docker.internal:8000/api/inngest --no-discovery
```

---

## Roadmap

**Shipped**
- Async research jobs with status polling + failure messages
- PDF ingest → chunk → embed → pgvector search
- LangGraph planner/researcher/writer with web + doc tools and source dedup
- Persisted reports + per-research citations
- Alembic history (pgvector, 384-dim fix, reports, sources)

**Up next**
- `GET /research/{id}/report` (+ sources) and `report` eager-load on detail GET
- Pagination / filter by `status` on `GET /research/`
- `AsyncSession` + `asyncpg` cutover
- Lazy embedding-model singleton (cold-start + RAM)
- Remove `create_all` from `main.py`, Alembic-only DDL
- pytest: routes, status transitions, loop-cap, retrieval similarity
- Auth, Dockerfile + CI, hosted-Inngest prod guide
