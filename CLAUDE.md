# Seller Intelligence Engine

## Project Overview

The Seller Intelligence Engine is a data-driven platform for analyzing and surfacing actionable insights about sellers — including performance metrics, risk signals, behavioral patterns, and competitive positioning. It exposes a REST API consumed by internal dashboards and downstream services.

## Tech Stack

- **Language:** Python 3.11+
- **Web Framework:** FastAPI (preferred) or Flask
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (async via `asyncpg` for FastAPI)
- **Migrations:** Alembic
- **Testing:** pytest + pytest-asyncio
- **Linting/Formatting:** Black, isort, flake8
- **Dependency Management:** pip + `requirements.txt` (or Poetry)

## Project Structure

```
seller-intelligence-engine/
├── src/
│   ├── api/            # FastAPI routers / Flask blueprints
│   ├── services/       # Business logic layer
│   ├── repositories/   # Database access layer (SQLAlchemy queries)
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic schemas (request/response)
│   └── core/           # Config, DB session, dependencies
├── migrations/         # Alembic migration scripts
├── tests/
│   ├── unit/
│   └── integration/
├── .env.example
├── requirements.txt
└── CLAUDE.md
```

## Common Commands

```bash
# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the development server (FastAPI)
uvicorn src.main:app --reload --port 8000

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Lint
flake8 src/ tests/

# Format code
black src/ tests/
isort src/ tests/

# Database migrations
alembic upgrade head           # apply all migrations
alembic revision --autogenerate -m "description"  # create new migration
alembic downgrade -1           # roll back one migration
```

## Environment Setup

Copy `.env.example` to `.env` and fill in values:

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/seller_intelligence
SECRET_KEY=your-secret-key
ENVIRONMENT=development
LOG_LEVEL=INFO
```

Load env vars via `python-dotenv` or set them in your shell. Never commit `.env`.

## Code Style

- Follow **PEP 8**. Black is the enforced formatter (line length: 88).
- Use **isort** for import ordering (Black-compatible profile).
- Use **type hints** on all function signatures.
- Use **Pydantic** schemas for all API inputs/outputs — never expose ORM models directly.
- Keep functions small and single-purpose. Prefer explicit over implicit.

### Layer Responsibilities

```
API layer (routers)     → validate input, call service, return response
Service layer           → business logic, orchestration, no direct DB calls
Repository layer        → all SQLAlchemy queries, returns domain objects
Models                  → ORM table definitions only, no business logic
```

## Architecture Notes

- **Async-first:** Use `async/await` throughout with `asyncpg` driver.
- **Dependency injection:** Use FastAPI `Depends()` for DB sessions and service injection.
- **Error handling:** Raise domain exceptions in services; translate to HTTP responses at the router layer.
- **No business logic in models:** Models are pure table definitions.
- **No raw SQL** in service or API layers — all queries go through the repository layer.

## Git Conventions

### Branch Naming
```
feature/<short-description>
fix/<short-description>
chore/<short-description>
```

### Commit Messages
Follow the Conventional Commits format:
```
feat: add seller risk score endpoint
fix: correct pagination offset calculation
chore: update alembic to 1.13
refactor: extract seller scoring into service layer
test: add unit tests for scoring service
```

### Pull Requests
- Keep PRs focused — one logical change per PR.
- All PRs require passing CI (lint + tests) before merge.
- Squash merge preferred to keep history clean.

## Testing Guidelines

- Unit tests mock the repository layer; do not hit the database.
- Integration tests use a real PostgreSQL instance (Docker Compose recommended).
- Test file naming: `test_<module>.py`, test function naming: `test_<scenario>`.
- Aim for >80% coverage on the service layer.
