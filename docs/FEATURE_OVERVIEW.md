# Service App — MVP feature overview

Technical snapshot of what exists in the repo today and what comes next. Product goals and roadmap → [`VISION.md`](VISION.md).

## Product intent

- **Primary audience**: small trade shops starting with plumbing; the repo currently ships **electrician-flavored catalog entries** only as placeholders.
- **Near-term workflows** (target product — not all built yet):
  - Capture technician narration (speech-to-text upstream, not bundled here yet).
  - Parse into structured jobs: customer, labor time, billable SKUs / line items.
  - Price lookups against internal catalogs loaded from eventual database tables.
  - **Web UI** for invoice list/detail, edit line items, and approve at home — **Phase 1b done** → [`PHASE_1B.md`](PHASE_1B.md).
  - **WhatsApp bot** for early demos: send a job note → get parsed JSON back — **Phase 1a done** → [`WHATSAPP_SETUP.md`](WHATSAPP_SETUP.md).

## What works today

| Capability | How to try it |
|------------|----------------|
| Sample price catalog | `service-app-demo` |
| LLM parse of a field log | `service-app-demo --parse '...'` (requires `OPENROUTER_API_KEY` in `.env`) |
| HTTP parse API | `service-app-api` then `POST /parse` with `{"transcript":"..."}` |
| WhatsApp demo | Twilio sandbox → Cloud Run webhook — [`WHATSAPP_SETUP.md`](WHATSAPP_SETUP.md) |
| Web invoice approval | `http://127.0.0.1:8090/app/invoices` — [`PHASE_1B.md`](PHASE_1B.md) |
| Programmatic use | `from service_app.ingestion import parse_service_call` after `pip install -e .` |

## Technical building blocks

| Area | Current state | Next steps |
|------|----------------|------------|
| LLM ingestion | [`parse_service_call`](../src/service_app/ingestion.py) + [`schemas`](../src/service_app/schemas.py) | Tune prompts from SME feedback |
| Catalog | Dict in [`catalog.py`](../src/service_app/catalog.py) | DB tables; seed plumber SKUs |
| Secrets | Env + `.env` via [`SecretsProvider`](../src/service_app/secrets.py) | GCP Secret Manager on Cloud Run |
| Database | [`models`](../src/service_app/db/models.py) — `Invoice`, `InvoiceLine` | Cloud SQL for production persistence |
| API / hosting | FastAPI + Cloud Run (`kgs-service-app`) — [`GCP_DEPLOY.md`](GCP_DEPLOY.md) | Persist deploy env vars in workflow |
| WhatsApp | Meta + Twilio webhooks; saves invoices | SME pilot sessions |
| Web UI | `/app/invoices` — list, edit, approve | Phase 2 export buttons |
| Bookkeeping | Not started | CSV export, then QuickBooks Online API |

## OpenRouter specifics

[`llm.py`](../src/service_app/llm.py) configures an `OpenAI` client with OpenRouter base URL and optional referrer headers ([OpenRouter docs](https://openrouter.ai/docs)).

Environment variables: `OPENROUTER_API_KEY` (required for `--parse`), optional `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`, `OPENROUTER_HTTP_REFERER`, `OPENROUTER_X_TITLE`. See [`.env.example`](../.env.example).

## CLI vs product

[`service_app/cli.py`](../src/service_app/cli.py) (`service-app-demo`) is a **developer demo**. End users demo via **WhatsApp** and approve invoices in the **browser**.

## Next steps

**Phase 2:** CSV/PDF export for QuickBooks. See [`VISION.md`](VISION.md).

## Naming / roadmap

Rename trade-specific modules (`catalog.py`) or split catalogs by vertical when onboarding multiple trades. Until then document which strings are electrically biased so plumbing pilots can refactor quickly.
