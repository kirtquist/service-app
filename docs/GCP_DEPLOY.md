# Deploy API to GCP Cloud Run

Project: **`kgs-service-app`**  
Service: **`service-app-api`** (region **`us-west1`** — must match Pulumi `gcp:region` and workflow `REGION`)

GitHub Actions deploys on push to **`main`** or **`dev`** after tests pass.

---

## Architecture

| Component | Purpose |
|-----------|---------|
| **Pulumi** (`infra/`) | APIs, Artifact Registry, Secret Manager, IAM — [recommended setup](#option-a-pulumi-recommended) |
| **Artifact Registry** | Docker images (`us-west1-docker.pkg.dev/kgs-service-app/service-app/api`) |
| **Cloud Run** | Hosts FastAPI (`GET /health`, `POST /parse`) — deployed by GitHub Actions |
| **Secret Manager** | `openrouter-api-key`, `web-auth-password`, `twilio-auth-token` → Cloud Run env |
| **GitHub Actions** | Build image, push, deploy (`.github/workflows/deploy-cloud-run.yml`) |

Cloud Run injects **`PORT=8080`**. Local dev uses **8090** by default (`service-app-api`).

---

## Option A: Pulumi (recommended)

Avoid manual `gcloud` resource creation — use the Pulumi stack in [`infra/`](../infra/README.md).

```bash
cd infra
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

pulumi stack select prod   # or: pulumi stack init prod
pulumi config set --secret openrouterApiKey "sk-or-v1-YOUR_KEY"
pulumi config set --secret webAuthPassword "YOUR_STRONG_WEB_PASSWORD"
pulumi up
```

Add GitHub secret from Pulumi output:

```bash
pulumi stack output github_deploy_sa_key_json --show-secrets
# → paste into GitHub secret GCP_SA_KEY
```

Merge to **`dev`** or **`main`** to trigger the first Cloud Run deploy.

Full details: **[`infra/README.md`](../infra/README.md)**

---

## Option B: Manual `gcloud` setup

Use this if you prefer not to run Pulumi, or need to troubleshoot individual resources.

Install [gcloud CLI](https://cloud.google.com/sdk/docs/install) and authenticate:

```bash
gcloud auth login
gcloud config set project kgs-service-app
```

### Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com
```

### Artifact Registry

```bash
gcloud artifacts repositories create service-app \
  --repository-format=docker \
  --location=us-west1 \
  --description="Service App API images"
```

### OpenRouter secret

```bash
echo -n "YOUR_OPENROUTER_KEY" | gcloud secrets create openrouter-api-key \
  --data-file=- \
  --replication-policy=automatic
```

To update later:

```bash
echo -n "NEW_KEY" | gcloud secrets versions add openrouter-api-key --data-file=-
```

### Runtime service account (Cloud Run)

```bash
gcloud iam service-accounts create service-app-api \
  --display-name="Service App Cloud Run runtime"

gcloud secrets add-iam-policy-binding openrouter-api-key \
  --member="serviceAccount:service-app-api@kgs-service-app.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Deploy service account (GitHub Actions)

```bash
gcloud iam service-accounts create github-deploy \
  --display-name="GitHub Actions deploy"

gcloud projects add-iam-policy-binding kgs-service-app \
  --member="serviceAccount:github-deploy@kgs-service-app.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding kgs-service-app \
  --member="serviceAccount:github-deploy@kgs-service-app.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud iam service-accounts add-iam-policy-binding \
  service-app-api@kgs-service-app.iam.gserviceaccount.com \
  --member="serviceAccount:github-deploy@kgs-service-app.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

Create a JSON key for GitHub:

```bash
gcloud iam service-accounts keys create github-deploy-key.json \
  --iam-account=github-deploy@kgs-service-app.iam.gserviceaccount.com
```

---

## GitHub repository secret

In **https://github.com/kirtquist/service-app** → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|--------|
| **`GCP_SA_KEY`** | Full JSON from Pulumi output **or** `github-deploy-key.json` |

Delete any local key file after uploading.

---

## Deploy Cloud Run

Merge to **`dev`** or **`main`**, or run **Deploy API to Cloud Run** manually (Actions → workflow_dispatch).

After deploy:

```bash
gcloud run services describe service-app-api \
  --region us-west1 \
  --format 'value(status.url)'
```

### Smoke test

```bash
export SERVICE_URL="https://service-app-api-XXXX.us-west1.run.app"

curl -s "$SERVICE_URL/health"

curl -s -X POST "$SERVICE_URL/parse" \
  -H 'Content-Type: application/json' \
  -d '{"transcript": "Baker residence, replaced P-trap, 2 hours"}'
```

---

## Local Docker (optional)

```bash
docker build -t service-app-api:local .
docker run --rm -p 8090:8090 \
  -e PORT=8090 \
  -e OPENROUTER_API_KEY="sk-or-v1-..." \
  service-app-api:local
```

---

## Security notes (demo phase)

- **`--allow-unauthenticated`** is enabled so SMEs can hit `/health` and `/parse` without auth — fine for early demos.
- Before production: restrict `/parse` (API key, Cloud IAM, or Identity-Aware Proxy) and add rate limits.
- Never commit `.env`, Pulumi secrets, or GCP keys; use Secret Manager + GitHub encrypted secrets only.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Pulumi “already exists” | Import resources or delete duplicates — see [`infra/README.md`](../infra/README.md) |
| Deploy fails: secret not found | Run `pulumi up` or create `openrouter-api-key` manually |
| 503 on `/parse` | Check Cloud Run logs; verify secret binding and OpenRouter key |
| `Permission denied` on deploy | Verify `GCP_SA_KEY` and IAM roles on `github-deploy` SA |
| Wrong project | Confirm `kgs-service-app` in Pulumi config and workflow env |

Logs:

```bash
gcloud run services logs read service-app-api --region us-west1 --limit 50
```
