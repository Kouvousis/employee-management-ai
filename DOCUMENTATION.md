# NovaTech Solutions — Project Documentation

**An Employee Management System with a RAG-powered AI Assistant**

---

## Table of contents

1. [Application overview](#1-application-overview)
2. [System architecture](#2-system-architecture)
3. [Data model](#3-data-model)
4. [GenAI techniques: RAG and Agents](#4-genai-techniques-rag-and-agents)
5. [Execution instructions](#5-execution-instructions)
6. [Usage examples](#6-usage-examples)
7. [Security considerations](#7-security-considerations)

---

## 1. Application overview

NovaTech Solutions is a full-stack employee management platform built around an embedded
**AI assistant ("Nova")**. It lets HR and admin users manage the company's employees, projects,
and tasks through a web dashboard, while a conversational AI assistant answers questions about
company policy and live HR data — and can perform write actions such as adding an employee or
assigning a task.

The defining feature of the system is its **Retrieval-Augmented Generation (RAG)** layer combined
with a **tool-using LangChain agent**. Instead of relying on the language model's parametric
memory (which would hallucinate company-specific facts), every answer about company data is
grounded either in retrieved documents (vector search) or in exact, live database queries.

### What the system does

- **Employee / Project / Task management** — full CRUD through a Material dashboard with paginated
  tables, create/edit dialogs, soft-delete (deactivation), and admin-only hard delete.
- **Conversational AI assistant** — answers policy questions, answers live HR-data questions, and
  executes write actions, all through natural language. Responses stream token-by-token and the
  assistant retains per-conversation memory.
- **Role-based access** — three roles (`admin`, `human_resources`, `employee`) enforced by the
  backend; the assistant scopes data access to the calling user's role.
- **Self-consistent AI knowledge** — any write to an employee or task (via the UI *or* the agent)
  automatically re-syncs the vector index, so the assistant never returns stale data.

> **Note on scope:** The frontend currently implements the **HR/admin view**. The backend enforces
> all three roles.

### Technology stack

| Layer | Technology |
|-------|------------|
| Frontend | Angular 22 (standalone, zoneless, signals), Angular Material, Tailwind CSS v4, Signal Forms, RxJS |
| Backend | FastAPI, SQLModel, Pydantic, Uvicorn (Python ≥ 3.14) |
| Database | PostgreSQL 18 + pgvector extension |
| AI / RAG | LangChain + LangGraph agent, langchain-postgres (PGVector), OpenAI (`gpt-4o-mini` + `text-embedding-3-small`), Anthropic (`claude-haiku` fallback) |
| Auth | JWT (`python-jose`), bcrypt password hashing |
| Tooling | `uv` (Python), `pnpm` (Node), Docker Compose |

---

## 2. System architecture

The application follows a classic three-tier architecture (presentation → API → data), with a
dedicated AI layer living inside the backend.

```
┌───────────────┐     HTTP/JWT      ┌────────────────┐    SQL / vector    ┌──────────────────────┐
│  Angular SPA  │ ───────────────▶  │    FastAPI     │ ─────────────────▶ │  PostgreSQL 18       │
│ (nginx :4200) │ ◀─────────────── │   backend      │ ◀───────────────── │  + pgvector          │
└───────────────┘   JSON / SSE      │   (:8000)      │                    └──────────────────────┘
                                    │                │
                                    │  ┌──────────┐  │
                                    │  │ LangChain│  │      tools
                                    │  │  agent   │──┼──▶ • vector search (RAG)
                                    │  │  (Nova)  │  │    • structured SQL queries
                                    │  └──────────┘  │    • write actions (+ vector sync)
                                    └────────────────┘
```

### 2.1 Frontend — Angular 22 (`client/`)

A single-page application built with modern Angular 22 conventions:

- **Standalone components only** (no NgModules) and **zoneless change detection** — state is
  signal-driven (`signal()`, `computed()`), with no `zone.js`.
- **Angular Material** for UI components (tables, paginator, dialogs, datepicker, snackbar) and
  **Tailwind CSS v4** for layout and spacing.
- **Signal Forms** (`@angular/forms/signals`) for reactive, signal-based form state and validation.
- **JWT authentication** handled by a functional HTTP interceptor that attaches the bearer token to
  every request and signs the user out on a `401` response. Route guards (`authGuard`,
  `hrOrAdminGuard`) protect authenticated and role-restricted routes.
- **Lazy-loaded routes** via `loadComponent`.

Key areas:

- `core/` — typed API models, the `AuthService` + JWT interceptor + route guards, and the HTTP
  services (`Employee` / `Project` / `Task` / `Chat`).
- `pages/` — route components: `auth/login`, `employees`, `projects`, `tasks`, `chat`, and
  `side-menu` (the authenticated app shell with toolbar and sidenav).
- `shared/` — reusable components such as the confirmation dialog.

### 2.2 Backend — FastAPI (`server/`)

- **`main.py`** — the FastAPI application and its startup lifespan (see §2.4).
- **`models/`** — SQLModel table classes (`Employee`, `Project`, `Task`, `User`). SQLModel unifies
  the SQLAlchemy table definition and Pydantic validation in a single class.
- **`schemas/`** — plain Pydantic models used *only* as HTTP request/response contracts, kept
  separate from the table classes to control exactly which fields are exposed.
- **`routers/`** — the API endpoints: `auth`, `employees`, `projects`, `tasks`, `chat`.
- **`rag/`** — the AI layer (detailed in §4).
- **`company_docs/`** — `.txt` files forming the company knowledge base, ingested into the vector
  store.

### 2.3 Database — PostgreSQL + pgvector

A single PostgreSQL 18 database serves **both** the relational data and the vector embeddings. The
`pgvector` extension stores embeddings in the `langchain_pg_collection` and
`langchain_pg_embedding` tables (managed by `langchain-postgres`). There is **no separate vector
database** — this keeps the deployment simple and transactionally consistent.

### 2.4 Startup sequence (`main.py` lifespan)

On every startup the backend runs an idempotent bootstrap:

1. Creates the `vector` extension and all SQLModel tables.
2. Seeds reference employees, projects, and tasks if the database is empty.
3. Calls `get_company_store()` and `get_employee_store()`. Each first checks whether its vector
   collection already contains embeddings, so the (expensive) embedding step only runs on a true
   cold start — subsequent restarts are fast.

### 2.5 Containerization

The whole stack runs with a single `docker compose up`. Three services are defined:

- **`db`** — the `pgvector/pgvector:pg18` image, initialized from the credentials in `server/.env`.
- **`backend`** — built from `server/Dockerfile` (Python 3.14 + `uv`), waits for the database to be
  healthy.
- **`frontend`** — built from `client/Dockerfile` (multi-stage: `pnpm build` → nginx serving the
  static bundle with SPA fallback).

All configuration, including database credentials and API keys, is supplied through `server/.env`.
No secrets are committed to the repository.

---

## 3. Data model

```
User (auth)  ──1:0..1──  Employee (HR identity)
                              │ 1:N
                              ▼
                            Task  ──N:1──  Project
```

- **`Employee`** — HR identity: first/last name, role, department, email, hire date, `is_active`.
- **`User`** — authentication: hashed password, an `AccessRights` enum (`admin` /
  `human_resources` / `employee`), and a nullable `employee_id` (allowing standalone admin accounts
  with no Employee row).
- **`Task`** — links an Employee to a Project; both foreign keys are nullable, so unassigned tasks
  are allowed. Carries a title and a `TaskStatus`.
- **`Project`** — a company initiative that groups tasks; has `is_active` for soft-delete.

`Employee` and `Project` use an `is_active` boolean for **soft-delete** — there is no hard-delete
path for them in the agent tools. Tasks, by contrast, support permanent deletion.

---

## 4. GenAI techniques: RAG and Agents

This is the core of the project. The AI layer (`server/rag/`) combines **Retrieval-Augmented
Generation** with a **tool-using agent** so the assistant answers from grounded, company-specific
data rather than the model's memory.

### 4.1 The language model and embeddings (`rag/config.py`)

- **LLM** — `gpt-4o-mini` (OpenAI) is the primary model, with `claude-haiku-4-5` (Anthropic) as a
  fallback when no OpenAI key is present. `temperature=0` is used for deterministic, factual
  answers, with retries and a request timeout for robustness.
- **Embeddings** — `text-embedding-3-small` (OpenAI) is used for *all* embeddings, regardless of
  which LLM is active. This is why `OPENAI_API_KEY` is always required.

### 4.2 Retrieval-Augmented Generation (RAG)

RAG grounds the model's answers in retrieved context. The system maintains **two distinct vector
collections**, both stored in PostgreSQL via `pgvector`:

| Collection | Source | Purpose |
|------------|--------|---------|
| `company_knowledge` | `company_docs/*.txt` | Unstructured policy/benefit/onboarding documents |
| `employee_data` | PostgreSQL Employee rows + their tasks | Per-employee profile documents for fuzzy lookups |

**Company knowledge ingestion** (`rag/vectorstores/company_store.py`):

1. `.txt` documents are loaded from `company_docs/` with a `DirectoryLoader`.
2. Each document is tagged with a `topic` derived from its filename.
3. The text is split with a `RecursiveCharacterTextSplitter` using a **chunk size of 800
   characters and a 100-character overlap** — small enough for precise retrieval, with overlap so
   facts spanning a boundary are not lost.
4. The chunks are embedded and written to the `company_knowledge` collection.

**Employee data ingestion** (`rag/vectorstores/employee_store.py`):

Each employee is serialized into a single natural-language `Document` containing their name, role,
department, email, hire date, and a bulleted list of their tasks (title + status). The
`employee_id` is stored in the document metadata so individual records can be located and replaced
later.

At query time, the relevant tool runs a **similarity search** over the appropriate collection and
hands the retrieved chunks to the LLM as grounding context.

### 4.3 Hybrid retrieval: vector search *and* structured SQL

A pure vector-search approach has a well-known weakness: a similarity search returns only the
top-`k` most similar chunks (here `k≈4`), so **enumeration and aggregation questions** ("who works
in Engineering?", "how many people per department?", "who owns task X?") silently return incomplete
results once the data grows beyond the first few matches.

To solve this, the system uses a **hybrid retrieval strategy**. Alongside the vector tools it
exposes **structured query tools** that hit PostgreSQL directly and return *exact, exhaustive*
results:

- **`query_employees`** — list employees filtered by department, role, name, or active status
  (case-insensitive partial matching). Returns the complete matching set, never a sample.
- **`count_employees`** — headcounts, optionally grouped by department or role.
- **`query_tasks`** — look up tasks and their assignees/projects (joins Task → Employee/Project).
- **`query_projects`** — project details: name, description, deadline, status, task count.

The agent routes each question to the right tool:

- **Vector search** for *fuzzy / unstructured* questions — policies and "tell me about a person".
- **Structured SQL queries** for *enumeration, counting, and exact lookups* — so answers stay
  correct and complete as the database grows.

### 4.4 The agent (`rag/agent.py`)

The assistant is a **tool-using agent** created with LangChain's `create_agent` (a ReAct-style
agent running on LangGraph). The model reasons about the user's request, decides which tool — if
any — to call, observes the tool's output, and then composes a grounded natural-language answer.

The agent is given the following tools:

**Read / retrieval tools**
- `company_knowledge_tool` — vector search over company documents.
- `employee_knowledge_tool` — vector search for a single named person (fuzzy lookup).
- `query_employees`, `count_employees`, `query_tasks`, `query_projects` — structured SQL queries.
- `get_current_date` — supplies "today" for date-relative requests.

**Write / action tools**
- `add_employee_tool`, `update_employee_tool`, `deactivate_employee_tool`
- `assign_task_tool`, `add_task_to_project_tool`, `delete_task_tool`
- `create_project_tool`, `assign_employee_to_project_tool`, `deactivate_project_tool`

Two further LangGraph features are wired in:

- **Conversation memory** — a `MemorySaver` checkpointer persists per-session state, so the agent
  remembers earlier turns within a conversation. Threads are scoped per user
  (`user_{id}_{thread_id}`) so one user can never resume another user's conversation.
- **Summarization middleware** — a `SummarizationMiddleware` fires at **8 000 tokens** to compress
  older turns, keeping long conversations within the context window without losing the gist.

### 4.5 Prompt engineering (`rag/prompts/hr_prompt.py`)

Tool selection in a LangChain agent is driven almost entirely by the **tool descriptions** and the
**system prompt**. The system prompt ("Nova") therefore:

- Enumerates every tool with precise guidance on *when* to use it (e.g. "use `query_employees` for
  any enumeration question; do **not** use the vector tool to list or count people").
- Lays down behavioral rules: always query a tool before answering (never answer company facts from
  memory); never invent names, IDs, emails, or policy details; ask the user for any required field
  they did not provide; confirm every write action in plain language naming the affected record.
- Encodes the soft-delete vs. hard-delete policy (employees and projects can only be *deactivated*;
  tasks can be permanently deleted) and demonstrates the correct behavior with worked examples.

### 4.6 The vector-sync invariant (`rag/sync.py`)

Because the `employee_data` vector collection is *derived* from PostgreSQL, it must be kept in
lockstep with the relational data. After **every** write that touches an employee or their tasks,
`sync_single_employee(employee_id)` is called. It:

1. Loads the current employee row (with tasks) from PostgreSQL.
2. Deletes the stale vector document for that `employee_id`.
3. Rebuilds the document from the fresh data and re-embeds it.

This call is made both by the agent's action tools **and** by the REST API write endpoints, so the
assistant's knowledge stays consistent no matter how the data was changed. Skipping it would leave
the assistant answering from stale embeddings.

### 4.7 Chat endpoint flow (`routers/chat.py`)

```
POST /chat (or /chat/stream)
   → build messages (with a role-scoping SystemMessage for employee users)
   → agent selects a tool
       → vector search  OR  structured SQL query  OR  write action (+ vector sync)
   → LLM composes the grounded response
   → return JSON (or stream tokens via Server-Sent Events)
```

The `/chat/stream` endpoint streams the answer token-by-token over **Server-Sent Events**; tool
calls run silently in the background and only the final text is streamed to the client. The thread
ID is returned in the `X-Thread-ID` response header so the client can continue the conversation.

---

## 5. Execution instructions

### 5.1 Running with Docker (recommended)

**Prerequisites:** Docker Desktop and an OpenAI API key (used for embeddings).

1. **Create your environment file:**
   ```bash
   cp server/.env.example server/.env
   ```
2. **Edit `server/.env`** and set your own values:
   - `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`
   - `DATABASE_URL` — must match the `POSTGRES_*` values; use host **`db`** for Docker, e.g.
     `postgresql+psycopg://postgres:yourpass@db:5432/novatech` (a `@` in the password must be
     percent-encoded as `%40`).
   - `OPENAI_API_KEY` (required) and `SECRET_KEY` (required — any long random string).
3. **Run it:**
   ```bash
   docker compose up --build
   ```
4. Open **http://localhost:4200** (the API docs are at **http://localhost:8000/docs**).

On first startup the backend creates the tables, seeds reference data, and builds the vector
indexes. This takes about a minute and requires the OpenAI key.

**Useful commands:**
```bash
docker compose logs -f backend   # watch seeding + vector build
docker compose down              # stop
docker compose down -v           # stop and wipe the database volume (full reset)
```

### 5.2 Running locally (without Docker)

**Backend** (Python ≥ 3.14, [`uv`](https://docs.astral.sh/uv/)):
```bash
cd server
uv run uvicorn main:app --reload          # http://localhost:8000
```
Requires a reachable PostgreSQL (with the `vector` extension) and a `server/.env` whose
`DATABASE_URL` uses host `localhost`.

**Frontend** (Node ≥ 22, [`pnpm`](https://pnpm.io/)):
```bash
cd client
pnpm install
pnpm start                                 # http://localhost:4200
```

### 5.3 Default seeded accounts

Log in with an employee **email** as the username; the default password is **`novatech123`**.

| Role | Email |
|------|-------|
| Admin | `jane.smith@novatech.com` |
| HR | `rachel.green@novatech.com` |
| Employee | `aisha.johnson@novatech.com` |

---

## 6. Usage examples

Open **Nova Assistant** in the app and try prompts like the following.

### 6.1 Company knowledge (RAG over policy documents)

> *"What is the parental leave policy?"*
> *"How many paid holidays do we get?"*

These trigger a **vector similarity search** over the `company_knowledge` collection; the retrieved
chunks ground the model's answer.

### 6.2 Live HR data (exact, database-backed)

> *"Who works in Engineering?"* → `query_employees(department="Engineering")`
> *"How many people are in each department?"* → `count_employees(group_by="department")`
> *"Who is in charge of migrating the billing service?"* → `query_tasks(title="...")`
> *"What's the deadline for the Mobile App Launch project?"* → `query_projects(name="...")`
> *"Which projects are still in planning?"* → `query_projects(status="planning")`

These route to the **structured SQL tools**, returning exact and complete results.

### 6.3 Write actions (HR / admin)

> *"Add a new backend engineer named John Doe, john.doe@novatech.com, hired today."*
> *"Assign a task 'Write API docs' to Priya Patel."*
> *"Deactivate the Mobile App Launch project."*

The agent calls the corresponding action tool, performs the database write, **re-syncs the vector
index**, and confirms the outcome in plain language naming the affected record.

### 6.4 Example multi-step conversation

```
User:  How many engineers do we have?
Nova:  → calls count_employees(role="engineer")
       "There are 6 engineers currently active."

User:  Who are they?
Nova:  → (remembers the context) calls query_employees(role="engineer")
       "The active engineers are: ... "

User:  Add a task 'Refactor auth module' to Priya Patel.
Nova:  → calls assign_task_tool(...) then sync_single_employee(...)
       "Done — I've assigned the task 'Refactor auth module' to Priya Patel."
```

---

## 7. Security considerations

- **Authentication** — JWT bearer tokens (signed with `SECRET_KEY`), bcrypt-hashed passwords, and a
  frontend interceptor that attaches the token and signs out on `401`.
- **Role-based access** — three roles enforced by the backend. For `employee` users, the chat
  endpoint injects a scoping `SystemMessage` instructing the agent to reveal only that user's own
  records, tasks, and assigned projects.
- **Prompt-injection defense** — user input is wrapped in `<user_input>` tags and the system
  instruction explicitly tells the model to treat everything inside those tags as untrusted data,
  ignoring any embedded instructions, role changes, or override attempts.
- **Thread isolation** — conversation threads are namespaced per user (`user_{id}_{thread_id}`), so
  one user cannot resume or read another user's conversation.
- **No committed secrets** — all credentials and API keys live in the gitignored `server/.env`;
  `server/.env.example` documents every variable with placeholder values.
- **Soft-delete by default** — employees and projects are deactivated rather than destroyed,
  preserving data and audit history.