# service-app

MVP scaffolding for a **field-service** style app aimed first at trades such as plumbing. The bundled **price catalog mock data skews electrician** until you swap SKUs toward pipes, fittings, and fixtures.

**Product direction:** web-based invoice review and approval at home, with future QuickBooks sync — see [`docs/VISION.md`](docs/VISION.md). The CLI is for development and testing only.

## Features (current)

- **OpenRouter**: Chat Completions via the OpenAI Python SDK pointing at OpenRouter (`OPENROUTER_API_KEY`).
- **Structured parsing**: Rough technician transcripts → validated JSON (customer, parts, labor hours) via Pydantic.
- **HTTP API**: FastAPI `GET /health`, `POST /parse`, WhatsApp webhooks (`service-app-api`).
- **WhatsApp demo**: Twilio sandbox or Meta Cloud API → parsed JSON reply — [`docs/WHATSAPP_SETUP.md`](docs/WHATSAPP_SETUP.md).
- **Web approval UI**: Review and approve invoices at `/app/invoices` — [`docs/PHASE_1B.md`](docs/PHASE_1B.md).
- **Invoice persistence**: SQLAlchemy `Invoice` + `InvoiceLine` models (SQLite by default).
- **Secrets hook**: [`EnvSecretsProvider`](src/service_app/secrets.py) reads from environment; swap for Vault/KMS in production.

## Setup

Requires **Python 3.10+** (3.11 recommended). Recreate `.venv` on each machine — do not copy virtualenv folders between systems.

```bash
cd service-app
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY from https://openrouter.ai/
```

Optional persistence and web login:

```bash
# DATABASE_URL=sqlite:///./data/service_app.db  # default when unset
# WEB_AUTH_PASSWORD=choose-a-strong-password    # protects /app/* routes
```

## Usage

Print sample catalog:

```bash
service-app-demo
```

Call OpenRouter (CLI):

```bash
service-app-demo --parse 'Showed up at Baker residence, swapped two GFCIs, 1.5 hours on site'
```

HTTP API (Phase 1a — after `pip install -e .`):

```bash
service-app-api
# In another terminal:
curl -s http://127.0.0.1:8090/health
curl -s -X POST http://127.0.0.1:8090/parse \
  -H 'Content-Type: application/json' \
  -d '{"transcript": "Baker residence, two GFCIs, 1.5 hours"}'
```

**Cloud Run** (project `kgs-service-app`): see [`docs/GCP_DEPLOY.md`](docs/GCP_DEPLOY.md). Deploys via GitHub Actions on push to `dev` / `main`.

From Python (`pip install -e .` so `service_app` is importable):

```python
from service_app.ingestion import parse_service_call
from service_app.catalog import lookup_item_price

parsed = parse_service_call("...")
price = lookup_item_price("gfci outlet")
```

The root [`app.py`](app.py) re-exports `parse_service_call`, `lookup_item_price`, and `PRICE_DATABASE` for quick scripts **after** editable install adds `service_app` to the path:

```bash
PYTHONPATH=src python app.py   # works without install; prefer pip install -e .
```

## GitHub repository

**https://github.com/kirtquist/service-app** — clone, branch, and push notes in [`docs/GITHUB_SETUP.md`](docs/GITHUB_SETUP.md).

---

## Docs

- [`docs/VISION.md`](docs/VISION.md) — product vision, workflows, QuickBooks direction, roadmap.
- [`docs/GCP_DEPLOY.md`](docs/GCP_DEPLOY.md) — Cloud Run deploy (`kgs-service-app`), GitHub Actions, Secret Manager.
- [`docs/WHATSAPP_SETUP.md`](docs/WHATSAPP_SETUP.md) — Twilio sandbox and Meta Cloud API webhook setup.
- [`docs/PHASE_1B.md`](docs/PHASE_1B.md) — web invoice list, edit, and approve.
- [`docs/SME_DEMO_PROMPTS.md`](docs/SME_DEMO_PROMPTS.md) — plumber-style test messages for demos.
- [`infra/README.md`](infra/README.md) — Pulumi stack for GCP foundation (recommended one-time setup).
- [`docs/API_KEYS.md`](docs/API_KEYS.md) — how keys are supplied now and where to plug a vault later.
- [`docs/FEATURE_OVERVIEW.md`](docs/FEATURE_OVERVIEW.md) — product/technical roadmap notes.

## License

MIT — see repository settings on GitHub.
