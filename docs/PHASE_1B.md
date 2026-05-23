# Phase 1b — Web invoice approval MVP

Browser UI for trade shop owners to **review, edit, and approve** invoices created from WhatsApp or pasted field notes.

**Live URL (Cloud Run):** `https://service-app-api-fozkmmaapq-uw.a.run.app/app/invoices`

---

## What it does

| Feature | Route |
|---------|--------|
| Invoice list (filter by status) | `GET /app/invoices` |
| Create from transcript | `GET/POST /app/invoices/new` |
| View / edit lines, labor, customer | `GET /app/invoices/{id}` |
| Approve | `POST /app/invoices/{id}/approve` |
| Change status | `POST /app/invoices/{id}/status` |

**Statuses:** `draft` → `pending_review` → `approved`

WhatsApp messages automatically create **`pending_review`** invoices and include a review link in the reply.

---

## Auth (single shop)

HTTP Basic auth — set on Cloud Run:

```bash
gcloud run services update service-app-api \
  --region us-west1 \
  --project kgs-service-app \
  --set-env-vars="WEB_AUTH_USERNAME=admin,WEB_AUTH_PASSWORD=YOUR_STRONG_PASSWORD"
```

If `WEB_AUTH_PASSWORD` is unset, the web UI is **open** (local dev only).

---

## Database

| Environment | `DATABASE_URL` |
|-------------|----------------|
| Local default | `sqlite:///./data/service_app.db` |
| Cloud Run (demo) | `sqlite:////tmp/service_app.db` |

Cloud Run SQLite is **ephemeral** — data survives restarts but not redeploys. For production, use Cloud SQL Postgres and set `DATABASE_URL` accordingly.

Tables are created automatically on startup (`create_all`).

---

## Local dev

```bash
cp .env.example .env
# Set OPENROUTER_API_KEY, optional WEB_AUTH_PASSWORD

pip install -e ".[dev]"
service-app-api

# Browser:
open http://127.0.0.1:8090/app/invoices
```

---

## End-to-end demo flow

1. Send a job note via **WhatsApp** to the Twilio sandbox.
2. Bot replies with summary + JSON + **review link**.
3. Open `/app/invoices` on your phone browser at home.
4. Fix line items → **Approve invoice**.

---

## Next (Phase 2)

- CSV / PDF export for QuickBooks
- Cloud SQL for durable storage
- Multi-tenant auth

See [`VISION.md`](VISION.md).
