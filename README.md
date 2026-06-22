# Project & Resource Management (PRM) Tool

Console client + FastAPI server for Admin, Manager, and Employee workflows.

## Architecture

- **prm-server** — FastAPI REST API, PostgreSQL, Alembic migrations, background scheduler
- **prm-client** — Rich console UI communicating over HTTP

Clean architecture layers: `domain` → `application` → `infrastructure` → `api`

## Design Patterns & SOLID

| Pattern / Principle | Where |
|---|---|
| **Repository** | `IUserRepository`, `IAllocationRepository`, etc. |
| **Unit of Work** | `UnitOfWork` binds repos to one DB session |
| **Factory** | `AIProviderFactory` — Gemma / Gemini / Groq |
| **Adapter** | `GemmaAdapter`, `GeminiAdapter`, `GroqAdapter` implement `IAIProvider` |
| **Strategy** | Project health evaluation in `ProjectHealthJob` |
| **DIP** | Use cases depend on ports, not SQLAlchemy or httpx |
| **OCP** | New LLM providers added via factory registry without changing use cases |

## Quick Start

### 1. Database (Docker)

```powershell
cd LearnAndCode2025_FinalAssignment/prm-server/docker
docker-compose up -d db
```

### 2. Server

```powershell
cd LearnAndCode2025_FinalAssignment/prm-server
pip install -e ".[dev]"
$env:DATABASE_URL = "postgresql+asyncpg://prm_user:prm_pass@localhost:5435/prm_db"
alembic upgrade head
python -m seeds.seed_admin
uvicorn src.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

### 3. Client

```powershell
cd LearnAndCode2025_FinalAssignment/prm-client
pip install -e .
$env:PRM_SERVER_URL = "http://localhost:8000"
python -m src.main
```

Default admin (change on first login): `admin` / `Admin@1234`

## LLM Configuration

Set in `.env` (server) or **Admin → System Configuration**. Env vars apply when DB values are empty.

| Env var / config key | Purpose |
|---|---|
| `LLM_PROVIDER` / `llm_provider` | `gemma`, `gemini`, `groq` |
| `LLM_API_KEY` / `llm_api_key` | API key (required for Gemini/Groq) |
| `LLM_BASE_URL` / `llm_base_url` | Ollama-compatible endpoint (required for Gemma), e.g. `http://localhost:11434/api/generate` |
| `LLM_MODEL` / `llm_model` | Model name (required for Gemma), e.g. `gemma2:9b` |

Example `.env` for local Ollama:

```env
LLM_BASE_URL=http://localhost:11434/api/generate
LLM_MODEL=gemma2:9b
```

## Email Notifications

Set `EMAIL_PROVIDER` in `.env`:

| Provider | Use case |
|----------|----------|
| `console` | Development — emails printed to server logs (default) |
| `smtp` | Production via SMTP (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, ...) |
| `gmail` | GCP Gmail API (`GMAIL_SENDER`, `GMAIL_SERVICE_ACCOUNT_FILE`) |

Install Gmail deps: `pip install -e ".[gmail]"`

**Notification 1 — Timesheet reminders:** Tue/Wed reminders, Thu freeze + email (daily 08:00 job).  
**Notification 2 — Project at-risk:** Email to manager when health transitions to `AT_RISK` (after health scheduler run).

Manager can restore frozen timesheet access: `POST /manager/employees/{id}/restore-timesheet-access`

## Background Scheduler

Runs on a daemon thread at startup. Jobs:
- Flag missed timesheets for allocated employees
- Recompute project health snapshots (ON_TRACK / ATTENTION / AT_RISK)

Interval configurable via Admin (default: 4 hours).

## Tests

```powershell
cd prm-server
pytest --cov=src/application --cov-report=term-missing
```

Target: ≥60% coverage on `src/application/`.
