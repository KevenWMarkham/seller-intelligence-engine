# NEXUS — Implementation Roadmap

> **Codename:** NEXUS · Seller Intelligence Engine
> **Stack:** Python 3.11 · FastAPI · React 18 · Qwen 2.5 via Ollama · SQLite/PostgreSQL · ChromaDB
> **Principle:** Local-first. No data leaves the machine. All inference via `localhost:11434`.

---

## How to Use This Roadmap

- Phases must be executed **in order** — each phase depends on foundations from the prior one.
- Check boxes as items are completed: change `[ ]` to `[x]`.
- Each phase maps 1:1 to a Sprint in `backlog.md`.
- Execution guidance lives in `orchestrator.md`.

---

## Progress Summary

| Phase | Name | Status |
|-------|------|--------|
| 1 | Foundation — Models, DB, Ollama, FastAPI | `[x] Complete` |
| 2 | Platform Context (Layer 0) | `[x] Complete` |
| 3 | News Ingestion (Layer 2) | `[x] Complete` |
| 4 | AI Engine (Layer 4) | `[x] Complete` |
| 5 | Basic Dashboard (Layer 6 MVP) | `[x] Complete` |
| 6 | Company Snapshot Part 1 (Layer 1) | `[x] Complete` |
| 7 | Company Snapshot Part 2 (Layer 1) | `[ ] Not Started` |
| 8 | Contact Intelligence (Layer 3) | `[ ] Not Started` |
| 9 | ISV Intelligence (Layer 1.5) | `[ ] Not Started` |
| 10 | AI Coaching (Layer 5) | `[ ] Not Started` |
| 11 | Full Dashboard UI (Layer 6 Complete) | `[ ] Not Started` |
| 12 | Integration, Notifications & Polish | `[ ] Not Started` |

---

## Phase 1 — Foundation

> **Goal:** Working data layer, async DB session, Ollama connectivity, and FastAPI skeleton. Every other phase builds on this.

### 1.1 Data Models (Pydantic v2 + SQLAlchemy ORM)

- [x] `src/models/company.py` — `Company`, `CompanyProfile`, `TechProfile`, `SalesMotion`, `CompetitiveSnapshot`, `CompanyPriority`
- [x] `src/models/contact.py` — `Contact`, `EnrichedContact`, `OrgMap`
- [x] `src/models/news.py` — `NewsItem`, `SocialSignal`, `CompanyEvent`, `ClassifiedNews`
- [x] `src/models/isv.py` — `ISVSolution`, `ISVMatch`, `PlatformAffinity`, `CapabilityMap`
- [x] `src/models/task.py` — `SellerTask`, `ConversationBrief`, `PriorityScore`
- [x] `src/models/coaching.py` — `PrepPackage`, `RoleplayScorecard`, `ReadinessScore`, `DebriefAnalysis`

### 1.2 Database Layer

- [x] `src/db/database.py` — async SQLAlchemy engine, session factory, `get_db` dependency
- [x] SQLite config for dev (`nexus.db`), PostgreSQL connection string for prod
- [x] `alembic.ini` and `src/db/migrations/` initialized
- [x] Initial Alembic migration covering all ORM tables
- [x] `python -m src.db.database init` command works

### 1.3 Ollama / Qwen Client

- [x] `src/ai/ollama_client.py` — async HTTP wrapper for `localhost:11434`
- [x] JSON mode support (`format: "json"`) on every generate call
- [x] Model selection: `qwen2.5:14b` preferred, `qwen2.5:7b` fallback
- [x] Health check endpoint (`GET /api/tags`)
- [x] Retry logic (3 attempts, exponential backoff)
- [x] 60-second timeout with configurable override
- [x] Parse raw Ollama response into Pydantic model immediately after every call

### 1.4 FastAPI Application Shell

- [x] `src/main.py` — FastAPI app with CORS, lifespan hooks, router registration
- [x] `src/api/tasks.py` — stub routes: `GET /api/tasks`, `GET /api/tasks/{id}`, `PATCH /api/tasks/{id}/status`
- [x] `src/api/companies.py` — stub routes: `GET /api/companies/{id}/snapshot`, `GET /api/companies/{id}/isvs`
- [x] `src/api/contacts.py` — stub: `GET /api/contacts/{company_id}`
- [x] `src/api/coaching.py` — stubs: `GET /api/coaching/{seller_id}`, `POST /api/coaching/roleplay/start`
- [x] `src/api/config.py` — stubs: `GET /api/config/platform`, `PUT /api/config/platform`
- [x] WebSocket stub: `WS /api/tasks/stream`
- [x] `uvicorn src.main:app --reload --port 8000` starts cleanly

