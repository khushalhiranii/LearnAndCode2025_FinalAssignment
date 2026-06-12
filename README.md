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

## LLM Configuration (Admin → System Configuration)

| Key | Default |
|---|---|
| `llm_provider` | `gemma` |
| `llm_api_key` | (set via Admin UI) |
| `llm_base_url` | `http://164.52.211.238/api/generate` |
| `llm_model` | `gemma3:12b-it-q8_0` |

Providers: `gemma`, `gemini`, `groq`

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
