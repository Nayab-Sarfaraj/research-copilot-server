<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Research_Copilot-000000?style=for-the-badge&logoColor=white">
  <img alt="Research Copilot" src="https://img.shields.io/badge/Research_Copilot-ffffff?style=for-the-badge&logoColor=black">
</picture>

**Async AI research reports from your PDFs + live web search**

Queue a query · Agent plans, retrieves, cites · Poll through granular phases until `completed`

[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-orange?style=flat-square)](https://langchain-ai.github.io/langgraph)
[![Groq](https://img.shields.io/badge/Groq-qwen_27b-F55036?style=flat-square)](src/research_copilot_server/dependencies/model.py)
[![Tavily](https://img.shields.io/badge/Tavily-advanced_search-1a1a2e?style=flat-square)](src/research_copilot_server/services/workflow.py)
[![pgvector](https://img.shields.io/badge/pgvector-VECTOR(384)-336791?style=flat-square&logo=postgresql&logoColor=white)](src/research_copilot_server/models/documents.py)
[![Inngest](https://img.shields.io/badge/Inngest-jobs-5B5BD6?style=flat-square)](src/research_copilot_server/inngest/index.py)
[![JWT Auth](https://img.shields.io/badge/Auth-JWT_%2B_bcrypt-blueviolet?style=flat-square)](src/research_copilot_server/services/auth.py)
[![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white)](pyproject.toml)

</div>

---

## What it does

Register and authenticate with `POST /auth/register` (which returns a JWT Bearer token immediately) or `POST /auth/login`, and inspect profile details via `GET /auth/me`. Submit a natural-language query with `POST /research/` (or `POST /research`), upload domain PDFs with `POST /document` (or `POST /documents`), and get back a structured report with `title`, `summary`, `content`, plus persisted `web` and `document` citations. A LangGraph agent (`planner → researcher ⇄ tools → writer`) executes the workflow asynchronously in the background via Inngest:
- HTTP returns `201 { status: queued }` in milliseconds.
- Research progress transitions through granular phase statuses: `queued → planning → researching → writing → completed` (or `failed`).
- Poll `GET /research/{id}` for live status and eager-loaded results, or fetch dedicated report endpoints `GET /research/{id}/report` and `GET /research/{id}/sources`.
- Manage research lifecycles with `PUT /research/{id}` (status update) and `DELETE /research/{id}` (cascading deletion of research, report, and sources).
- View your paginated query history via `GET /research/?page=1&limit=10`.
- Built-in sliding-window rate limiting protects against abuse (5 research queries/minute, 10 PDF uploads/hour).
- Strict per-user data isolation ensures users only access, mutate, or delete their own documents, queries, and reports (`403 Forbidden` on cross-user access).

Or query existing knowledge: upload PDFs first to build a local pgvector knowledge base, then execute queries that fuse `knowledge_search` (your uploaded documents) with `web_search` (Tavily, advanced depth).

---

## Architecture

```mermaid
graph TB
    subgraph Client["Client"]
        UI["Frontend / curl<br/>Auth: JWT Bearer Token<br/>POST query + PDF<br/>poll GET /research/:id"]
    end

    subgraph API["FastAPI :8000 — src/research_copilot_server/main.py"]
        Routes["API routes<br/>auth.py / research.py<br/>document.py / health.py"]
        RateLimit["Rate Limiter<br/>Sliding window: research 5/m, docs 10/h"]
        Svc["Services<br/>auth.py / research.py / document.py<br/>retrieval.py / workflow.py"]
        Repo["Repositories<br/>user.py / research.py / document.py"]
    end

    subgraph Jobs["Inngest"]
        Fn["process_research<br/>trigger: research/requested<br/>retries = 2<br/>steps: get-research → run-workflow → save-report"]
    end

    subgraph Agent["LangGraph Agent — services/workflow.py"]
        Planner["planner<br/>Groq plain prompt<br/>status: planning"]
        Researcher["researcher + ToolNode<br/>Groq bind_tools<br/>status: researching"]
        Writer["writer<br/>with_structured_output<br/>status: writing"]
    end

    subgraph Data["Managed data services"]
        PG[("Postgres 16 + pgvector :5433<br/>users / research / reports<br/>sources / documents")]
        RD[("Redis :6379<br/>compose available")]
    end

    subgraph ExtAI["External + local AI"]
        Groq["Groq Chat API<br/>qwen/qwen3.8-27b, max 900 tokens"]
        Tavily["Tavily Search API<br/>advanced depth, top-5"]
        Embed["BGE-small-en-v1.5<br/>local, 384-dim"]
    end

    UI -->|POST /auth/register or login| Routes
    UI -->|POST research query (Bearer)| Routes
    UI -->|POST document PDF (Bearer)| Routes
    UI -->|poll research by id| Routes
    Routes --> RateLimit
    RateLimit --> Svc
    Svc --> Repo
    Repo <--> PG
    Svc -->|enqueue job| Fn
    Svc -->|encode chunks| Embed
    Fn -->|ainvoke| Planner
    Planner -->|update status| PG
    Planner --> Researcher
    Researcher -->|update status| PG
    Researcher -->|web search| Tavily
    Researcher -->|knowledge search| PG
    PG -.->|top k chunks| Researcher
    Researcher --> Writer
    Writer -->|update status| PG
    Writer --> Groq
    Planner --> Groq
    Fn -->|save report & sources<br/>status: completed| PG
```

HTTP is thin (authenticate → validate → rate limit → CRUD → enqueue). All LLM / search cost lives in Inngest steps so requests never block. Postgres is the single source of truth — users, jobs, vectors, reports, and citations all live there. Per-user data isolation ensures users only see and manage their own documents, research tasks, and reports.

---

## Research Status Flow

```mermaid
stateDiagram-v2
    [*] --> queued : POST /research/
    queued --> planning : LangGraph planner node
    planning --> researching : LangGraph researcher node
    researching --> writing : LangGraph writer node
    writing --> completed : save-research-report step
    queued --> failed : on_failure hook / error
    planning --> failed : on_failure hook / error
    researching --> failed : on_failure hook / error
    writing --> failed : on_failure hook / error
    completed --> [*]
    failed --> [*]
    created --> planning : legacy initial status
    processing --> planning : legacy transition status
```

`ResearchStatus` (`models/research.py:20`): `queued | created | processing | planning | researching | writing | completed | failed`.
- Normal flow: `queued → planning → researching → writing → completed`.
- `error_message` is populated automatically on `failed` by `_mark_failed` in Inngest's `on_failure` handler.

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

    User->>C: Register / Login (POST /auth/login)
    C->>A: POST /auth/login {email, password}
    A-->>C: 200 {access_token, token_type: bearer, user}
    User->>C: Ask "Tradeoffs of pgvector vs dedicated vector DBs?"
    C->>A: POST /research/ (Authorization: Bearer <token>) {query}
    A->>A: Rate limit check (5/min per user)
    A->>DB: INSERT research(status=queued, user_id)
    A->>I: send research/requested {research_id}
    A-->>C: 201 {id, status: queued, user_id, ...}
    Note over I,DB: Durable Inngest steps (retries=2)
    I->>DB: get-research (load query & id)
    I->>G: run-research-workflow: workflow.ainvoke({research_id, query, ...})
    G->>DB: UPDATE status=planning
    G->>L: planner — "Create a clear plan..."
    G->>DB: UPDATE status=researching
    G->>L: researcher — tool-bound prompt + plan
    loop Until no tool_calls OR search_count = 3
        G->>T: web_search (advanced, max 5 → top-3 compacted)
        G->>DB: knowledge_search (cosine top-k)
        DB-->>G: chunks {content, metadata, similarity}
        G->>L: researcher reviews evidence, calls tools again or answers
    end
    G->>DB: UPDATE status=writing
    G->>L: writer — evidence → {title, summary, content}
    G-->>I: {title, summary, content, sources[]}
    I->>DB: save-research-report: INSERT report + sources, status=completed
    C->>A: GET /research/:id (poll)
    A->>DB: SELECT research (with eager-loaded report & sources)
    A-->>C: 200 {status: completed, report: {...}, sources: [...]}
    alt any step throws
        I->>DB: mark-research-failed: status=failed + error_message
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
    C->>A: POST /document (multipart file, Authorization: Bearer <token>)
    A->>A: Rate limit check (10/hour per user)
    A->>A: reject if not .pdf (400)
    A->>P: process_pdf_document(filename, bytes, user_id)
    P->>P: fitz.open → page.get_text per page
    P->>P: RecursiveCharacterTextSplitter(1000 / 150)
    loop each chunk
        P->>E: encode(chunk) → 384 floats
        P->>DB: bulk INSERT documents{content, metadata, embedding, user_id}
    end
    A-->>C: 201 {filename, saved_chunk_count, chunks: [{content, metadata, embedding_length}]}
    Note over P,DB: Empty PDFs return saved_chunk_count: 0 — no error
```

---

## Project Structure

```
research-copilot-server/
├── src/research_copilot_server/
│   ├── main.py                   # FastAPI app, CORS, error handling, router mounts, Inngest serve
│   ├── api/routes/
│   │   ├── auth.py               # POST /auth/register, POST /auth/login, GET /auth/me
│   │   ├── research.py           # POST, GET (paginated), GET :id, GET :id/report, GET :id/sources, PUT :id, DELETE :id
│   │   ├── document.py           # POST /document and /documents — PDF chunking & embeddings
│   │   └── health.py             # GET / and GET /health
│   ├── config/db.py              # Base, engine, SessionLocal, get_db (DATABASE_URL fallback)
│   ├── dependencies/
│   │   ├── auth.py               # JWT HTTPBearer guard (get_current_user)
│   │   ├── model.py              # shared ChatGroq(GROQ_MODEL, max_tokens=900)
│   │   ├── prompt.py             # user_query_prompt_template
│   │   └── rate_limit.py         # sliding-window rate limiter per (resource, user_id)
│   ├── models/
│   │   ├── user.py               # User(id, email, password, name, researches, documents)
│   │   ├── research.py           # Research + ResearchStatus, 1-1 report, 1-N sources, FK to user
│   │   ├── research_reports.py   # ResearchReport(title, summary, content, research_id)
│   │   ├── research_source.py    # ResearchSource(title, url, web|document, metadata)
│   │   └── documents.py          # Document(content, metadata JSON, VECTOR(384), FK to user)
│   ├── schema/
│   │   ├── auth.py               # user_register_body, user_login_body, user_response, token_response, user_register_response
│   │   ├── research.py           # user_query_body, ResearchResponse, ResearchListResponse, update_research_body, ResearchDeleteResponse
│   │   ├── report.py             # model_output (LLM), ResearchReportResponse, SourceResponse
│   │   ├── document.py           # DocumentResponse, DocumentChunkResponse
│   │   └── health.py             # ApiInfoResponse, HealthResponse
│   ├── repository/               # DB layer — no HTTP, no LLM
│   │   ├── user.py               # get_by_id, get_by_email, create_user
│   │   ├── research.py           # paginated select, eager load, update_status, update, delete
│   │   └── document.py           # bulk insert + cosine_distance vector search
│   ├── services/                 # Business logic + orchestration
│   │   ├── auth.py               # bcrypt hash/verify, JWT token issuance & decode, register/login
│   │   ├── research.py           # create (QUEUED + Inngest send), get, update, delete, report fetch (with user auth checks)
│   │   ├── document.py           # fitz → split → BGE embed → repository (with user_id)
│   │   ├── retrieval.py          # query embed (normalized) → JSON top-k
│   │   ├── workflow.py           # StateGraph, tools, planner/researcher/writer with phase updates
│   │   └── llm.py                # legacy prompt helper
│   └── inngest/index.py          # client (with signing key) + process_research + on_failure handler
├── alembic/
│   ├── env.py                    # Alembic env using config.db.DATABASE_URL
│   └── versions/                 # 10 migrations: research → reports → queued → error → pgvector → docs → 384-dim → sources → phases → users
├── docker-compose.yaml           # pgvector/pgvector:pg16 (:5433) + redis:7-alpine (:6379)
├── pyproject.toml                # uv, Python >=3.13, dependencies
├── tests/
│   └── test_rate_limit.py        # unit tests for sliding-window rate limiter
├── .env.example                  # environment template
└── README.md
```

Dependency direction: `routes → dependencies / services → repository → models`. Routes never touch the DB directly; repositories never touch the LLM.

---

## Data Types

The Pydantic schemas define the **API contract**; SQLAlchemy models define the **persistence contract**; `model_output` defines the **LLM contract** that constrains the `writer` node.

```python
# schema/auth.py — Authentication
class user_register_body(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    name: str | None = None

class user_login_body(BaseModel):
    email: EmailStr
    password: str

class user_response(BaseModel):
    id: int
    email: str
    name: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}

class token_response(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: user_response

class user_register_response(user_response):
    access_token: str
    token_type: str = "bearer"

# Aliases: UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse, UserRegisterResponse
```

```python
# schema/research.py & schema/report.py — HTTP Research & Reports
class user_query_body(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)

class update_research_body(BaseModel):
    status: ResearchStatus

class ResearchDeleteResponse(BaseModel):
    message: str

class ResearchResponse(BaseModel):
    id: int
    user_id: int | None = None
    query: str
    status: ResearchStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    report: ResearchReportResponse | None = None
    sources: list[SourceResponse] = Field(default_factory=list)
    model_config = {"from_attributes": True}

class ResearchListResponse(BaseModel):
    items: list[ResearchResponse]
    page: int
    limit: int
    total: int
    model_config = {"from_attributes": True}

class ResearchReportResponse(BaseModel):
    id: int
    research_id: int | None = None
    title: str
    summary: str
    content: str
    created_at: datetime
    sources: list[SourceResponse] | None = None
    model_config = {"from_attributes": True}

# Aliases: user_query_response, create_research_response, paginated_research_response, PaginatedResearchResponse, research_report_response
```

```python
# schema/report.py — LLM structured output (writer node)
class model_output(BaseModel):
    content: str = Field(description="Relevant response of the user query")
    title: str
    summary: str
```

```python
# models/research.py + research_source.py + documents.py — DB enums & definitions
class ResearchStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    PLANNING = "planning"
    RESEARCHING = "researching"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"

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
    research_id: int
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

Copy to `.env` at repo root (`load_dotenv()` runs in `config/db.py`, `workflow.py`, `dependencies/model.py`, and `services/auth.py`).

| Variable              | Default / Example                                                                             | Description                                                                                    |
| --------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `DATABASE_URL`        | `postgresql+psycopg2://postgres:postgres@localhost:5433/research_copilot`                     | SQLAlchemy & Alembic connection URL (default in `config/db.py`)                                |
| `GROQ_API_KEY`        | *(required for LLM)*                                                                          | Groq API key for planner, researcher, and writer nodes                                         |
| `TAVILY_API_KEY`      | *(optional)*                                                                                  | Tavily search key — if absent, `web_search` returns `{"error": ...}` gracefully                |
| `GROQ_MODEL`          | `qwen/qwen3.8-27b`                                                                            | Groq chat model identifier                                                                     |
| `JWT_SECRET`          | `research-copilot-secret-jwt-key-2026-very-secure`                                            | Secret key used to sign and verify JWT authentication tokens (override in production)          |
| `INNGEST_APP_ID`      | `research-copilot`                                                                            | Application ID configured on the Inngest client                                                |
| `INNGEST_SIGNING_KEY` | `0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef`                          | 64-hex signing key for Inngest SDK webhook verification (required in production)               |
| `REDIS_URL`           | `redis://localhost:6379/0`                                                                    | Redis instance in compose for future distributed caching/locks                                 |
| `INNGEST_DEV`         | `1`                                                                                           | Enables local Inngest development mode                                                         |
| `PYTHONPATH`          | `src`                                                                                         | Allows module resolution for `research_copilot_server.*`                                       |

> [!WARNING]
> Do not commit `.env` to version control. Always provide a high-entropy secret for `JWT_SECRET` in staging and production environments.

---

## Local Development

### Prerequisites

- Python 3.13+, `uv`
- Docker (Postgres with pgvector + Redis)
- Groq API key (and optionally Tavily API key)

### Setup

```bash
# 1. Install dependencies
uv sync

# 2. Start Postgres (:5433) + Redis (:6379)
docker compose up -d

# 3. Run database migrations (10 migrations)
uv run alembic upgrade head

# 4. Start API (:8000)
$env:PYTHONPATH="src"; $env:INNGEST_DEV="1"; uv run python -m uvicorn research_copilot_server.main:app --reload --port 8000

# 5. Start Inngest dev server (in a separate terminal)
docker run --rm -p 8288:8288 inngest/inngest inngest dev \
  -u http://host.docker.internal:8000/api/inngest --no-discovery
```

Access endpoints:
- API: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Inngest Dashboard: `http://localhost:8288`

### Running Tests

```bash
# Run unit tests (includes rate limiting verification)
uv run python -m unittest discover tests
```

### Smoke Test Flow

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Register a new user (returns user info + access_token directly)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"researcher@example.com","password":"securepassword123","name":"Dr. Alice"}'

# 3. Or log in to acquire / refresh a JWT access token
# (Save the access_token from the JSON response as $TOKEN)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"researcher@example.com","password":"securepassword123"}'

# 4. Verify authenticated user identity
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/auth/me

# 5. Upload domain PDF document (rate limit: 10/hour; accepts /document or /documents)
curl -X POST http://localhost:8000/document \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@paper.pdf"

# 6. Queue a research query (rate limit: 5/minute; accepts /research or /research/)
curl -X POST http://localhost:8000/research/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"Impact of pgvector on modern RAG applications?"}'

# 7. Poll research status and eager-loaded report
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/research/1

# 8. Fetch dedicated report and sources once status is completed
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/research/1/report
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/research/1/sources

# 9. List paginated research queries
curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/research/?page=1&limit=10"

# 10. Optional: Update research status manually
curl -X PUT http://localhost:8000/research/1 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status":"planning"}'

# 11. Optional: Delete research query (cascades to report & sources)
curl -X DELETE http://localhost:8000/research/1 \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Production Deployment

Recommended baseline for a VM / containerized environment:

```
1. Provision Postgres 16 with pgvector extension enabled + Redis.
2. Configure environment: DATABASE_URL, GROQ_API_KEY, TAVILY_API_KEY, GROQ_MODEL, JWT_SECRET.
3. Run migrations: `uv run alembic upgrade head` (do NOT rely on Base.metadata.create_all).
4. Run Uvicorn: `uvicorn research_copilot_server.main:app --host 0.0.0.0 --port 8000`.
   Note: The in-memory sliding-window rate limiter is per-process. When running multiple workers
   or instances, use sticky sessions or back the window tracking with Redis.
5. Direct hosted Inngest to https://<your-domain>/api/inngest (remove INNGEST_DEV=1).
6. Configure HTTPS reverse proxy (Nginx, Caddy, or Cloudflare) with security headers.
```

---

## Key Implementation Notes

<details>
<summary><strong>Granular research phase status tracking</strong></summary>

Rather than jumping directly from `processing` to `completed`, the workflow tracks actual progress in real time (`models/research.py:20`):
- `planner` node sets status to `planning`
- `researcher` node sets status to `researching`
- `writer` node sets status to `writing`
- Inngest's `save-research-report` step writes the report, persists sources, and sets status to `completed`
- Inngest's `on_failure` hook captures any error across steps and marks status as `failed` with `error_message`

This gives clients fine-grained visibility when polling `GET /research/{id}`.

</details>

<details>
<summary><strong>JWT authentication and per-user data isolation</strong></summary>

All document uploads and research operations are gated by `get_current_user` (`dependencies/auth.py`). Both `Document` and `Research` tables enforce a foreign key relationship to `users.id` with cascade deletion. All individual research endpoints (`GET /{id}`, `GET /{id}/report`, `GET /{id}/sources`, `PUT /{id}`, and `DELETE /{id}`) in `services/research.py` enforce ownership and return `403 Forbidden` if a user attempts to access, edit, or delete another user's research resource.

</details>

<details>
<summary><strong>Sliding-window rate limiting</strong></summary>

Implemented in `dependencies/rate_limit.py` using thread-safe sliding windows per `(resource, user_id)`.
- `POST /research/`: 5 queries per 60 seconds
- `POST /document`: 10 uploads per 3600 seconds (1 hour)
- Exceeding the threshold returns `429 Too Many Requests` with a calculated `Retry-After` header. Automatic cleanup evicts stale window keys every 256 requests.

</details>

<details>
<summary><strong>Why Inngest, not Celery/RQ</strong></summary>

`POST /research/` only inserts a `queued` row and fires `research/requested` (`services/research.py:18`). The durable steps (`get-research → run-research-workflow → save-research-report`, each with its own `SessionLocal`) live in `inngest/index.py:129` with `retries=2`. The Inngest client supports configurable `INNGEST_APP_ID` and `INNGEST_SIGNING_KEY` (with a 64-char hex key fallback for dev signature verification) served at `/api/inngest`. No broker code to maintain, each step replays independently, and `on_failure` maps any crash to `failed + error_message` without the client ever hanging.

</details>

<details>
<summary><strong>Tool-loop guard — MAX_SEARCH_COUNT = 3</strong></summary>

`should_continue` (`workflow.py:247`) only routes `researcher → tools` when the last message has `tool_calls` **and** `search_count < 3`. `tools → increment_search_count → researcher` is the only cycle; otherwise `researcher → writer → END`. A runaway LLM cannot loop forever or burn unbounded Tavily/Groq calls.

</details>

<details>
<summary><strong>Context windows are hard-capped at 6000 chars</strong></summary>

`_research_context` keeps the last 6000 chars of `tool + ai` messages for the writer; `_messages_for_model` keeps the human query plus newest evidence ≤ 6000 chars (truncating the oldest overflow). Web hits are pre-sliced (`content[:500]`, top-3), doc hits (`content[:800]`, top-2). This is what keeps `max_tokens=900` outputs grounded instead of truncated mid-JSON.

</details>

<details>
<summary><strong>Sources are extracted, deduped, then persisted</strong></summary>

`researcher` JSON-parses every `tool` message: `{results: [...]}` → `_web_source_from_item` (`title/url/web`), plain lists → `_document_source_from_result` (`title from metadata.source/document`). Dedup key is `(type, url, title, metadata-JSON)`. `_save_report` (`inngest/index.py:76`) appends them as `ResearchSource` rows alongside the `ResearchReport` in one commit.

</details>

<details>
<summary><strong>BGE-small 384-dim — ingest vs query asymmetry is intentional</strong></summary>

Ingest (`document.py:39`) stores raw `model.encode(chunk).tolist()`; query (`retrieval.py:15`) uses `normalize_embeddings=True` so cosine distance is a true angular match. Similarity returned is `round(1 - distance, 4)`. Migration `c5ec45a97157` pins `VECTOR(384)` — switching embedding models requires a migration + re-embed.

</details>

<details>
<summary><strong>Tavily degrades gracefully without a key</strong></summary>

If `TAVILY_API_KEY` is unset, `tavily_client` is `None` and `web_search` returns `{"error": "TAVILY_API_KEY is not configured"}` as tool evidence instead of raising (`workflow.py:54`). The agent still answers from local docs.

</details>

<details>
<summary><strong>Sync SQLAlchemy inside async routes is the scaling bottleneck</strong></summary>

`config/db.py` uses `psycopg2` + `sessionmaker` (blocking) while routes/services are `async`. Fine for MVP concurrency, but each DB call blocks the event loop. The fix is `asyncpg` + `AsyncSession` + `async get_db` — `asyncpg` is already included in `pyproject.toml`.

</details>

<details>
<summary><strong>Strict Alembic-driven migrations (create_all removed)</strong></summary>

`Base.metadata.create_all(bind=engine)` was completely removed from `main.py` in favor of strict, version-controlled Alembic migrations. All schema initialization and table updates must be performed using `uv run alembic upgrade head` across all environments. `alembic/env.py` directly references `DATABASE_URL` from `config/db.py` and configures `include_object` to safely ignore transition columns like `embedding_1536`.

</details>

---

## Tech Stack

| Component      | Technology                                                    | Why                                                                           |
| -------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **API**        | FastAPI + Uvicorn                                             | Async routes, Pydantic validation, `/docs` interactive OpenAPI                |
| **Auth**       | PyJWT + bcrypt + HTTPBearer                                   | Secure password hashing, stateless 24-hour JWT Bearer tokens, user scoping    |
| **Rate Limit** | In-memory sliding window                                      | Granular per-user limits on costly endpoints with `Retry-After` headers       |
| **ORM**        | SQLAlchemy 2.0 (`mapped_column`)                              | Strongly typed models, `select/update/delete` with eager loading              |
| **Migrations** | Alembic (10 ordered revisions)                                | `research → reports → queued → error → pgvector → docs → 384-dim → sources → phases → users` |
| **Vector DB**  | Postgres 16 + pgvector `VECTOR(384)`                          | Unified DB for auth, jobs, vectors, reports; `cosine_distance` ordered search |
| **Embeddings** | `sentence-transformers:BAAI/bge-small-en-v1.5`                | Local, fast, 384-dim matches vector column; normalized on query               |
| **Agent**      | LangGraph `StateGraph`                                        | Explicit `planner/researcher/tools/writer` graph with loop guards and status  |
| **LLM**        | LangChain-Groq (`qwen/qwen3.8-27b`)                           | Fast, cheap structured output (`with_structured_output(model_output)`)        |
| **Web search** | Tavily (`advanced` depth)                                     | Snippets with URLs that map 1:1 to `ResearchSource(web)`                      |
| **PDF**        | PyMuPDF (`fitz`) + `RecursiveCharacterTextSplitter(1000/150)` | Fast page text extraction preserving layout; chunk overlap preserves context  |
| **Jobs**       | Inngest                                                       | Durable steps + retries + failure hook, served at `/api/inngest`              |
| **Infra**      | Docker Compose + `uv`                                         | `pgvector/pg16` + `redis:7-alpine` locally; reproducible Python 3.13+ env     |

---

## Product Limits & Rate Limits

| Constraint          | Value                                                              | Details                                                     |
| ------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------- |
| Query length        | 3–500 chars                                                        | Validated via `user_query_body`                             |
| Document type       | PDF only                                                           | `400 Bad Request` if file extension or stream is not PDF   |
| Chunking            | 1000 chars / 150 overlap per page                                  | `RecursiveCharacterTextSplitter`                            |
| Embedding dimension | 384 (`VECTOR(384)`)                                                | BAAI/bge-small-en-v1.5                                      |
| Document search     | top-5 SQL match, top-2 passed to LLM                               | `content[:800]`                                             |
| Web search          | max 5 hits, top-3 passed to LLM                                    | `content[:500]`, `include_answer=True`                      |
| Agent loop          | max 3 tool rounds                                                  | Controlled by `MAX_SEARCH_COUNT = 3`                        |
| Context window      | 6000-char evidence window                                          | Keeps Groq token limit safe                                 |
| Writer output       | `max_tokens=900`                                                   | Structured output: `{title, summary, content}`              |
| Research rate limit | 5 requests / 60 seconds per user                                   | `429 Too Many Requests` with `Retry-After` header           |
| Document rate limit | 10 uploads / 3600 seconds per user                                 | `429 Too Many Requests` with `Retry-After` header           |
| Job retries         | 2 retries (Inngest)                                                | Missing research ID is marked non-retriable                 |
| Pagination          | Default `page=1, limit=10`, max `limit=100`                        | Supported on `GET /research/`                               |
| Report read         | Eager-loaded in `GET /research/{id}` + dedicated `/report` endpoint | `GET /research/{id}/report` and `GET /research/{id}/sources`|
| Research update     | `PUT /research/{id}`                                               | Updates research status (`update_research_body`)             |
| Research deletion   | `DELETE /research/{id}`                                            | Cascades deletion of research, report, and sources          |
| Document routes     | `POST /document` & `POST /documents`                               | Dual endpoint mounting with trailing slash support          |
| Authorization       | User-scoped ownership                                              | Cross-user access or mutations return `403 Forbidden`       |

---

## Scripts

```bash
uv sync                                          # install dependencies
docker compose up -d                             # start Postgres + Redis containers
uv run alembic upgrade head                      # run database migrations
uv run python -m unittest discover tests         # run test suite
$env:PYTHONPATH="src"; uv run python -m uvicorn research_copilot_server.main:app --reload --port 8000  # start API
docker run --rm -p 8288:8288 inngest/inngest inngest dev -u http://host.docker.internal:8000/api/inngest --no-discovery  # Inngest dev server
```

---

## Roadmap

**Shipped**

- [x] User authentication (JWT Bearer tokens, bcrypt hashing, `/auth/register`, `/auth/login`, `/auth/me`)
- [x] Per-user data ownership and isolation for documents, research queries, and reports (`403 Forbidden` protection)
- [x] Granular research phase statuses (`planning`, `researching`, `writing`) with live DB updates
- [x] Async research pipeline with Inngest durable steps (`get-research → run-research-workflow → save-research-report`)
- [x] Strict Alembic-only DDL: removed `Base.metadata.create_all` from `main.py` in favor of versioned migrations
- [x] Full research lifecycle mutations: status updates (`PUT /research/{id}`) and cascading deletion (`DELETE /research/{id}`)
- [x] Dual route mounts (`/document` and `/documents`, `/research` and `/research/`) with slash tolerance
- [x] Per-user sliding-window rate limiting on research queries and PDF uploads
- [x] PDF ingestion → RecursiveCharacter text chunking → BGE-small embeddings → pgvector cosine search
- [x] LangGraph planner/researcher/writer workflow with web (Tavily) + knowledge tools and source deduplication
- [x] Persisted reports + per-research citations with dedicated `GET /research/{id}/report` and `GET /research/{id}/sources`
- [x] Paginated query history (`GET /research/?page=1&limit=10`)
- [x] Standardized health check models and global unhandled exception handler
- [x] 10 Alembic migrations tracking schema evolution
- [x] Initial automated test suite (`tests/test_rate_limit.py`)

**Up next**

- [ ] `AsyncSession` + `asyncpg` cutover to eliminate synchronous DB blocking on the event loop
- [ ] Redis-backed rate limiting for multi-worker / multi-instance deployment
- [ ] Lazy embedding-model singleton to optimize server cold-start and memory usage
- [ ] Expand test suite: route integration tests, workflow graph tests, retrieval similarity validation
- [ ] Dockerfile + CI pipeline (GitHub Actions) and hosted Inngest production configuration guide
