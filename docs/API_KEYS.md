# API keys — OpenRouter and beyond

Service credentials (OpenRouter, future QuickBooks OAuth client secrets) belong in environment or a vault — **not** in the application database. See also [`VISION.md`](VISION.md) for product context.

## Local development

1. Copy [`.env.example`](../.env.example) to `.env` at the project root (gitignored).
2. Set **`OPENROUTER_API_KEY`** to a key from [OpenRouter](https://openrouter.ai/).
3. Optionally set **`OPENROUTER_HTTP_REFERER`** and **`OPENROUTER_X_TITLE`** for OpenRouter’s usage rankings.

[`pydantic-settings`](../src/service_app/settings.py) loads `.env` automatically when present.

## How it flows in code

- [`EnvSecretsProvider`](../src/service_app/secrets.py) implements [`SecretsProvider`](../src/service_app/secrets.py) and resolves `OPENROUTER_API_KEY` through [`Settings`](../src/service_app/settings.py).
- Replace the default provider via `service_app.secrets.set_secrets_provider(MyVaultProvider())` when you integrate HashiCorp Vault, AWS Secrets Manager, Doppler, etc.

## Continuous integration / production

Do **not** commit `.env`. Production secrets live in **GCP Secret Manager**, provisioned by Pulumi ([`infra/README.md`](../infra/README.md)):

| Pulumi config | Secret Manager ID | Cloud Run env |
|---------------|-------------------|---------------|
| `openrouterApiKey` (secret) | `openrouter-api-key` | `OPENROUTER_API_KEY` |
| `webAuthPassword` (secret) | `web-auth-password` | `WEB_AUTH_PASSWORD` |
| (auto) | `database-url` | `DATABASE_URL` |

GitHub Actions (`.github/workflows/deploy-cloud-run.yml`) mounts these on each deploy. Set values with:

```bash
cd infra && pulumi config set --secret webAuthPassword "..."
pulumi up
```

Twilio auth token (`twilio-auth-token`) may be created manually or added to Pulumi later.

For GitHub Actions deploy auth, use repository secret **`GCP_SA_KEY`** (Pulumi output).

## Storing keys in the application database

The MVP avoids persisting raw API keys in SQLite/Postgres. Service credentials belong in platform secret stores.

If you must support per-tenant BYOK flows later:

- Prefer encrypting-at-rest **before** inserting (envelope encryption with KMS), or defer to OAuth-style flows where keys never hit your disks.
