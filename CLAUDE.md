# Seller Intelligence Engine — NEXUS

## Project Overview

**Codename:** NEXUS
**Philosophy:** Local-first, platform-aware, AI-powered sales intelligence. No data leaves the machine — all inference runs via Ollama on localhost.

NEXUS is a sales intelligence engine that:
- Ingests real-time news and market signals
- Builds deep company snapshots with tech stack and competitive analysis
- Maps the ISV ecosystem per platform vendor
- Resolves and prioritizes functional-area contacts at target companies
- Generates platform-specific, conversation-ready briefs for sellers
- Coaches sellers through AI-powered roleplay simulations
- Delivers prioritized tasks via dashboard, Slack, and email

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Inference | Qwen 2.5 (14B preferred, 7B minimum) via Ollama on `localhost:11434` |
| Coaching Agent | OpenClaw (local) with SOUL.md + MEMORY.md |
| Backend | Python 3.11+ · FastAPI · SQLAlchemy (async) · Alembic |
| Frontend | React 18 · Vite · TailwindCSS · TanStack Query · Recharts |
| Database | SQLite (dev) · PostgreSQL (prod) |
| Vector Store | ChromaDB (local) |
| Task Queue | APScheduler (simple) or Celery + Redis (scale) |
| Real-time | WebSockets (FastAPI + socket.io-client) |
| Templating | Jinja2 (prompt templates in `prompts/`) |
| Testing | pytest · pytest-asyncio |
| Linting | Black (line length 88) · isort · flake8 |

---

## Architecture Pipeline

```
Platform Vendor Context (Layer 0)
        ↓
Company Snapshot Engine (Layer 1)
        ↓
ISV Landscape Intelligence (Layer 1.5)
        ↓
News & Signal Ingestion (Layer 2)
        ↓
FA Contact Intelligence (Layer 3)
        ↓
Conversation & Priority Engine — Qwen/Ollama (Layer 4)
        ↓
AI Sales Coach — OpenClaw (Layer 5)
        ↓
Seller Dashboard & Task Delivery (Layer 6)
```

---

## Project Structure

