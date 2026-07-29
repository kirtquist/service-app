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

### Cloud Run (Secret Manager + deploy)

**Preferred — Pulumi** ([`infra/README.md`](../infra/README.md)):

```bash
cd infra
pulumi config set --secret intuitClientId "YOUR_DEVELOPMENT_CLIENT_ID"
pulumi config set --secret intuitClientSecret "YOUR_DEVELOPMENT_CLIENT_SECRET"
pulumi up
```

Creates/updates `INTUIT_CLIENT_ID` and `INTUIT_CLIENT_SECRET` in Secret Manager and grants the runtime service account access. If you created those secrets manually first, import them once (see infra README).

**Deploy wiring:** `.github/workflows/deploy-cloud-run.yml` mounts both secrets and sets `INTUIT_ENVIRONMENT=sandbox` on each deploy — manual `gcloud run update` is no longer required after merge.

**Manual fallback** (if not using Pulumi):

```bash
echo -n "YOUR_CLIENT_ID" | gcloud secrets versions add INTUIT_CLIENT_ID --data-file=- --project=kgs-service-app
echo -n "YOUR_CLIENT_SECRET" | gcloud secrets versions add INTUIT_CLIENT_SECRET --data-file=- --project=kgs-service-app
```

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

---

## 6. Troubleshooting

| Issue | Fix |
|-------|-----|
| Redirect URI mismatch | URI in Intuit portal must match `INTUIT_REDIRECT_URI` or `{PUBLIC_BASE_URL}/app/integrations/quickbooks/callback` exactly |
| Invalid OAuth state | Retry connect; state expires after 10 minutes |
| Connect works locally but not Cloud Run | Add Cloud Run callback URL to Intuit app; mount secrets on Cloud Run |
| 401 from QBO API | Token refresh failed — disconnect and reconnect |
| No items in QBO | Create at least one Service item in the sandbox company |
| Invoice has no lines | Add labor hours or parts before sending |
