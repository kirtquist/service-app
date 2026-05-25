# Service App — MVP feature overview

Technical snapshot of what exists in the repo today and what comes next. Product goals and roadmap → [`VISION.md`](VISION.md).

## Product intent

- **Primary audience**: small trade shops starting with plumbing; the repo currently ships **electrician-flavored catalog entries** only as placeholders.
- **Near-term workflows**:
  - Capture technician narration → parse → price → **approve in browser** (Phase 1b ✅)
  - **Export** approved invoices as CSV (QuickBooks) or PDF (Phase 2 ✅)
  - QuickBooks Online API sync (Phase 3)

## What works today

| Capability | How to try it |
|------------|----------------|
| Sample price catalog | `service-app-demo` |
| LLM parse | `service-app-demo --parse '...'` or `POST /parse` |
| WhatsApp demo | [`WHATSAPP_SETUP.md`](WHATSAPP_SETUP.md) |
| Web invoice approval | `/app/invoices` — [`PHASE_1B.md`](PHASE_1B.md) |
| CSV / PDF export | Approved invoice detail → Download buttons — [`PHASE_2.md`](PHASE_2.md) |

## Technical building blocks

| Area | Current state | Next steps |
|------|----------------|------------|
| LLM ingestion | OpenRouter parse + Pydantic validation | SME prompt tuning |
| Catalog | In-memory dict | Plumber SKUs in DB |
| Database | SQLite local; **Cloud SQL Postgres** prod (Pulumi) | Alembic migrations |
| API / hosting | FastAPI on Cloud Run | — |
| WhatsApp | Twilio + Meta webhooks; saves invoices | Voice notes |
| Web UI | List, edit, approve, export | Phase 3 QBO connect |
| Bookkeeping | CSV + PDF export | QuickBooks Online API |

## Database

- **Local:** SQLite `./data/service_app.db` (default)
- **Production:** PostgreSQL 15 on GCP Cloud SQL — provisioned in [`infra/`](../infra/README.md), connection via Secret Manager `database-url`

See [`PHASE_2.md`](PHASE_2.md) for architecture and deploy steps.

## Next steps

**Phase 3:** QuickBooks Online OAuth and one-way invoice sync. See [`VISION.md`](VISION.md).

**SME validation (pre-Phase 3):** [`SME_INTERVIEW.md`](SME_INTERVIEW.md) — local test checklist: [`PRE_PHASE3_TEST_PLAN.md`](PRE_PHASE3_TEST_PLAN.md).
