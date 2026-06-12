# NovaTech Solutions — Employee Management System with an AI Assistant

A full-stack employee management platform with a **RAG (Retrieval-Augmented Generation) chatbot**.
HR and admins manage employees, projects, and tasks through a Material dashboard, and an
embedded LangChain agent ("Nova") answers questions about company policy and live HR data — and
can perform actions like adding an employee or assigning a task.

The whole stack runs with a single `docker compose up`.

> **Note:** The frontend currently implements the **HR/admin view**. The backend enforces all
> three roles (`admin`, `human_resources`, `employee`).

---

## Features

- **HR/admin dashboard** — manage all employees, projects, and tasks. The backend enforces three
  roles (`admin`, `human_resources`, `employee`); the frontend is the HR/admin view.
- **Employees / Projects / Tasks** — paginated Material tables with create/edit dialogs,
  soft-delete (deactivate), and admin-only hard delete. Inline task status changes.
- **Nova, the AI assistant** — a LangChain agent that:
  - answers **policy questions** from the company knowledge base (vector search),
  - answers **live data questions** with exact, database-backed lookups
    (who works where, headcounts, task ownership, project deadlines),
  - performs **write actions** (add/update/deactivate employee, create project, assign task),
  - streams responses token-by-token and keeps per-conversation memory.
- **JWT authentication** with an Angular HTTP interceptor and route guards.
- **Self-syncing vector index** — any employee/task write (via the UI *or* the agent) keeps the
  `employee_data` vector store consistent with PostgreSQL.

---

## Tech stack

| Layer | Technology |
|---|---|
| **Frontend** | Angular 22 (standalone, **zoneless**, signals), Angular Material, Tailwind CSS v4, **Signal Forms**, RxJS |
| **Backend** | FastAPI, SQLModel, Pydantic, Uvicorn |
| **Database** | PostgreSQL 18 + **pgvector** |
| **AI / RAG** | LangChain + LangGraph agent, `langchain-postgres` (PGVector), OpenAI (`gpt-4o-mini` + `text-embedding-3-small`), Anthropic (`claude-haiku` fallback) |
| **Auth** | JWT (`python-jose`), bcrypt |
| **Tooling** | `uv` (Python), `pnpm` (Node), Docker Compose |

---

## Architecture

```
Browser ──▶ Angular (nginx :4200) ──▶ FastAPI (:8000) ──▶ PostgreSQL + pgvector (:5432)
                                            │
                                            └─▶ LangChain agent ─▶ tools:
                                                  • vector search (policies, fuzzy lookups)
                                                  • structured SQL queries (employees/tasks/projects)
                                                  • write actions (+ vector sync)
```

The agent routes each question to the right tool: **vector search** for unstructured/fuzzy
questions (policies, "tell me about X"), and **exact PostgreSQL queries** for enumeration and
lookups ("who works in Engineering", "who owns task Y", "deadline of project Z") so answers stay
correct and complete as the data grows.

---

## Getting started (Docker — recommended)

**Prerequisites:** Docker Desktop, and an OpenAI API key (used for embeddings).

1. **Create your environment file:**
   ```bash
   cp server/.env.example server/.env
   ```
2. **Edit `server/.env`** and set your own values:
   - `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`
   - `DATABASE_URL` — must match the `POSTGRES_*` values; use host **`db`** for Docker
     (e.g. `postgresql+psycopg://postgres:yourpass@db:5432/novatech`). A `@` in the password
     must be percent-encoded as `%40`.
   - `OPENAI_API_KEY` (required) and `SECRET_KEY` (required, any long random string)
3. **Run it:**
   ```bash
   docker compose up --build
   ```
4. Open **http://localhost:4200** (API docs at **http://localhost:8000/docs**).

On first startup the backend creates the tables, **seeds reference data**, and builds the vector
indexes (this takes a minute and requires the OpenAI key).

**Useful commands:**
```bash
docker compose logs -f backend   # watch seeding + vector build
docker compose down              # stop
docker compose down -v           # stop and wipe the database volume (full reset)
```

### Default seeded accounts
Log in with an employee **email** as the username; default password **`novatech123`**.

| Role | Email |
|---|---|
| Admin | `jane.smith@novatech.com` |
| HR | `rachel.green@novatech.com` |
| Employee | `aisha.johnson@novatech.com` |

---

## Running locally (without Docker)

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

---

## Project structure

```
.
├── client/                      # Angular 22 frontend
│   ├── src/app/
│   │   ├── core/
│   │   │   ├── models/          # typed API interfaces
│   │   │   ├── auth/            # AuthService, JWT interceptor, route guards
│   │   │   └── api/             # Employee/Project/Task/Chat HTTP services
│   │   ├── pages/               # login, employees, projects, tasks, chat, side-menu (shell)
│   │   └── shared/              # reusable components (confirm dialog)
│   ├── Dockerfile               # multi-stage: pnpm build → nginx
│   └── nginx.conf
│
├── server/                      # FastAPI backend
│   ├── models/                  # SQLModel tables: Employee, Project, Task, User
│   ├── schemas/                 # Pydantic request/response contracts
│   ├── routers/                 # auth, employees, projects, tasks, chat
│   ├── rag/                     # AI layer
│   │   ├── agent.py             # LangChain/LangGraph agent + tool registry
│   │   ├── config.py            # LLM + embeddings configuration
│   │   ├── sync.py              # keeps the employee vector index in sync with the DB
│   │   ├── prompts/             # the HR system prompt
│   │   ├── tools/               # vector tools, structured query tools, write-action tools
│   │   └── vectorstores/        # PGVector company_knowledge + employee_data stores
│   ├── company_docs/            # .txt knowledge base ingested into the vector store
│   ├── main.py                  # app entry point + startup (tables, seed, vector build)
│   ├── seed.py                  # reference employees/projects/tasks
│   └── Dockerfile               # Python 3.14 + uv
│
├── docker-compose.yml           # db + backend + frontend
└── README.md
```

---

## What the assistant can do

Open **Nova Assistant** in the app and try prompts like:

**Company knowledge (policy docs):**
- *"What is the parental leave policy?"*
- *"How many paid holidays do we get?"*

**Live HR data (exact, database-backed):**
- *"Who works in Engineering?"*
- *"How many people are in each department?"*
- *"Who is in charge of migrating the billing service?"*
- *"What's the deadline for the Mobile App Launch project?"*
- *"Which projects are still in planning?"*

**Actions (HR/admin):**
- *"Add a new backend engineer named John Doe, john.doe@novatech.com, hired today."*
- *"Assign a task 'Write API docs' to Priya Patel."*
- *"Deactivate the Mobile App Launch project."*

Access is role-scoped: an `employee` user can ask about their own records and assigned projects,
but not about other employees.

---

## Notes

- `server/.env` is gitignored — never commit real credentials. `server/.env.example` documents
  every variable.
- `OPENAI_API_KEY` is always required (embeddings use OpenAI even if Anthropic is the LLM).
- Both vector collections live in the **same PostgreSQL database** via `pgvector` — there is no
  separate vector database.