### 1.5 Project Scaffolding

- [x] `requirements.txt` complete with all pinned dependencies
- [x] `frontend/package.json` with all React dependencies
- [x] `.env.example` with all environment variable keys documented
- [x] `scripts/setup.sh` — one-command local environment bootstrap
- [x] `pytest` runs (17 tests passing)

### 1.6 Phase 1 Validation

- [x] `uvicorn src.main:app --reload` — server starts on `:8000`
- [x] `curl http://localhost:8000/api/tasks` — returns `{"tasks":[],"count":0}`
- [x] `curl http://localhost:11434/api/tags` — Qwen model visible
- [x] Ollama client `generate()` returns parsed Pydantic model

---

## Phase 2 — Platform Vendor Context (Layer 0)

> **Goal:** Seller can select their primary platform vendor. Selection propagates through all downstream layers.

### 2.1 Platform Configuration

- [x] `config/platform.yaml` — active vendor selection with schema
- [x] `config/platforms/google.yaml` — GCP product catalog + workload mappings
- [x] `config/platforms/microsoft.yaml` — Azure/M365 product catalog
- [x] `config/platforms/aws.yaml` — AWS product catalog
- [x] `config/platforms/oracle.yaml` — OCI/Fusion product catalog
- [x] `config/platforms/salesforce.yaml` — Salesforce product catalog
- [x] `config/platforms/ibm.yaml` — IBM/Red Hat product catalog

### 2.2 Competitive Configuration

- [x] `config/competitive/` — at minimum 3 vendor vs. vendor YAML files
- [x] Each file: win themes, displacement narratives, tracked competitor signals
- [x] Example: `google_vs_aws.yaml`, `microsoft_vs_aws.yaml`, `google_vs_azure.yaml`

### 2.3 Platform Context Service

- [x] `src/api/config.py` — `GET /api/config/platform` reads `config/platform.yaml`
- [x] `PUT /api/config/platform` — writes vendor selection to `config/platform.yaml`
- [x] Platform context injected into FastAPI request state via dependency
- [x] Product-to-workload mapping function: `map_workload(vendor, workload) -> list[str]`

### 2.4 Phase 2 Validation

- [x] `PUT /api/config/platform {"vendor": "google"}` — persists selection
- [x] `GET /api/config/platform` — returns correct vendor + product catalog
- [x] Platform YAML files load without error

---

## Phase 3 — News & Signal Ingestion (Layer 2)

> **Goal:** Real-time news collected, deduplicated, normalized, and stored. RSS + NewsAPI only (social and CRM come later).

### 3.1 News Collector

- [x] `src/ingestion/news.py` — `NewsCollector` class
- [x] RSS/Atom feed polling via `feedparser` with configurable URL list
- [x] NewsAPI.org integration (keyword-filtered, rate-limited)
- [x] SEC EDGAR RSS feed for tracked companies
- [x] URL-hash deduplication (exact match)
- [x] MinHash near-duplicate detection (Jaccard similarity threshold 0.85)
- [x] Platform relevance boost scoring (0.0–1.0) based on vendor keywords
- [x] Signal type classification: `earnings | product_launch | leadership_change | m_and_a | partnership | tech_initiative`
- [x] Store to `news_items` DB table

### 3.2 Ingestion Configuration

- [x] `config/ingestion.yaml` — poll interval, RSS URLs, NewsAPI config, SEC tickers
- [x] Environment variable injection for API keys (`${NEWSAPI_KEY}`)
- [x] Graceful degradation when API key absent (RSS only mode)

### 3.3 Scheduler

- [x] APScheduler integration in `src/main.py` lifespan
- [x] News polling job: every 15 minutes (configurable)
- [x] Job status logging

### 3.4 Phase 3 Validation

- [x] Manual trigger: `python scripts/run_pipeline.py --layer news`
- [x] 10+ news items visible in DB after one poll cycle (47 collected)
- [x] Deduplication confirmed: same URL not inserted twice
- [x] `GET /api/tasks` still returns `[]` (AI layer not built yet)

---

## Phase 4 — Conversation & Priority Engine (Layer 4)

