# service-app

MVP scaffolding for a **field-service** style app aimed first at trades such as plumbing. The bundled **price catalog mock data skews electrician** until you swap SKUs toward pipes, fittings, and fixtures.

**Product direction:** web-based invoice review and approval at home, with future QuickBooks sync — see [`docs/VISION.md`](docs/VISION.md). The CLI is for development and testing only.

## Features (current)

- **OpenRouter**: Chat Completions via the OpenAI Python SDK pointing at OpenRouter (`OPENROUTER_API_KEY`).
- **Structured parsing**: Rough technician transcripts → JSON fields (customer, parts, labor hours).
- **Secrets hook**: [`EnvSecretsProvider`](src/service_app/secrets.py) reads from environment; swap for Vault/KMS in production.
- **Database stub**: SQLAlchemy `Base` + session factory wired for when you add `DATABASE_URL`.

## Setup

Requires **Python 3.10+** (3.11 recommended). Recreate `.venv` on each machine — do not copy virtualenv folders between systems.

```bash
cd service-app
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY from https://openrouter.ai/
```

Optional: enable SQLite persistence later:

```bash
# mkdir -p data
# DATABASE_URL=sqlite:///./data/service_app.db — then call configure_engine from your app bootstrap
```

## Usage

Print sample catalog:

```bash
service-app-demo
```

Parse a technician log line via OpenRouter (pass a quoted **transcript** — a plain-English field note):

```bash
service-app-demo --parse 'Showed up at Baker residence, swapped two GFCIs, 1.5 hours on site'
```

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
- [`docs/API_KEYS.md`](docs/API_KEYS.md) — how keys are supplied now and where to plug a vault later.
- [`docs/FEATURE_OVERVIEW.md`](docs/FEATURE_OVERVIEW.md) — product/technical roadmap notes.

## License

MIT — see repository settings on GitHub.
