# Pulumi infrastructure for GCP (`kgs-service-app`).

Provisions **long-lived** resources with [Pulumi](https://www.pulumi.com/) (Python). **Cloud Run image deploys** remain in GitHub Actions (`.github/workflows/deploy-cloud-run.yml`) on each push to `dev` / `main`.

## What Pulumi creates

| Resource | Name / ID |
|----------|-----------|
| Enabled APIs | Run, Artifact Registry, Secret Manager, IAM, Cloud Build, **Compute** (provider region lookup) |
| Artifact Registry | `service-app` (Docker, `us-central1`) |
| Secret Manager | `openrouter-api-key` |
| Runtime SA | `service-app-api@kgs-service-app.iam.gserviceaccount.com` |
| GitHub deploy SA | `github-deploy@kgs-service-app.iam.gserviceaccount.com` |
| IAM | Runtime SA → read secret; GitHub SA → deploy + push images |

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

From repo root:

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
# gcp:project and gcp:region are already in Pulumi.prod.yaml

pulumi preview
pulumi up
```

If `pulumi stack init prod` says the stack already exists, use `pulumi stack select prod` instead.

Stack config for `prod` is checked in as `Pulumi.prod.yaml` (project + region only — **no secrets in git**).

## Wire GitHub Actions

Export the deploy service account key (shown once; treat as sensitive):

```bash
pulumi stack output github_deploy_sa_key_json --show-secrets
```

Copy the full JSON into GitHub → **Settings → Secrets → Actions** → **`GCP_SA_KEY`**.

Then merge to **`dev`** or **`main`** (or run the deploy workflow manually). GitHub Actions builds the Docker image, pushes to Artifact Registry, and deploys Cloud Run service **`service-app-api`**.

## Useful outputs

```bash
pulumi stack output project_id
pulumi stack output artifact_registry_repository
pulumi stack output runtime_service_account_email
```

## Updating the OpenRouter key

```bash
pulumi config set --secret openrouterApiKey "NEW_KEY"
pulumi up   # creates a new secret version
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
