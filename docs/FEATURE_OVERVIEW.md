# Service App — MVP feature overview

## Product intent

- **Primary audience**: small trade shops starting with plumbing; the repo currently ships **electrician-flavored catalog entries** only as placeholders.
- **Near-term workflows**:
  - Capture technician narration (speech-to-text upstream, not bundled here yet).
  - Parse into structured jobs: customer, labor time, billable SKUs / line items.
  - Price lookups against internal catalogs loaded from eventual database tables.

## Technical building blocks

| Area | Current state | Next steps |
|------|----------------|------------|
| LLM ingestion | [`parse_service_call`](../src/service_app/ingestion.py) via OpenRouter | Add validation with Pydantic models; wire STT vendor |
| Catalog | Dict in [`catalog.py`](../src/service_app/catalog.py) | Migrate to DB tables (`parts`, regional price lists); seed plumber SKUs |
| Secrets | Env + `.env` via [`SecretsProvider`](../src/service_app/secrets.py) | Production vault + CI secrets documentation (see `docs/API_KEYS.md`) |
| Database | Declarative `Base` + session factory stubs | Models for `customer`, `job`, `invoice_line`; Alembic migrations |

## OpenRouter specifics

[`llm.py`](../src/service_app/llm.py) configures `OpenAI` client with OpenRouter base URL and optional referrer headers consistent with provider guidance ([OpenRouter docs](https://openrouter.ai/docs)).

## Naming / roadmap

Rename trade-specific modules (`catalog.py`) or split catalogs by vertical when onboarding multiple trades. Until then document which strings are electrically biased so plumbing pilots can refactor quickly.