```
nexus/
├── CLAUDE.md
├── README.md
├── docker-compose.yaml
├── requirements.txt
├── package.json
│
├── config/
│   ├── platform.yaml               # Active vendor selection
│   ├── scoring.yaml                # Priority score weights
│   ├── ingestion.yaml              # News/social polling config
│   ├── platforms/
│   │   ├── google.yaml
│   │   ├── microsoft.yaml
│   │   ├── aws.yaml
│   │   ├── oracle.yaml
│   │   ├── salesforce.yaml
│   │   └── ibm.yaml
│   └── competitive/
│       └── {vendor}_vs_{vendor}.yaml
│
├── openclaw/
│   ├── config.yaml
│   ├── SOUL.md
│   └── MEMORY.md
│
├── src/
│   ├── main.py                     # FastAPI app entry point
│   ├── api/
│   │   ├── tasks.py
│   │   ├── companies.py
│   │   ├── contacts.py
│   │   ├── coaching.py
│   │   └── config.py
│   ├── ai/
│   │   ├── ollama_client.py        # Ollama/Qwen wrapper
│   │   ├── classifier.py           # News relevance classifier
│   │   ├── brief_generator.py      # Conversation brief generator
│   │   └── scorer.py               # Task priority scorer
│   ├── snapshot/
│   │   ├── aggregator.py           # Company data aggregator
│   │   ├── technographics.py       # Tech stack profiler
│   │   ├── motion_classifier.py    # Sales motion classifier
│   │   ├── competitive.py          # Competitive landscape
│   │   └── priorities.py           # Business priority extractor
│   ├── isv/
│   │   ├── scraper.py              # Marketplace scraper
│   │   ├── classifier.py           # ISV industry/capability classifier
│   │   ├── capability_mapper.py    # Business capability mapper
│   │   ├── affinity.py             # Platform affinity scorer
│   │   ├── matcher.py              # ISV-company matcher
│   │   └── storyteller.py          # ISV solution narrator
│   ├── ingestion/
│   │   ├── news.py                 # RSS + NewsAPI collector
│   │   ├── social.py               # LinkedIn + Twitter monitor
│   │   └── crm.py                  # Salesforce/HubSpot sync
│   ├── contacts/
│   │   ├── resolver.py             # Contact resolver (LinkedIn/Proxycurl)
│   │   ├── org_chart.py            # Org chart builder
│   │   └── linker.py               # Contact-news-platform linker
│   ├── coaching/
│   │   ├── prep.py                 # Pre-call prep package generator
│   │   ├── roleplay.py             # Roleplay simulator
│   │   ├── objections.py           # Objection library (ChromaDB)
│   │   ├── readiness.py            # Readiness gate scorer
│   │   └── debrief.py              # Post-call debrief analyzer
│   ├── tasks/
│   │   ├── manager.py              # Task lifecycle manager
│   │   ├── assignment.py           # Seller assignment engine
│   │   └── notifier.py             # Multi-channel notifier
│   ├── models/
│   │   ├── company.py
│   │   ├── contact.py
│   │   ├── news.py
│   │   ├── isv.py
│   │   ├── task.py
│   │   └── coaching.py
│   └── db/
│       ├── database.py
│       └── migrations/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── Dashboard.jsx
│       │   ├── TaskCard.jsx
│       │   ├── TaskDetail.jsx
│       │   ├── SnapshotViewer.jsx
│       │   ├── PlatformSelector.jsx
│       │   ├── MotionBadge.jsx
│       │   ├── CoachingPanel.jsx
│       │   ├── RoleplayChat.jsx
│       │   ├── ScorecardView.jsx
│       │   ├── ISVRecommendations.jsx
│       │   ├── CompetitiveLandscape.jsx
│       │   ├── PriorityAlignment.jsx
│       │   └── ContactCard.jsx
│       ├── hooks/
│       │   ├── useWebSocket.js
│       │   ├── useTasks.js
│       │   └── useCoaching.js
│       └── api/
│           └── client.js
│
├── prompts/
│   ├── classify_news.jinja2
│   ├── generate_brief.jinja2
│   ├── score_priority.jinja2
│   ├── classify_motion.jinja2
│   ├── build_snapshot.jinja2
│   ├── match_isv.jinja2
│   ├── roleplay_persona.jinja2
│   ├── prep_package.jinja2
│   └── debrief_analysis.jinja2
│
├── scripts/
│   ├── setup.sh
│   ├── seed_data.py
│   └── run_pipeline.py
│
└── tests/
    ├── test_snapshot.py
    ├── test_classifier.py
    ├── test_brief_generator.py
    ├── test_isv_matcher.py
    ├── test_scorer.py
    └── test_coaching.py
```

---

## Common Commands

```bash
# ── Backend Setup ──────────────────────────────────────────────────────────
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# ── Run Backend ────────────────────────────────────────────────────────────
uvicorn src.main:app --reload --port 8000

# ── Frontend Setup & Dev ───────────────────────────────────────────────────
cd frontend && npm install
npm run dev          # Vite dev server on :3000

# ── Database ───────────────────────────────────────────────────────────────
python -m src.db.database init              # Initialize schema
alembic upgrade head                        # Apply all migrations
alembic revision --autogenerate -m "desc"   # Generate new migration
alembic downgrade -1                        # Roll back one

# ── AI / Ollama ────────────────────────────────────────────────────────────
ollama serve                                # Start inference server
ollama pull qwen2.5:14b                     # Pull preferred model
ollama pull qwen2.5:7b                      # Pull fallback model

# ── Seed & Pipeline ────────────────────────────────────────────────────────
python scripts/seed_data.py                 # Seed 5-10 sample companies
python scripts/run_pipeline.py              # Manual full pipeline trigger

# ── Testing ────────────────────────────────────────────────────────────────
pytest
pytest --cov=src --cov-report=term-missing

# ── Lint & Format ──────────────────────────────────────────────────────────
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

---

## Environment Variables

```bash
# .env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b

