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
| Log out | `GET /app/logout` → `GET /app/logged-out` |

**Statuses:** `draft` → `pending_review` → `approved`

WhatsApp messages automatically create **`pending_review`** invoices and include a review link in the reply.

---

## Workflow

| Stage | What happens | Pricing |
|-------|----------------|---------|
| **Field** | One WhatsApp message or paste at `/app/invoices/new` per job close-out | AI parse + catalog lookup for recognized parts |
| **Home** | Review invoice, edit lines/labor, **add missing parts**, approve | Manual **Add line** — enter unit price yourself (no auto lookup) |

If the tech forgot fittings, the owner adds them on the invoice detail page before approving. A future **“add from note”** feature (parse a short list into the invoice) is documented for SME validation — see [`SME_INTERVIEW.md`](SME_INTERVIEW.md).

---

## Auth (single shop)

HTTP Basic auth protects `/app/*`. Credentials are managed in **Pulumi** → GCP Secret Manager:

```bash
cd infra
pulumi stack select prod
pulumi config set --secret webAuthPassword "YOUR_STRONG_PASSWORD"
pulumi up
```

- **Username:** `pulumi config get webAuthUsername` (default `admin`) — synced to Cloud Run as `WEB_AUTH_USERNAME` via GitHub Actions deploy.
- **Password:** Secret Manager `web-auth-password` → Cloud Run env `WEB_AUTH_PASSWORD`.

If `webAuthPassword` is not set in Pulumi, the web UI remains open (dev only).

After `pulumi up`, push to `dev`/`main` (or re-run the deploy workflow) so Cloud Run mounts the secret.

**Log out:** Use **Log out** in the header. HTTP Basic auth has no server session — logout clears cached browser credentials and shows a confirmation page.

---

## Database

| Environment | `DATABASE_URL` |
|-------------|----------------|
| Local default | `sqlite:///./data/service_app.db` |
| Production | PostgreSQL on **Cloud SQL** — Pulumi secret `database-url` |

Cloud Run connects via the Cloud SQL Auth proxy (`--add-cloudsql-instances`). See [`PHASE_2.md`](PHASE_2.md).

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

See [`PHASE_2.md`](PHASE_2.md) for Cloud SQL, CSV/PDF export, and production database setup.

**SME interviews:** [`SME_INTERVIEW.md`](SME_INTERVIEW.md)

See [`VISION.md`](VISION.md).
