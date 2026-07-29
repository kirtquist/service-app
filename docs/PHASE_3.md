# Phase 3 — QuickBooks Online integration

OAuth connect and one-click invoice sync to QuickBooks Online (QBO).

**Related:** [`VISION.md`](VISION.md) · [`API_KEYS.md`](API_KEYS.md) · [`PHASE_2.md`](PHASE_2.md)

---

## What exists today

| Piece | Status |
|-------|--------|
| Intuit OAuth (connect / callback / disconnect) | ✅ |
| Token storage in Postgres/SQLite (`quickbooks_connections`) | ✅ |
| Access token refresh | ✅ |
| QBO API client | ✅ |
| Web UI at `/app/integrations/quickbooks` | ✅ |
| Push approved invoice to QBO | ✅ |
| **Send to QuickBooks** on approved invoice detail | ✅ |

---

## 1. Intuit Developer app setup

1. [developer.intuit.com](https://developer.intuit.com/) → your app → **Keys & credentials**
2. Copy **Development** Client ID and Client Secret (sandbox).
3. Under **Redirect URIs**, add **exactly** (no trailing slash unless you register one):

**Local** (Intuit portal accepts `localhost`; use it consistently in the browser):

```
http://localhost:8090/app/integrations/quickbooks/callback
```

**Cloud Run** (must match `PUBLIC_BASE_URL` in `.github/workflows/deploy-cloud-run.yml`):

```
https://service-app-api-fozkmmaapq-uw.a.run.app/app/integrations/quickbooks/callback
```

Cloud Run also exposes an alternate hostname (`https://service-app-api-908743017998.us-west1.run.app`). Both reach the same service, but OAuth uses **`PUBLIC_BASE_URL`** (`fozkmmaapq-uw`) when building the redirect URI — register **that** callback in Intuit, not only the alias URL.

4. Scopes: **`com.intuit.quickbooks.accounting`** (included in the connect URL).

---

## 2. Where to store credentials

| Secret | Local (`.env`) | Production (GCP Secret Manager) | Cloud Run env | Database |
|--------|----------------|----------------------------------|---------------|----------|
| Client ID | `INTUIT_CLIENT_ID` | `INTUIT_CLIENT_ID` | `INTUIT_CLIENT_ID` | ❌ never |
| Client Secret | `INTUIT_CLIENT_SECRET` | `INTUIT_CLIENT_SECRET` | `INTUIT_CLIENT_SECRET` | ❌ never |
| Environment | `INTUIT_ENVIRONMENT` | — (set in deploy workflow) | `INTUIT_ENVIRONMENT=sandbox` | — |
| OAuth access/refresh tokens | — | — | — | ✅ `quickbooks_connections` |

**App credentials** (client ID/secret) follow the same pattern as OpenRouter — environment or Secret Manager, not committed to git.

**OAuth tokens** (after a shop owner connects) are stored in the application database per connected QBO company (`realm_id`). That is expected for multi-step OAuth; protect the database like any credential store.

### Local `.env`

```bash
INTUIT_CLIENT_ID=your-development-client-id
INTUIT_CLIENT_SECRET=your-development-client-secret
INTUIT_ENVIRONMENT=sandbox
INTUIT_REDIRECT_URI=http://localhost:8090/app/integrations/quickbooks/callback
```

If `INTUIT_REDIRECT_URI` is omitted, the app builds it from `PUBLIC_BASE_URL` + `/app/integrations/quickbooks/callback`.

### Production architecture (secrets + deploy)

```
Intuit Developer (Development keys)
        ↓
Pulumi stack config (encrypted) ──pulumi up──► Secret Manager
  intuitClientId                                  INTUIT_CLIENT_ID
  intuitClientSecret                              INTUIT_CLIENT_SECRET
        ↓
GitHub Actions deploy ──mounts secrets──► Cloud Run env vars
        ↓
App OAuth + invoice sync
```

| Layer | Responsibility |
|-------|----------------|
| **Pulumi** | Create secrets, push values, grant runtime SA `secretAccessor` — [`infra/README.md`](../infra/README.md) |
| **Secret Manager** | Encrypted storage at rest (`INTUIT_CLIENT_ID`, `INTUIT_CLIENT_SECRET`) |
| **`.github/workflows/deploy-cloud-run.yml`** | Mount secrets + set `INTUIT_ENVIRONMENT=sandbox`, `PUBLIC_BASE_URL` on every deploy |
| **Cloud Run** | Injects secrets as env vars; app reads via [`settings.py`](../src/service_app/settings.py) |

**Do not** commit client ID/secret to git. OAuth tokens after connect live in Postgres (`quickbooks_connections`), not Secret Manager.

### Cloud Run (Secret Manager + deploy)

**Preferred — Pulumi** ([`infra/README.md`](../infra/README.md)):

```bash
cd infra
pulumi stack select prod
pulumi config set --secret intuitClientId "YOUR_DEVELOPMENT_CLIENT_ID"
pulumi config set --secret intuitClientSecret "YOUR_DEVELOPMENT_CLIENT_SECRET"
pulumi up
```

Creates/updates `INTUIT_CLIENT_ID` and `INTUIT_CLIENT_SECRET` in Secret Manager and grants the runtime service account access.

**If secrets already exist in GCP** (manual setup), import once before `pulumi up`:

```bash
pulumi import gcp:secretmanager/secret:Secret intuit-client-id projects/kgs-service-app/secrets/INTUIT_CLIENT_ID
pulumi import gcp:secretmanager/secret:Secret intuit-client-secret projects/kgs-service-app/secrets/INTUIT_CLIENT_SECRET
```

Import may show **replication** warnings — choose **yes**; they are normal. After import + config + `pulumi up`, `pulumi preview` should show **unchanged** when synced.

**Deploy wiring** (already in repo): `.github/workflows/deploy-cloud-run.yml` mounts:

```
INTUIT_CLIENT_ID=INTUIT_CLIENT_ID:latest
INTUIT_CLIENT_SECRET=INTUIT_CLIENT_SECRET:latest
```

…and sets `INTUIT_ENVIRONMENT=sandbox`. Without this, a code deploy would **drop** manually added secret mounts.

**Rotate keys:**

```bash
pulumi config set --secret intuitClientId "NEW_ID"
pulumi config set --secret intuitClientSecret "NEW_SECRET"
pulumi up
```

New Cloud Run instances pick up `:latest` automatically; no manual `gcloud run update` needed.

**Manual fallback** (if not using Pulumi):

```bash
echo -n "YOUR_CLIENT_ID" | gcloud secrets versions add INTUIT_CLIENT_ID --data-file=- --project=kgs-service-app
echo -n "YOUR_CLIENT_SECRET" | gcloud secrets versions add INTUIT_CLIENT_SECRET --data-file=- --project=kgs-service-app
```

---

## 3. Connect flow

### Local

```bash
pip install -e ".[dev]"
service-app-api
```

1. Open **`http://localhost:8090/app/integrations/quickbooks`** (sign in with web auth if `WEB_AUTH_PASSWORD` is set).
2. Confirm the **Redirect URI** shown on the page matches what you registered in Intuit.
3. Click **Connect QuickBooks** → Intuit sandbox login → authorize.
4. Land back on settings with **Connected** and the company name.

### Cloud Run

1. Use the **canonical URL** for the whole flow: **`https://service-app-api-fozkmmaapq-uw.a.run.app`**
2. Sign in with HTTP Basic auth: username **`admin`**, password from Pulumi / Secret Manager `web-auth-password` (not your local `.env`).
3. Open `/app/integrations/quickbooks` → **Connect QuickBooks**.
4. After Intuit redirects back, the browser may prompt for **Basic auth again** on the `fozkmmaapq-uw` hostname (different from the `908743017998` alias — credentials are not shared between hostnames).

Disconnect clears tokens from the database only (Intuit revoke can be added later).

---

## 4. Code layout

```
src/service_app/qbo/
  config.py           # sandbox/production API base URLs
  oauth.py            # authorization URL, code exchange, refresh
  service.py          # connection CRUD + token refresh
  client.py           # QBO REST client
  invoice_mapping.py  # Invoice → QBO payload, customer/item lookup
  sync.py             # push approved invoices
src/service_app/web/qbo_routes.py
src/service_app/web/templates/quickbooks_settings.html
```

Invoice sync fields on `invoices`: `qbo_external_id`, `qbo_sync_status`, `qbo_synced_at`.

---

## 5. Send invoice to QuickBooks

1. Connect sandbox company at `/app/integrations/quickbooks`.
2. Approve an invoice on its detail page.
3. Click **Send to QuickBooks** in the QuickBooks Online section.
4. On success, the page shows the QBO invoice Id and sync timestamp.
5. Re-sending is idempotent — if `qbo_external_id` is already set, no duplicate is created.

**Mapping (MVP):**

- Customer: find by `DisplayName` or create in QBO.
- Line items: labor (if hours > 0) and each parts line as `SalesItemLineDetail` rows.
- Uses the first Service item in QBO (or any item if none); descriptions carry part/labor text.
- `DocNumber` = `INV-0001` style from local invoice id.

**Line items (MVP limitation):** QBO receives generic Service item rows; part names appear in **Description**, not as mapped inventory SKUs. Catalog mapping is a future phase.

---

## 6. Database notes

- Invoice sync columns: `qbo_external_id`, `qbo_sync_status`, `qbo_synced_at`.
- Existing SQLite/Postgres databases created before Phase 3 get columns added automatically on startup ([`bootstrap.py`](../src/service_app/db/bootstrap.py) `apply_schema_patches`).

---

## 7. Troubleshooting

| Issue | Fix |
|-------|-----|
| Redirect URI mismatch | URI in Intuit portal must match the **Redirect URI** on the QuickBooks settings page exactly (check `PUBLIC_BASE_URL` / `INTUIT_REDIRECT_URI`) |
| Registered alias URL only | OAuth uses `fozkmmaapq-uw` hostname — register that callback, not only `908743017998.us-west1.run.app` |
| Invalid OAuth state | Retry connect; state expires after 10 minutes |
| `invalid_client` on connect | **Development** Client ID + Secret must match; Cloud Run values come from Secret Manager (via Pulumi), not local `.env`. Use `echo -n` when adding secret versions |
| HTTP Basic auth clears password | Wrong password for Cloud Run (`web-auth-password` secret); or signing in on alias URL then OAuth lands on `fozkmmaapq-uw` |
| Connect works locally but not Cloud Run | Register Cloud Run callback in Intuit; verify secrets mounted (deploy workflow); check `INTUIT_ENVIRONMENT=sandbox` |
| 401 from QBO API | Token refresh failed — disconnect and reconnect |
| 500 on `/app/invoices` (local) | Stale DB missing QBO columns — restart app (schema patch runs on startup) |
| No items in QBO | Create at least one Service item in the sandbox company |
| Invoice has no lines | Add labor hours or parts before sending |
| Deploy dropped QBO secrets | Ensure `INTUIT_*` lines are in `deploy-cloud-run.yml` |
