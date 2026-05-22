# Deploy API to GCP Cloud Run

Project: **`kgs-service-app`**  
Service: **`service-app-api`** (region **`us-central1`**)

GitHub Actions deploys on push to **`main`** or **`dev`** after tests pass. One-time GCP and GitHub setup below.

---

## Architecture

| Component | Purpose |
|-----------|---------|
| **Artifact Registry** | Docker images (`us-central1-docker.pkg.dev/kgs-service-app/service-app/api`) |
| **Cloud Run** | Hosts FastAPI (`GET /health`, `POST /parse`) |
| **Secret Manager** | `openrouter-api-key` → env `OPENROUTER_API_KEY` on Cloud Run |
| **GitHub Actions** | Build image, push, deploy (`.github/workflows/deploy-cloud-run.yml`) |

Cloud Run injects **`PORT=8080`**. Local dev uses **8090** by default (`service-app-api`).

---

## 1. One-time GCP setup

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
  --location=us-central1 \
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

Create a JSON key for GitHub (store securely; rotate periodically):

```bash
gcloud iam service-accounts keys create github-deploy-key.json \
  --iam-account=github-deploy@kgs-service-app.iam.gserviceaccount.com
```

---

## 2. GitHub repository secret

In **https://github.com/kirtquist/service-app** → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|--------|
| **`GCP_SA_KEY`** | Full contents of `github-deploy-key.json` |

Delete the local key file after uploading:

```bash
rm github-deploy-key.json
```

---

## 3. Deploy

Merge to **`dev`** or **`main`**, or run **Deploy API to Cloud Run** manually (Actions → workflow_dispatch).

After deploy, get the URL:

```bash
gcloud run services describe service-app-api \
  --region us-central1 \
  --format 'value(status.url)'
```

### Smoke test

```bash
export SERVICE_URL="https://service-app-api-XXXX.us-central1.run.app"

curl -s "$SERVICE_URL/health"

curl -s -X POST "$SERVICE_URL/parse" \
  -H 'Content-Type: application/json' \
  -d '{"transcript": "Baker residence, replaced P-trap, 2 hours"}'
```

---

## 4. Local Docker (optional)

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
- Never commit `.env` or GCP keys; use Secret Manager + GitHub encrypted secrets only.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Deploy fails: secret not found | Create `openrouter-api-key` in Secret Manager |
| 503 on `/parse` | Check Cloud Run logs; verify secret binding and OpenRouter key |
| `Permission denied` on deploy | Verify `GCP_SA_KEY` and IAM roles on `github-deploy` SA |
| Wrong project | Workflow uses `kgs-service-app` — confirm `gcloud config get-value project` |

Logs:

```bash
gcloud run services logs read service-app-api --region us-central1 --limit 50
```
