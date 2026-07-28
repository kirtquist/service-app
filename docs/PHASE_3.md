# Phase 3 — QuickBooks Online integration

OAuth connect framework for pushing approved invoices to QuickBooks Online (QBO). Invoice create/sync mapping is the next build step after connect works.

**Related:** [`VISION.md`](VISION.md) · [`API_KEYS.md`](API_KEYS.md) · [`PHASE_2.md`](PHASE_2.md)

---

## What exists today

| Piece | Status |
|-------|--------|
| Intuit OAuth (connect / callback / disconnect) | ✅ |
| Token storage in Postgres/SQLite (`quickbooks_connections`) | ✅ |
| Access token refresh | ✅ |
| QBO API client scaffold | ✅ |
| Web UI at `/app/integrations/quickbooks` | ✅ |
| Push approved invoice to QBO | 🔜 next |

---

## 1. Intuit Developer app setup

1. [developer.intuit.com](https://developer.intuit.com/) → your app → **Keys & credentials**
2. Copy **Development** Client ID and Client Secret (sandbox).
3. Under **Redirect URIs**, add **exactly** (no trailing slash unless you register one):

**Local:**

```
http://127.0.0.1:8090/app/integrations/quickbooks/callback
```

**Cloud Run:**

```
https://service-app-api-fozkmmaapq-uw.a.run.app/app/integrations/quickbooks/callback
```

4. Scopes: **`com.intuit.quickbooks.accounting`** (included in the connect URL).

---

## 2. Where to store credentials

| Secret | Local (`.env`) | Production (GCP Secret Manager) | Database |
|--------|----------------|----------------------------------|----------|
| Client ID | `INTUIT_CLIENT_ID` | `intuit-client-id` → env | ❌ never |
| Client Secret | `INTUIT_CLIENT_SECRET` | `intuit-client-secret` → env | ❌ never |
| OAuth access/refresh tokens | — | — | ✅ `quickbooks_connections` |

**App credentials** (client ID/secret) follow the same pattern as OpenRouter — environment or Secret Manager, not committed to git.

**OAuth tokens** (after a shop owner connects) are stored in the application database per connected QBO company (`realm_id`). That is expected for multi-step OAuth; protect the database like any credential store.

### Local `.env`

```bash
INTUIT_CLIENT_ID=your-development-client-id
INTUIT_CLIENT_SECRET=your-development-client-secret
INTUIT_ENVIRONMENT=sandbox
INTUIT_REDIRECT_URI=http://127.0.0.1:8090/app/integrations/quickbooks/callback
```

If `INTUIT_REDIRECT_URI` is omitted, the app builds it from `PUBLIC_BASE_URL` + `/app/integrations/quickbooks/callback`.

### Cloud Run (Secret Manager)

Create secrets once:

```bash
echo -n "YOUR_CLIENT_ID" | gcloud secrets create intuit-client-id \
  --data-file=- --project=kgs-service-app --replication-policy=automatic

echo -n "YOUR_CLIENT_SECRET" | gcloud secrets create intuit-client-secret \
  --data-file=- --project=kgs-service-app --replication-policy=automatic

gcloud secrets add-iam-policy-binding intuit-client-id \
  --member="serviceAccount:service-app-api@kgs-service-app.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=kgs-service-app

gcloud secrets add-iam-policy-binding intuit-client-secret \
  --member="serviceAccount:service-app-api@kgs-service-app.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=kgs-service-app
```

Mount on Cloud Run:

```bash
gcloud run services update service-app-api \
  --region us-west1 \
  --project kgs-service-app \
  --set-secrets="INTUIT_CLIENT_ID=intuit-client-id:latest,INTUIT_CLIENT_SECRET=intuit-client-secret:latest" \
  --update-env-vars="INTUIT_ENVIRONMENT=sandbox,PUBLIC_BASE_URL=https://service-app-api-fozkmmaapq-uw.a.run.app"
```

Also add both secrets to `.github/workflows/deploy-cloud-run.yml` when you want deploys to keep them mounted.

---

## 3. Connect flow (test)

```bash
pip install -e ".[dev]"
service-app-api
```

1. Open `http://127.0.0.1:8090/app/integrations/quickbooks` (sign in with web auth).
2. Click **Connect QuickBooks**.
3. Sign in to Intuit and authorize the sandbox company.
4. You should land back on the settings page with **Connected** and the company name.

Disconnect clears tokens from the database only (Intuit revoke can be added later).

---

## 4. Code layout

```
src/service_app/qbo/
  config.py    # sandbox/production API base URLs
  oauth.py     # authorization URL, code exchange, refresh
  service.py   # connection CRUD + token refresh
  client.py    # QBO REST client
  sync.py      # invoice push (stub)
src/service_app/web/qbo_routes.py
src/service_app/web/templates/quickbooks_settings.html
```

Invoice sync fields on `invoices`: `qbo_external_id`, `qbo_sync_status`, `qbo_synced_at`.

---

## 5. Next implementation step

- Map approved `Invoice` + lines → QBO Invoice API payload (generic Parts/Labor items OK for MVP).
- Add **Send to QuickBooks** on approved invoice detail page.
- Handle duplicate sync (idempotent on `qbo_external_id`).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Redirect URI mismatch | URI in Intuit portal must match `INTUIT_REDIRECT_URI` or `{PUBLIC_BASE_URL}/app/integrations/quickbooks/callback` exactly |
| Invalid OAuth state | Retry connect; state expires after 10 minutes |
| Connect works locally but not Cloud Run | Add Cloud Run callback URL to Intuit app; mount secrets on Cloud Run |
| 401 from QBO API | Token refresh failed — disconnect and reconnect |