# News
NEWSAPI_KEY=
GNEWS_KEY=

# Contact Enrichment
PROXYCURL_KEY=
CLEARBIT_KEY=
HUNTER_KEY=

# Technographics
BUILTWITH_KEY=
THEIRSTACK_KEY=

# Social
TWITTER_BEARER=
LINKEDIN_KEY=

# CRM
SF_CLIENT_ID=
SF_CLIENT_SECRET=
SF_INSTANCE_URL=

# Notifications
SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=
SMTP_HOST=
SMTP_USER=
SMTP_PASS=

# OpenClaw
OPENCLAW_PORT=3001

# Database
DATABASE_URL=sqlite:///nexus.db       # dev
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/nexus  # prod
REDIS_URL=redis://localhost:6379
```

Never commit `.env`. All API keys are optional — the system degrades gracefully with cached/mock data.

---

## Architecture & Code Style Rules

### Async-First
Use `async/await` throughout. SQLAlchemy async sessions via `asyncpg`. All Ollama calls are async HTTP.

### Layer Responsibilities
```
API layer (routers)     → validate input, call service, return HTTP response
Service layer           → business logic and orchestration, no direct DB calls
Repository layer        → all SQLAlchemy queries, returns Pydantic/domain objects
Models                  → ORM table definitions only, zero business logic
```

### Pydantic v2
All data models use Pydantic v2. Never expose SQLAlchemy ORM models directly in API responses.

### Qwen / Ollama Integration
- Every Ollama call uses **JSON mode** (`format: "json"`) for reliable structured output
- Parse all Qwen responses into Pydantic models immediately
- Wrap all Ollama calls in `src/ai/ollama_client.py` — no direct `httpx` to Ollama elsewhere
- Include retry logic and timeout handling in the client wrapper

### Prompt Templates
- All prompts live in `prompts/*.jinja2` — never inline prompt strings in Python code
- Render with `jinja2.Environment` passing context dicts
- Keep prompts versioned alongside code

### Dependency Injection
Use FastAPI `Depends()` for DB sessions and service injection. Never instantiate services directly in routes.

### Error Handling
Raise domain-specific exceptions in services. Translate to HTTP status codes at the router layer only.

---

## Layer Reference

### Layer 0 — Platform Vendor Context
**Config:** `config/platform.yaml`, `config/platforms/{vendor}.yaml`, `config/competitive/`

Seller selects their primary vendor (Google Cloud, Microsoft, AWS, Oracle, Salesforce, IBM). Selection propagates through all downstream layers — filtering news, shaping briefs, prioritizing contacts, selecting ISVs.

### Layer 1 — Company Snapshot Engine
| Module | Responsibility |
|---|---|
| `src/snapshot/aggregator.py` | Pull from SEC EDGAR, Crunchbase, LinkedIn, website scraping |
| `src/snapshot/technographics.py` | BuiltWith, TheirStack, Wappalyzer, job posting signals |
| `src/snapshot/motion_classifier.py` | Classify: WEDGE / NEW LOGO / EXPAND / DISPLACE |
| `src/snapshot/competitive.py` | Competitive landscape, market position, battle cards |
| `src/snapshot/priorities.py` | Extract business priorities from earnings calls, annual reports |

**Sales Motion Types:**
- `WEDGE` — No platform adoption. Land small POC in one functional area.
- `NEW` — Greenfield. Lead with industry relevance and multi-thread.
- `EXPAND` — Active adoption 1-2 areas. Land-and-expand adjacent workloads.
- `DISPLACE` — Using competitor. Build TCO/risk case, exec sponsor required.

### Layer 1.5 — ISV Landscape Intelligence
| Module | Responsibility |
|---|---|
| `src/isv/scraper.py` | Scrape AWS, Azure, GCP, Salesforce, ServiceNow marketplaces (weekly) |
| `src/isv/classifier.py` | Classify ISVs by industry vertical and business capability |
| `src/isv/capability_mapper.py` | Map solutions to business outcomes and KPIs |
| `src/isv/affinity.py` | Score co-sell status, integration depth, certifications |
| `src/isv/matcher.py` | Match ISVs to target companies by industry + capability gap + motion |
| `src/isv/storyteller.py` | Generate Qwen-written ISV solution narratives per company |

### Layer 2 — News & Signal Ingestion
| Module | Responsibility |
|---|---|
| `src/ingestion/news.py` | RSS/Atom, NewsAPI, SEC EDGAR — poll every 15 min, dedup by URL hash + MinHash |
| `src/ingestion/social.py` | LinkedIn + Twitter executive and company signal monitoring |
| `src/ingestion/crm.py` | Salesforce/HubSpot sync — opportunities, account tiers, engagement history |

**Signal types:** `earnings`, `product_launch`, `leadership_change`, `m_and_a`, `partnership`, `tech_initiative`

### Layer 3 — FA Contact Intelligence
| Module | Responsibility |
|---|---|
| `src/contacts/resolver.py` | LinkedIn/Proxycurl + Clearbit/Apollo + Hunter.io, 90-day cache refresh |
| `src/contacts/org_chart.py` | Qwen-inferred reporting structure, tag: Decision Maker / Influencer / Champion |
| `src/contacts/linker.py` | Triple match: news event → FA contact → platform opportunity |

### Layer 4 — Conversation & Priority Engine
| Module | Responsibility |
|---|---|
| `src/ai/ollama_client.py` | Ollama REST wrapper, JSON mode, retry/timeout, model health check |
| `src/ai/classifier.py` | Classify news: relevance 0-1, urgency, opportunity type |
| `src/ai/brief_generator.py` | Generate conversation opener, solution connection, ISV recommendation, predicted objections |
| `src/ai/scorer.py` | Score tasks 1-100 across 6 weighted factors; Qwen provides natural-language reasoning |

**Scoring weights** (configurable in `config/scoring.yaml`):
| Factor | Default Weight |
|---|---|
| Company priority alignment | 25% |
| Deal value potential | 20% |
| Contact seniority | 15% |
| Sales motion opportunity | 15% |
| News urgency | 15% |
| Platform adoption depth | 10% |

### Layer 5 — AI Sales Coach (OpenClaw + Qwen)
| Module | Responsibility |
|---|---|
| `src/coaching/prep.py` | Pre-call prep: contact dossier, company situation, ISV brief, call roadmap |
| `src/coaching/roleplay.py` | Multi-turn roleplay; prospect persona enriched with real company data |
| `src/coaching/objections.py` | ChromaDB-backed objection library; drill by industry/role/stage/motion |
| `src/coaching/readiness.py` | Readiness gate 1-10 across 5 dimensions; configurable threshold (default 7) |
| `src/coaching/debrief.py` | Post-call analysis; updates objection library + seller MEMORY.md |

**OpenClaw config:** `openclaw/config.yaml` — connects to Qwen via Ollama, SOUL.md defines coach persona.

### Layer 6 — Seller Dashboard & Task Delivery
| Component | Location |
|---|---|
| Task queue manager | `src/tasks/manager.py` |
| Seller assignment engine | `src/tasks/assignment.py` |
| Multi-channel notifier | `src/tasks/notifier.py` |
| React dashboard | `frontend/src/` |
| Company snapshot viewer | `frontend/src/components/SnapshotViewer.jsx` |

**Task lifecycle:** `created → prepped → coached → ready → in_progress → completed | snoozed | escalated`

**Notification thresholds:**
- Priority 80+: Immediate Slack DM with full brief
- Priority 50-79: Morning digest email
- Priority < 50: Dashboard only

**REST API endpoints:**
```
GET    /api/tasks
GET    /api/tasks/{id}
PATCH  /api/tasks/{id}/status
GET    /api/companies/{id}/snapshot
GET    /api/companies/{id}/isvs
GET    /api/contacts/{company_id}
GET    /api/coaching/{seller_id}
POST   /api/coaching/roleplay/start
WS     /api/tasks/stream
GET    /api/config/platform
PUT    /api/config/platform
```

---

## Build Order

Execute phases in order. Each phase produces a working, testable increment.

| Phase | Layers | Deliverable |
|---|---|---|
| 1 | Models + DB + Ollama Client + FastAPI shell | Data schemas, DB, AI connectivity, API skeleton |
| 2 | Layer 0 | Platform selection, product catalogs, competitive config |
| 3 | Layer 2 (RSS + NewsAPI only) | Working news collector with dedup and scheduling |
| 4 | Layer 4 (Classifier + Brief Generator + Scorer) | News → classified → brief → scored tasks |
| 5 | Layer 6 (Basic React task feed) | Viewable prioritized task list in browser |
| 6 | Layer 1 (Aggregator + Technographics) | Company profiles with tech stack detection |
| 7 | Layer 1 (Motion + Competitive + Priorities) | Full snapshot with sales motion and priority alignment |
| 8 | Layer 3 (Contacts) | FA contacts resolved and linked to news + platform |
| 9 | Layer 1.5 (ISV full pipeline) | ISV ecosystem mapped and matched to companies |
| 10 | Layer 5 (Coaching full stack) | AI coaching with roleplay and readiness gate |
| 11 | Layer 6 (Full UI) | Complete seller experience: snapshot, coaching, ISVs |
| 12 | Integration + Polish | End-to-end pipeline, notifications, CRM sync, tests |

**Always start with Phase 1.** Every other layer depends on the models, DB session, and Ollama client.

---

## Git Conventions

### Branch Naming
```
feature/<short-description>
fix/<short-description>
chore/<short-description>
```

### Commit Messages (Conventional Commits)
```
feat: add ISV-company matcher
fix: correct Qwen JSON parse error on empty response
chore: add APScheduler for news polling
refactor: extract brief generation into service layer
test: add unit tests for motion classifier
```

### Pull Requests
- One logical change per PR.
- CI must pass (lint + tests) before merge.
- Squash merge preferred.

---

## Testing Guidelines

- **Unit tests** mock the repository and Ollama client layers — never hit real DB or AI.
- **Integration tests** use real SQLite (or Postgres via Docker) and a live Ollama instance.
- Test file: `test_<module>.py`, test function: `test_<scenario>`.
- Target >80% coverage on service and AI layers.
- Seed data (`scripts/seed_data.py`) creates 5-10 sample companies for realistic local testing.

---

## Notes for Claude Code

1. **Start with Phase 1** — models, DB session, Ollama client, FastAPI shell. Everything else builds on this.
2. **Pydantic v2 throughout** — use `model_validate`, `model_dump`, field validators, not v1 patterns.
3. **Jinja2 prompts in `prompts/`** — never inline prompt strings in Python. Keep prompts separate for easy iteration.
4. **All Qwen calls request JSON mode** — parse responses into Pydantic models immediately after every Ollama call.
5. **Build frontend with mock data first** — complete the full UI experience with static fixtures, then wire real API calls.
6. **Seed data is critical** — the dashboard needs content immediately; seed realistic companies, contacts, and tasks.
7. **All API keys are optional** — degrade gracefully with cached or mock data when external sources are unavailable.
8. **OpenClaw is Phase 10** — the intelligence pipeline must work end-to-end before adding coaching.
9. **Local-first is a hard constraint** — no LLM API calls (no OpenAI, no Anthropic). All inference via `localhost:11434`.
10. **Test each layer independently** before integrating — the modular structure in `src/` supports this cleanly.