> **Goal:** News → Qwen classification → conversation briefs → scored tasks. The core AI loop.

### 4.1 Prompt Templates

- [x] `prompts/classify_news.jinja2` — relevance, urgency, opportunity type classification
- [x] `prompts/generate_brief.jinja2` — conversation opener, why it matters, solution connection, suggested ask, predicted objections
- [x] `prompts/score_priority.jinja2` — 6-factor weighted scoring with Qwen reasoning
- [x] `prompts/classify_motion.jinja2` — WEDGE / NEW / EXPAND / DISPLACE classification
- [x] All prompts request JSON mode output
- [x] Jinja2 `Environment` loader configured in `src/ai/`

### 4.2 News Classifier

- [x] `src/ai/classifier.py` — `classify_news(headline, body, platform_vendor, watched_companies)`
- [x] Returns `NewsClassification` Pydantic model
- [x] Filters relevance < 0.3 before brief generation

### 4.3 Brief Generator

- [x] `src/ai/brief_generator.py` — `generate_brief(...)`
- [x] Returns `ConversationBrief` Pydantic model
- [x] Sales motion-aware templates (different brief shape per motion type)
- [x] Includes predicted objections per brief

### 4.4 Priority Scorer

- [x] `src/ai/scorer.py` — `score_task(...)`
- [x] Returns `PriorityScore` with `score: int`, `reasoning: str`, `factor_scores: dict`
- [x] Scoring weights loaded from `config/scoring.yaml`
- [x] `config/scoring.yaml` — default weights for all 6 factors

### 4.5 Task Creation Pipeline

- [x] `src/ai/pipeline.py` — `run_ai_pipeline(session)` orchestrates full flow
- [x] Pipeline: classify → filter → brief → score → create task
- [x] Task deduplication: one task per (company, news_item) pair
- [x] Store to `seller_tasks` DB table

### 4.6 Phase 4 Validation

- [x] `python scripts/run_pipeline.py --layer ai` — processes staged news items
- [x] `GET /api/tasks` — returns 3 scored tasks (seeds: Acme/85, GlobalData/70, RetailNow/55)
- [x] Task has: `priority_score`, `conversation_brief_json.opener`, `predicted_objections`
- [x] Qwen response is valid JSON, parsed into Pydantic models

---

## Phase 5 — Basic Seller Dashboard (Layer 6 MVP)

> **Goal:** Sellers can view their prioritized task queue in a browser. Mock data first, then wire real API.

### 5.1 Frontend Foundation

- [x] `frontend/` — Vite + React 18 + TailwindCSS configured
- [x] `frontend/src/api/client.js` — fetch wrapper for FastAPI backend
- [x] `frontend/src/App.jsx` — router setup (React Router v6)
- [x] TailwindCSS configured with dark mode

### 5.2 Dashboard Components (mock data first)

- [x] `frontend/src/components/Dashboard.jsx` — main task feed layout with status/priority filters
- [x] `frontend/src/components/TaskCard.jsx` — priority score badge, company, contact name, motion badge
- [x] `frontend/src/components/TaskDetail.jsx` — full conversation brief, objections, action buttons
- [x] `frontend/src/components/MotionBadge.jsx` — WEDGE / NEW / EXPAND / DISPLACE chip
- [x] `frontend/src/components/PlatformSelector.jsx` — vendor dropdown in nav
- [x] `frontend/src/components/ContactCard.jsx` — name, title, LinkedIn link, role badge

### 5.3 React Hooks

- [x] `frontend/src/hooks/useTasks.js` — TanStack Query hook for `GET /api/tasks`
- [x] `frontend/src/hooks/useWebSocket.js` — WebSocket client for `WS /api/tasks/stream`

### 5.4 WebSocket Task Stream

- [x] `src/api/tasks.py` — `WS /api/tasks/stream` — connection handling ready (broadcast in Sprint 11)
- [x] Frontend WebSocket hook connects and handles messages

### 5.5 Phase 5 Validation

- [x] `npm run dev` — Vite dev server starts on `:3000`
- [x] Task list loads from `GET /api/tasks` with enriched company + contact objects
- [x] Task card shows priority score, company, motion badge
- [x] Task detail shows full conversation brief with copy-to-clipboard opener
- [x] Action buttons (Start, Complete, Snooze) call PATCH `/api/tasks/{id}/status`

