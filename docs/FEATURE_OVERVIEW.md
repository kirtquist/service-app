# Service App — MVP feature overview

Technical snapshot of what exists in the repo today and what comes next. Product goals and roadmap → [`VISION.md`](VISION.md).

## Product intent

- **Primary audience**: small trade shops starting with plumbing; the repo currently ships **electrician-flavored catalog entries** only as placeholders.
- **Near-term workflows** (target product — not all built yet):
  - Capture technician narration (speech-to-text upstream, not bundled here yet).
  - Parse into structured jobs: customer, labor time, billable SKUs / line items.
  - Price lookups against internal catalogs loaded from eventual database tables.
  - **Web UI** for invoice list/detail, edit line items, and approve at home (Phase 1b in `VISION.md`).
  - **WhatsApp bot** for early demos: send a job note → get parsed JSON (Phase 1a in `VISION.md`).

## What works today

| Capability | How to try it |
|------------|----------------|
| Sample price catalog | `service-app-demo` |
| LLM parse of a field log | `service-app-demo --parse '...'` (requires `OPENROUTER_API_KEY` in `.env`) |
| HTTP parse API | `service-app-api` then `POST /parse` with `{"transcript":"..."}` |
| Programmatic use | `from service_app.ingestion import parse_service_call` after `pip install -e .` |

## Technical building blocks

| Area | Current state | Next steps |
|------|----------------|------------|
| LLM ingestion | [`parse_service_call`](../src/service_app/ingestion.py) + [`schemas`](../src/service_app/schemas.py) | WhatsApp webhook on [`api/app.py`](../src/service_app/api/app.py) |
| Catalog | Dict in [`catalog.py`](../src/service_app/catalog.py) | DB tables (`parts`, regional price lists); seed plumber SKUs |
| Secrets | Env + `.env` via [`SecretsProvider`](../src/service_app/secrets.py) | GCP Secret Manager on Cloud Run; see [`API_KEYS.md`](API_KEYS.md) |
| Database | SQLAlchemy `Base` + [`session`](../src/service_app/db/session.py) stubs | Phase 1b: `customer`, `job`, `invoice`, `invoice_line`; Alembic |
| API / hosting | FastAPI [`/health`](../src/service_app/api/app.py), [`/parse`](../src/service_app/api/app.py) — `service-app-api`; Dockerfile + GH Actions → Cloud Run (`kgs-service-app`) — see [`GCP_DEPLOY.md`](GCP_DEPLOY.md) |
| WhatsApp | Meta + Twilio webhooks on Cloud Run — see [`WHATSAPP_SETUP.md`](WHATSAPP_SETUP.md) | Configure secrets on Cloud Run; SME testing |
| Web UI | Not started | Invoice CRUD + approval (Phase 1b) |
| Bookkeeping | Not started | CSV export, then QuickBooks Online API (see `VISION.md`) |

## OpenRouter specifics

[`llm.py`](../src/service_app/llm.py) configures an `OpenAI` client with OpenRouter base URL and optional referrer headers ([OpenRouter docs](https://openrouter.ai/docs)).

Environment variables: `OPENROUTER_API_KEY` (required for `--parse`), optional `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`, `OPENROUTER_HTTP_REFERER`, `OPENROUTER_X_TITLE`. See [`.env.example`](../.env.example).

## CLI vs product

[`service_app/cli.py`](../src/service_app/cli.py) (`service-app-demo`) is a **developer demo**. End users will demo via **WhatsApp** (Phase 1a) and approve invoices in a **browser** (Phase 1b).

## Next steps

See **[`VISION.md` — Phase 1a checklist](VISION.md#phase-1a--checklist-get-started)** for the ordered build list (API → Cloud Run → WhatsApp → SME feedback).

## Naming / roadmap

Rename trade-specific modules (`catalog.py`) or split catalogs by vertical when onboarding multiple trades. Until then document which strings are electrically biased so plumbing pilots can refactor quickly.
