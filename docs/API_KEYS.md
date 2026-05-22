# API keys — OpenRouter and beyond

## Local development

1. Copy [`.env.example`](../.env.example) to `.env` at the project root (gitignored).
2. Set **`OPENROUTER_API_KEY`** to a key from [OpenRouter](https://openrouter.ai/).
3. Optionally set **`OPENROUTER_HTTP_REFERER`** and **`OPENROUTER_X_TITLE`** for OpenRouter’s usage rankings.

[`pydantic-settings`](../src/service_app/settings.py) loads `.env` automatically when present.

## How it flows in code

- [`EnvSecretsProvider`](../src/service_app/secrets.py) implements [`SecretsProvider`](../src/service_app/secrets.py) and resolves `OPENROUTER_API_KEY` through [`Settings`](../src/service_app/settings.py).
- Replace the default provider via `service_app.secrets.set_secrets_provider(MyVaultProvider())` when you integrate HashiCorp Vault, AWS Secrets Manager, Doppler, etc.

## Continuous integration / production

Do **not** commit `.env`. On GitHub Actions, use **encrypted repository secrets**:

- `OPENROUTER_API_KEY` (and optionally the referer/title vars)

Inject them as environment variables into the workflow job prior to tests or deployments.

## Storing keys in the application database

The MVP avoids persisting raw API keys in SQLite/Postgres. Service credentials belong in platform secret stores.

If you must support per-tenant BYOK flows later:

- Prefer encrypting-at-rest **before** inserting (envelope encryption with KMS), or defer to OAuth-style flows where keys never hit your disks.