---

## Phase 6 — Company Snapshot Part 1 (Layer 1)

> **Goal:** Company profiles with real tech stack data. Aggregator + technographics.

### 6.1 Company Data Aggregator

- [x] `src/snapshot/aggregator.py` — `aggregate_company(domain, ticker, name)` waterfall
- [x] SEC EDGAR API integration — fetch 10-K/10-Q filings via free EDGAR API
- [x] Crunchbase API integration (graceful degradation if key absent)
- [x] Company website scraper (BeautifulSoup) — About, homepage, www variants
- [x] Returns `CompanyProfile` Pydantic model

### 6.2 Technographic Profiler

- [x] `src/snapshot/technographics.py` — `profile_tech_stack(domain)` waterfall
- [x] BuiltWith API integration (graceful degradation)
- [x] TheirStack API integration (graceful degradation)
- [x] Website technology detection via regex patterns (15 stacks)
- [x] Cross-reference detected tech against platform vendor catalogs (config/platforms/*.yaml)
- [x] Returns `TechProfile` with `platform_adoption` per vendor

### 6.3 Snapshot API

- [x] `src/api/companies.py` — `GET /api/companies/{id}/snapshot` returns enriched profile
- [x] Live tech profiling on-the-fly when no cached data in DB

### 6.4 Seed Data

- [x] `scripts/seed_data.py` — 5 sample companies with realistic profiles (from prior sprints)
- [x] Companies span different industries, motions, and platform adoptions

### 6.5 Phase 6 Validation

- [x] `python scripts/seed_data.py` completes without error
- [x] `GET /api/companies/1/snapshot` — returns company profile with tech stack
- [x] 17 new unit tests; 77 total passing

---

## Phase 7 — Company Snapshot Part 2 (Layer 1)

> **Goal:** Full snapshot with sales motion classification, competitive landscape, and priority extraction.

### 7.1 Sales Motion Classifier

- [ ] `src/snapshot/motion_classifier.py` — `MotionClassifier.classify(tech_profile, platform_vendor)`
- [ ] Qwen prompt via `prompts/classify_motion.jinja2`
- [ ] Returns `SalesMotion`: type, confidence, reasoning, entry_points, competitor_to_displace

### 7.2 Competitive Analyzer

- [ ] `src/snapshot/competitive.py` — `CompetitiveAnalyzer.analyze(company_profile, platform_vendor)`
- [ ] Parse earnings call transcripts for competitive mentions
- [ ] Cross-reference against `config/competitive/` battle cards
- [ ] Returns `CompetitiveSnapshot`: market_position, competitors[], strengths, vulnerabilities

### 7.3 Priority Extractor

- [ ] `src/snapshot/priorities.py` — `PriorityExtractor.extract(company_profile)`
- [ ] Extract from: earnings call text, annual report strategy sections, job posting patterns
- [ ] Map each priority to platform capabilities (alignment score)
- [ ] Returns `list[CompanyPriority]` with platform product alignment

### 7.4 Build Snapshot Prompt

- [ ] `prompts/build_snapshot.jinja2` — full snapshot synthesis prompt
- [ ] Qwen generates 3-paragraph company description + priority alignment summary

### 7.5 Phase 7 Validation

- [ ] `GET /api/companies/1/snapshot` — includes `sales_motion`, `competitive`, `priorities`
- [ ] Sales motion is one of: WEDGE / NEW / EXPAND / DISPLACE
- [ ] `SnapshotViewer.jsx` mock data updated to show motion + competitive cards

---

## Phase 8 — FA Contact Intelligence (Layer 3)

> **Goal:** Functional area contacts resolved, org chart built, contacts linked to news events and platform opportunities.

### 8.1 Contact Resolver

- [ ] `src/contacts/resolver.py` — `ContactResolver.resolve(company_id)`
- [ ] Proxycurl API integration (graceful degradation)
- [ ] Clearbit/Apollo integration (graceful degradation)
- [ ] Hunter.io email enrichment (graceful degradation)
- [ ] 90-day cache: skip refresh if contact fresher than 90 days
- [ ] Returns `list[EnrichedContact]`

### 8.2 Org Chart Builder

- [ ] `src/contacts/org_chart.py` — `OrgChartBuilder.build(contacts)`
- [ ] Qwen-inferred reporting structure from title patterns
- [ ] Tag each contact: `decision_maker | influencer | champion`
- [ ] Map functional areas: Engineering, Finance, Sales, Marketing, Operations, HR, Legal, Product
- [ ] Returns `OrgMap`

### 8.3 Contact-News Linker

- [ ] `src/contacts/linker.py` — `ContactNewsLinker.link(news_item, org_map, platform_vendor)`
- [ ] Rule engine: signal type → functional area mapping
  - [ ] Cloud migration news → CTO / VP Engineering
  - [ ] Earnings miss → CFO / CEO
  - [ ] Product launch → VP Product / CMO
  - [ ] Data breach → CISO / CTO
  - [ ] AI initiative → CTO / VP Data Science
- [ ] Returns `ContactNewsMatch` with relevance score and conversation angle

### 8.4 Contact API

- [ ] `GET /api/contacts/{company_id}` — returns enriched contacts with org chart
- [ ] Contacts included in task generation pipeline (tasks now have real contacts)
- [ ] `ContactCard.jsx` wired to real contact data

### 8.5 Phase 8 Validation

- [ ] `GET /api/contacts/1` — returns 3+ contacts with roles and functional areas tagged
- [ ] Task cards show real contact names, titles, LinkedIn URLs
- [ ] Linker correctly routes cloud migration news to CTO/VP Eng contacts

---

## Phase 9 — ISV Landscape Intelligence (Layer 1.5)

> **Goal:** ISV ecosystem mapped per platform, classified by capability, matched to target companies, solution stories generated.

### 9.1 Marketplace Scraper

- [ ] `src/isv/scraper.py` — `MarketplaceScraper.scrape(platform_vendor)`
- [ ] AWS Marketplace scraper
- [ ] Azure Marketplace / AppSource scraper
- [ ] Google Cloud Marketplace scraper
- [ ] Salesforce AppExchange scraper
- [ ] Weekly schedule via APScheduler
- [ ] Incremental updates (only new/changed listings)
- [ ] Store to `isv_solutions` table

### 9.2 ISV Classifier

- [ ] `src/isv/classifier.py` — `ISVClassifier.classify(isv_solution)`
- [ ] Industry vertical taxonomy (8 verticals from design spec)
- [ ] Business capability taxonomy (8 capabilities from design spec)
- [ ] Qwen classification via `prompts/` — handles multi-industry, multi-capability ISVs

### 9.3 Business Capability Mapper

- [ ] `src/isv/capability_mapper.py` — `CapabilityMapper.map(isv_solution, company_context)`
- [ ] Extract: business outcomes, processes improved, KPIs impacted
- [ ] Returns `CapabilityMap`

### 9.4 Platform Affinity Scorer

- [ ] `src/isv/affinity.py` — `AffinityScorer.score(isv, platform_vendor)`
- [ ] Score: co-sell status, marketplace listing depth, joint case studies, integration points, cert level
- [ ] Returns `PlatformAffinity`

### 9.5 ISV-Company Matcher

- [ ] `src/isv/matcher.py` — `ISVMatcher.match(company_snapshot, platform_vendor)`
- [ ] Match algorithm: industry fit × capability gap × platform alignment × motion fit
- [ ] Prompt: `prompts/match_isv.jinja2`
- [ ] Returns `list[ISVMatch]` sorted by fit_score descending

### 9.6 Solution Storyteller

- [ ] `src/isv/storyteller.py` — `SolutionStoryteller.narrate(isv_match, company_snapshot)`
- [ ] Qwen generates: plain-English solution description, company priority mapping, business outcomes, platform integration story
- [ ] Returns `SolutionStory`

### 9.7 ISV API & UI

- [ ] `GET /api/companies/{id}/isvs` — returns ranked ISV matches
- [ ] `ISVRecommendations.jsx` — renders ISV cards with motion badge, co-sell indicator, outcome
- [ ] ISV recommendations included in `ConversationBrief` (top 2 ISVs per task)

### 9.8 Phase 9 Validation

- [ ] `GET /api/companies/1/isvs` — returns 3+ ISV matches with fit scores
- [ ] ISV narratives are business-value language (not marketing speak)
- [ ] ISVs show co-sell indicator where applicable
- [ ] Top ISVs appear in task conversation briefs

---

## Phase 10 — AI Sales Coach (Layer 5)

> **Goal:** Pre-call prep engine, roleplay simulator, objection library, readiness gate, post-call debrief. All powered by Qwen via Ollama.

### 10.1 OpenClaw Setup

- [ ] `openclaw/config.yaml` — Ollama provider, Qwen endpoint, Slack + web channels configured
- [ ] `openclaw/SOUL.md` — sales coach persona: expert B2B coach, direct, motion-aware, 5 coaching modes
- [ ] `openclaw/MEMORY.md` — seller profile template with strengths, growth areas, active accounts

### 10.2 Pre-Call Prep Engine

- [ ] `src/coaching/prep.py` — `PrepEngine.generate(task_id, seller_id)`
- [ ] Contact dossier: role, tenure, communication style, recent signals
- [ ] Company situation: news triggers, financial health, competitive position
- [ ] ISV solution brief: top 2 ISVs for this account
- [ ] Conversation roadmap: 4-step (open → discover → value → ask)
- [ ] Predicted objections with scripted responses (role/industry/motion-specific)
- [ ] Success metrics definition
- [ ] Prompt: `prompts/prep_package.jinja2`
- [ ] Returns `PrepPackage`

### 10.3 Roleplay Simulator

- [ ] `src/coaching/roleplay.py` — `RoleplaySimulator.start(task_id, seller_id)`
- [ ] Multi-turn conversation via Qwen — coach plays prospect persona enriched with real company data
- [ ] Prospect persona driven by real contact data (Bob Chen's actual skepticisms, Acme's actual AWS dependency)
- [ ] Prompt: `prompts/roleplay_persona.jinja2`
- [ ] After session: generate `RoleplayScorecard` (5 dimensions, 1–10)

### 10.4 Objection Library

- [ ] `src/coaching/objections.py` — `ObjectionLibrary` backed by ChromaDB
- [ ] Index by: industry, contact role, deal stage, sales motion
- [ ] Add new objections from roleplay sessions and real call debriefs
- [ ] `drill(filter)` — return 5 relevant objections for practice
- [ ] Track improvement over time per seller per objection category

### 10.5 Readiness Gate

- [ ] `src/coaching/readiness.py` — `ReadinessGate.assess(roleplay_scorecard, prep_completion)`
- [ ] Score 5 dimensions: product knowledge, contact knowledge, objection handling, conversation flow, confidence
- [ ] Configurable threshold (default 7/10)
- [ ] Returns `ReadinessScore` with `gate_passed: bool` and recommendations

### 10.6 Post-Call Debrief

- [ ] `src/coaching/debrief.py` — `DebriefAnalyzer.analyze(task_id, seller_notes)`
- [ ] Analyze vs prep package: what was predicted vs what happened
- [ ] Add new objections to ChromaDB library
- [ ] Update `openclaw/MEMORY.md` seller profile
- [ ] Generate follow-up tasks
- [ ] Prompt: `prompts/debrief_analysis.jinja2`
- [ ] Returns `DebriefAnalysis`

### 10.7 Coaching API

- [ ] `GET /api/coaching/{seller_id}` — coaching history, current readiness scores
- [ ] `POST /api/coaching/roleplay/start` — starts roleplay session, returns session_id
- [ ] Task status transitions: `prepped → coached → ready` gated by readiness score

### 10.8 Phase 10 Validation

- [ ] `POST /api/coaching/roleplay/start` — returns session_id, roleplay begins
- [ ] Multi-turn roleplay conversation with real persona data
- [ ] After roleplay: `GET /api/coaching/{seller_id}` shows updated readiness score
- [ ] Readiness gate blocks task to "ready" status if score < 7

---

## Phase 11 — Full Dashboard UI (Layer 6 Complete)

> **Goal:** Complete seller experience: snapshot viewer, ISV cards, coaching panel, competitive landscape, all wired to real API.

### 11.1 Company Snapshot Viewer

- [ ] `SnapshotViewer.jsx` — full company deep-dive panel
  - [ ] Company overview (revenue, headcount, stage, HQ)
  - [ ] Tech stack visualization with platform adoption bars
  - [ ] Competitive landscape with battle cards (`CompetitiveLandscape.jsx`)
  - [ ] Priority alignment matrix (`PriorityAlignment.jsx`) — company priorities × platform capabilities
  - [ ] ISV ecosystem fit panel (`ISVRecommendations.jsx`)

### 11.2 Coaching Interface

- [ ] `CoachingPanel.jsx` — prep package display, readiness score, action buttons
- [ ] `RoleplayChat.jsx` — inline multi-turn chat with OpenClaw coach
- [ ] `ScorecardView.jsx` — 5-dimension readiness scorecard with progress bars
- [ ] `useCoaching.js` hook — TanStack Query for coaching endpoints

### 11.3 Dashboard Enhancements

- [ ] Filter bar: filter tasks by company, motion type, priority range, platform, coaching status
- [ ] Team lead view: all team tasks, coaching readiness heatmap
- [ ] Task card shows coaching readiness badge (not started / prepped / coached / ready)
- [ ] Action buttons: Prep, Practice, Ready, Complete, Snooze, Escalate, Add Notes

### 11.4 Phase 11 Validation

- [ ] Full seller journey works end-to-end in UI: task → snapshot → coaching → ready
- [ ] Snapshot viewer shows populated data for seeded companies
- [ ] Roleplay chat works inline via coaching panel
- [ ] Readiness scorecard displays and updates

---

## Phase 12 — Integration, Notifications & Polish

> **Goal:** Full end-to-end pipeline, Slack/email notifications, CRM sync, test coverage, production readiness.

### 12.1 Social Signal Monitor

- [ ] `src/ingestion/social.py` — LinkedIn and X/Twitter monitoring
- [ ] LinkedIn company page updates and executive post tracking
- [ ] X API v2 keyword and mention tracking
- [ ] Signal normalization into `NewsItem` schema
- [ ] Graceful degradation when credentials absent

### 12.2 CRM Pipeline Sync

- [ ] `src/ingestion/crm.py` — Salesforce/HubSpot API sync
- [ ] Pull: opportunities, account tiers, deal stages, seller assignments, last activity
- [ ] Enrich tasks with CRM deal data (improves priority scoring)
- [ ] Webhook listener for real-time CRM events
- [ ] Write tasks back to CRM as activities/tasks

### 12.3 Seller Assignment Engine

- [ ] `src/tasks/assignment.py` — route tasks to correct seller
- [ ] CRM account ownership → named account lists → territory rules → round-robin fallback
- [ ] Team lead visibility across all team tasks

### 12.4 Multi-Channel Notifier

- [ ] `src/tasks/notifier.py` — Slack, email, CRM task write
- [ ] Priority 80+: immediate Slack DM with full brief + "Start Coaching" button
- [ ] Priority 50–79: morning digest email
- [ ] Priority < 50: dashboard only
- [ ] Configurable thresholds per seller in DB

### 12.5 Test Coverage

- [ ] `tests/test_snapshot.py` — unit tests for aggregator, technographics, motion classifier
- [ ] `tests/test_classifier.py` — news classifier with mocked Ollama responses
- [ ] `tests/test_brief_generator.py` — brief generation with mocked Ollama
- [ ] `tests/test_isv_matcher.py` — ISV matching algorithm
- [ ] `tests/test_scorer.py` — priority scoring with weight validation
- [ ] `tests/test_coaching.py` — prep engine, readiness gate, debrief analyzer
- [ ] All Ollama calls mocked in unit tests (no real inference in CI)
- [ ] Coverage target: >80% on service and AI layers

### 12.6 Production Readiness

- [ ] `docker-compose.yaml` — Postgres + Redis + app containers
- [ ] PostgreSQL migration tested end-to-end (alembic upgrade head)
- [ ] Environment variable validation on startup (fail fast if required keys missing)
- [ ] Structured logging (JSON format, configurable level)
- [ ] Health check endpoint: `GET /api/health`
- [ ] `README.md` — complete setup and quickstart documentation

### 12.7 Phase 12 Validation

- [ ] `pytest --cov=src --cov-report=term-missing` — >80% coverage
- [ ] Full pipeline: seed data → news poll → AI processing → task in dashboard → coaching → complete
- [ ] Slack notification fires for task with priority > 80
- [ ] `docker-compose up` — all services start cleanly

---

## Completion Criteria

The NEXUS system is complete when:

- [ ] All 12 phases checked off above
- [ ] Full pipeline runs unattended for 24 hours without error
- [ ] 5 seeded companies each have: snapshot, contacts, ISV recommendations, scored tasks
- [ ] A seller can complete the full journey: task → prep → roleplay → ready → call → debrief
- [ ] Test coverage > 80% on AI and service layers
- [ ] No API keys required for core functionality (graceful degradation throughout)
