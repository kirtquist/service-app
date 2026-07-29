# Pulumi infrastructure for GCP (`kgs-service-app`).

Provisions **long-lived** resources with [Pulumi](https://www.pulumi.com/) (Python). **Cloud Run image deploys** remain in GitHub Actions (`.github/workflows/deploy-cloud-run.yml`) on each push to `dev` / `main`.

## What Pulumi creates

| Resource | Name / ID |
|----------|-----------|
| Enabled APIs | Run, Artifact Registry, Secret Manager, IAM, Cloud Build, **SQL Admin**, Compute |
| Artifact Registry | `service-app` (Docker, region from `Pulumi.prod.yaml`, e.g. `us-west1`) |
| Secret Manager | `openrouter-api-key`, `web-auth-password`, `database-url`, `INTUIT_CLIENT_ID`, `INTUIT_CLIENT_SECRET` (when configured) |
| Cloud SQL | PostgreSQL 15 instance `service-app-db`, database `service_app` |
| Runtime SA | `service-app-api@kgs-service-app.iam.gserviceaccount.com` |
| GitHub deploy SA | `github-deploy@kgs-service-app.iam.gserviceaccount.com` |
| IAM | Runtime SA → read secrets + Cloud SQL client; GitHub SA → deploy + push images |

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/install/)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) authenticated with permission to manage `kgs-service-app`
- Python 3.10+

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project kgs-service-app
pulumi login   # pulumi.com free account, or configure GCS self-hosted backend
```

## First-time setup

`Pulumi.prod.yaml` in git is **stack config only** — it does not create the stack. You must **`init`** once before **`select`**.

From repo root :

```bash
cd infra
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# First time only — creates the prod stack (registers with pulumi.com backend)
pulumi stack init prod

# Later sessions
# pulumi stack select prod

pulumi config set --secret openrouterApiKey "sk-or-v1-YOUR_KEY"
pulumi config set --secret webAuthPassword "YOUR_STRONG_WEB_PASSWORD"
pulumi config set --secret intuitClientId "YOUR_INTUIT_DEVELOPMENT_CLIENT_ID"
pulumi config set --secret intuitClientSecret "YOUR_INTUIT_DEVELOPMENT_CLIENT_SECRET"
# Optional — default is admin (must match deploy workflow WEB_AUTH_USERNAME)
pulumi config set webAuthUsername admin
# gcp:project and gcp:region are already in Pulumi.prod.yaml

pulumi preview
pulumi up
```

If `pulumi stack init prod` says the stack already exists, use `pulumi stack select prod` instead.

Stack config for `prod` is checked in as `Pulumi.prod.yaml` (project + region only — **no secrets in git**).

## Wire GitHub Actions

**Required before deploy will work:** add GitHub Actions secret **`GCP_SA_KEY`**.

Export the deploy service account key after `pulumi up` (treat as sensitive):

```bash
pulumi stack output github_deploy_sa_key_json --show-secrets
```

Copy the **entire JSON object** (starts with `{`, ends with `}`) into:

**GitHub → kirtquist/service-app → Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|--------|
| `GCP_SA_KEY` | Full JSON from Pulumi output above |

Then merge to **`dev`** or **`main`**, or re-run **Deploy API to Cloud Run** from the Actions tab.

## Updating secrets

**OpenRouter key:**

```bash
pulumi config set --secret openrouterApiKey "NEW_KEY"
pulumi up   # creates a new secret version
```

**Web UI password** (HTTP Basic auth for `/app/*`):

```bash
pulumi config set --secret webAuthPassword "NEW_PASSWORD"
pulumi up
```

Username is plain config (`webAuthUsername`, default `admin`). After changing it, update `WEB_AUTH_USERNAME` in `.github/workflows/deploy-cloud-run.yml` to match, then redeploy.

**QuickBooks OAuth (Development keys from Intuit):**

```bash
pulumi config set --secret intuitClientId "YOUR_DEVELOPMENT_CLIENT_ID"
pulumi config set --secret intuitClientSecret "YOUR_DEVELOPMENT_CLIENT_SECRET"
pulumi up   # creates secret versions in INTUIT_CLIENT_ID / INTUIT_CLIENT_SECRET
```

If you already created those secrets manually in GCP, **import** them once before `pulumi up`:

```bash
pulumi import gcp:secretmanager/secret:Secret intuit-client-id projects/kgs-service-app/secrets/INTUIT_CLIENT_ID
pulumi import gcp:secretmanager/secret:Secret intuit-client-secret projects/kgs-service-app/secrets/INTUIT_CLIENT_SECRET
```

Then set config and run `pulumi up` to manage versions and IAM. A healthy stack shows **`pulumi preview` → N unchanged** when fully synced.

**Import warnings:** `replication` validation warnings during import are normal — choose **yes**. They usually clear once the secret is in Pulumi state.

**Verify after setup:**

```bash
pulumi preview   # expect: N unchanged when synced
```

## Cloud Run env vars — Pulumi vs GitHub Actions

| Layer | Owns today | Examples |
|-------|------------|----------|
| **Pulumi** | Secret Manager resources, values, IAM, Cloud SQL, service accounts | `openrouter-api-key`, `INTUIT_CLIENT_ID` |
| **GitHub Actions deploy** | Container image + which secrets/env vars Cloud Run mounts | `PUBLIC_BASE_URL`, secret mounts, `INTUIT_ENVIRONMENT=sandbox` |

**Could Pulumi manage all Cloud Run environment variables?** Yes — `gcp.cloudrunv2.Service` can define env vars, secret refs, scaling, and the service shell. This repo **intentionally splits** responsibilities: Pulumi provisions long-lived infra; GitHub Actions deploys a new image on every push to `dev`/`main`.

Moving everything to Pulumi would mean either (a) Pulumi also deploys the container image on each release, or (b) two tools updating the same Cloud Run service (easy to fight over config). The current split is deliberate: **Pulumi = secrets + platform**, **CI = app deploy wiring**.

Non-secret deploy-time settings (`PUBLIC_BASE_URL`, `INTUIT_ENVIRONMENT`) stay in the workflow because they change with releases and are not sensitive.

## Useful outputs

```bash
pulumi stack output project_id
pulumi stack output artifact_registry_repository
pulumi stack output runtime_service_account_email
pulumi stack output web_auth_username
pulumi stack output web_auth_password_secret_id
pulumi stack output cloud_sql_connection_name
pulumi stack output database_url_secret_id
pulumi stack output intuit_client_id_secret_id
pulumi stack output intuit_client_secret_secret_id
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Compute Engine API` warning on preview | Fixed in stack — `compute.googleapis.com` is enabled by Pulumi; wait a few minutes after first enable |
| `SecretIAMMember` AttributeError | Use pulumi-gcp 8+ — resource is `SecretIamMember` (fixed in repo) |
| Pulumi “already exists” (GCP) | Import resources or delete duplicates — see below |

If you ran manual `gcloud` steps from [`GCP_DEPLOY.md`](../docs/GCP_DEPLOY.md) first, `pulumi up` may fail with “already exists”. Options:

1. **Fresh project** — delete conflicting resources in GCP console, then `pulumi up`.
2. **Import** — `pulumi import` each existing resource (see Pulumi GCP docs).
3. **Skip Pulumi** — continue with manual setup in `GCP_DEPLOY.md`.

## Destroy (careful)

```bash
pulumi destroy
```

Does not remove Cloud Run revisions created by GitHub Actions (manage those in GCP console or `gcloud run services delete`).
