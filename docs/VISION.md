# Service App — Product vision

Living document for product direction. Update as we learn from pilots, SME interviews, and build milestones.

**Related:** technical current state → [`FEATURE_OVERVIEW.md`](FEATURE_OVERVIEW.md)

---

## One-line pitch

Help trade service owners **capture jobs in the field**, **review and approve invoices at home**, and **send approved data to their bookkeeper** (e.g. QuickBooks) — without paperwork or re-keying.

---

## Problem

Small plumbing (and similar trade) shops lose time and money on:

- Handwritten or mental notes after a long day
- Rebuilding invoices from memory at home
- Bookkeepers re-entering the same line items into accounting software
- Mistakes on parts, labor hours, and customer details

Most owners and technicians are **not “computer people.”** They need something that feels like reviewing a receipt, not operating business software.

---

## Target users

| Persona | Role | Needs |
|---------|------|--------|
| **Owner / lead tech** | Runs jobs, approves what gets billed | Fast capture in the field; simple review and approve at home |
| **Office / bookkeeper** | QuickBooks, taxes, AR | Clean invoice data in QuickBooks without manual entry |
| **Supply-side contacts** | Distributors, reps (validation channel) | Insight into real workflows, pricing habits, pain points |

**Initial vertical:** plumbing. Sample catalog data in the repo is electrician-flavored placeholder only.

**Go-to-market:** TBD (SaaS, per-shop licensing, etc.). Early focus is **one shop, one login, real jobs** — prove the workflow before multi-tenant complexity.

---

## Core workflow (target state)

```
Field capture          Draft in app              Review at home           Bookkeeping
(voice / text /        (LLM + catalog            (web UI: edit,           (QuickBooks etc.)
 photos — TBD)    →     →  line items)       →     approve, status)    →    sync / export
```

1. **In the field** — minimal friction: dictate or jot what was done (speech-to-text is upstream; not in MVP repo yet).
2. **System drafts** — parse transcript into customer, parts, labor; apply catalog pricing.
3. **At home** — user opens a **web** list of invoices in any state; fixes line items; taps **Approve**.
4. **Downstream** — approved invoices export or sync to QuickBooks for the bookkeeper’s normal review.

The **CLI demo** in this repo is for **development and testing only** — not the customer-facing product.

---

## Product principles

- **Web-first, mobile-friendly** — responsive UI; phone browser at home is enough for MVP.
- **Low typing** — big actions (Approve, Edit line, Send to QuickBooks); messy field notes are OK.
- **Clear statuses** — user always knows where an invoice stands (see lifecycle below).
- **Your app = approval layer** — QuickBooks remains the accounting system of record; we don’t ask users to replace it.
- **Progressive complexity** — CSV export before OAuth APIs; one shop before SaaS.

---

## Invoice lifecycle

Statuses (names may change after SME input):

| Status | Meaning |
|--------|---------|
| **Draft** | Created from field capture; may be incomplete |
| **Pending review** | Ready for owner to check at home |
| **Approved** | Owner signed off; eligible for export/sync |
| **Sent / synced** | Pushed to customer or QuickBooks |
| **Paid** | Optional later; may come from QuickBooks webhooks |

Design goal: **one job → one invoice card** with total visible; editing feels like fixing a receipt.

---

## Bookkeeping integration (QuickBooks)

High-value differentiator: *“Approve at home; it lands in QuickBooks for your bookkeeper.”*

**Intended flow**

1. User approves invoice in Service App.
2. App pushes **invoice data** to QuickBooks Online (QBO) — ideally as something the bookkeeper can review, not silently finalized.
3. Store sync metadata on each invoice: external system, external ID, sync status, last synced at.

**Phased approach**

| Phase | Capability |
|-------|------------|
| 1 | Web invoices + approval UI |
| 2 | CSV / PDF export for manual QuickBooks import |
| 3 | QBO API — OAuth per company, one-way push of **approved** invoices |
| 4 | Customer/item mapping, retries, optional status from QBO |

**Notes**

- **QuickBooks Online** is the likely first integration (API + OAuth). Desktop QB is a separate, harder path.
- Intuit developer program, sandbox, and production app review apply for live QBO.
- Line-item mapping to QBO Items will be imperfect at first — generic “Parts” / “Labor” lines are acceptable for MVP sync.

Other systems (Xero, FreshBooks) are out of scope until QBO path is proven.

---

## Validation & SME input

Planned conversations with plumbing SMEs — including contacts through a friend who **sells plumbing supplies** and knows many working plumbers.

**Questions to explore**

- How do they quote and invoice today (paper, QB, text, Square)?
- When and where do they “close out” a job (truck, kitchen table, weekend)?
- What must be on an invoice before they’re comfortable sending it?
- Would they trust AI-drafted line items if review is one screen away?
- QuickBooks Online vs Desktop split in that market?
- Price sensitivity and who pays (owner vs shop) for a tool like this.

Capture learnings in this doc or linked interview notes as meetings happen.

---

## Technical direction (summary)

Aligned with [`FEATURE_OVERVIEW.md`](FEATURE_OVERVIEW.md):

| Layer | Direction |
|-------|-----------|
| **LLM** | OpenRouter — parse field transcripts into structured job data |
| **Catalog / pricing** | DB-backed parts and labor rates; plumber SKUs replace electrician placeholders |
| **Persistence** | SQLAlchemy models (`customer`, `job`, `invoice`, `invoice_line`); Alembic migrations |
| **Web UI** | Primary surface for **approval at home** | Invoice list, edit, approve (Phase 1b) |
| **WhatsApp** | Early **field demo** channel | Send job text → get parsed JSON back (Phase 1a) |
| **Hosting** | GCP **Cloud Run** for demos | Webhook + API; scale-to-zero, low cost |
| **Secrets** | Env locally; **Secret Manager** on GCP | No raw keys in app DB |
| **Integrations** | Export first, then QBO API | After approval workflow validated |

---

## Demo strategy

**Goal:** show value to SMEs and supply contacts **before** the full product exists.

| Channel | Best for | When |
|---------|----------|------|
| **CLI** (`service-app-demo`) | Developer testing | Now (done) |
| **WhatsApp** | Field-style demo — “text the bot a job note, get structured data back” | **Early Phase 1** — first external demo |
| **Web UI** | Review, edit, approve invoices at home | Phase 1b — after parse demo lands |
| **QuickBooks** | Bookkeeper handoff | Phase 2+ |

**Why WhatsApp first for demos**

- Plumbers and small-shop owners already use WhatsApp daily — no new app to install.
- Proves the **core magic** (messy note → structured job JSON) in one message.
- Easy to share with your supply-side friend’s contacts: “Send this number a voice note or text.”
- Web approval is still the long-term product; WhatsApp is the **fastest proof** for SME conversations.

**WhatsApp voice notes:** Phase 1a can start with **typed text only**. Voice adds: download media from WhatsApp → speech-to-text (Whisper via OpenRouter or Google STT) → existing `parse_service_call()`. Add voice once text replies work end-to-end.

**Hosting:** Deploy the webhook/API on **GCP Cloud Run** (container, HTTPS URL for Meta/Twilio webhooks, scales to zero for cheap demos). Use **Secret Manager** for `OPENROUTER_API_KEY` and WhatsApp tokens — not `.env` in the image.

---

## Roadmap (product phases)

### Phase 0 — Today (repo scaffold)

- OpenRouter parsing, mock catalog, CLI demo, DB stubs, secrets pattern.

### Phase 1a — Demo loop (WhatsApp + Cloud Run) ← **start here**

Prove parse in the field; JSON reply in chat. Minimal scope:

1. Pydantic model for parse output (validate LLM JSON).
2. Small **FastAPI** app: `GET /health`, `POST /parse` (internal), `POST /webhook/whatsapp`.
3. WhatsApp provider: **Twilio Sandbox** or **Meta WhatsApp Cloud API** (sandbox for speed; Meta for production-like demos).
4. Flow: inbound message → `parse_service_call()` → reply with formatted JSON (optionally append catalog line totals).
5. **Dockerfile** + deploy to **Cloud Run**; secrets from GCP Secret Manager.
6. Smoke-test with 3–5 real-ish plumber job notes; iterate prompt with SME feedback.

**Not in 1a:** auth, database, invoice persistence, web UI, QuickBooks.

### Phase 1b — Approval MVP (web)

- Auth (single shop).
- Invoice list and detail in browser.
- Status workflow: draft → pending → approved.
- Manual create/edit line items.
- Persist parsed WhatsApp (or manual) jobs as **draft invoices** in DB.
- Optional: link from web “paste transcript” using same `/parse` API.

### Phase 2 — Export

- PDF invoice for customer
- CSV formatted for QuickBooks import

### Phase 3 — QuickBooks Online

- Connect company (OAuth)
- Push approved invoices; track sync state

### Phase 4 — Field capture & polish

- WhatsApp **voice** notes (STT pipeline)
- Photos / attachments
- Smarter catalog and regional pricing
- SaaS / multi-tenant if validated

---

## Phase 1a — checklist (get started)

Use this as the working task list until the WhatsApp demo is live.

### Week 1 — API + validation

- [x] Add `ParsedServiceCall` Pydantic model (`customer_name`, `parts[]`, `labor_hours`).
- [x] Validate `parse_service_call()` output; clear errors when model returns bad JSON.
- [x] Add `service_app/api/` with FastAPI app wrapping existing ingestion + catalog.
- [x] `POST /parse` — accept `{ "transcript": "..." }`, return validated JSON (+ optional price hints).
- [x] Unit tests for validation (mock LLM or fixture JSON).

### Week 2 — Cloud Run

- [x] Add `Dockerfile` (slim Python image, `uvicorn` entrypoint).
- [ ] GCP project + Artifact Registry — run **`pulumi up`** in [`infra/`](../infra/README.md) (project **`kgs-service-app`**) or manual steps in [`GCP_DEPLOY.md`](GCP_DEPLOY.md)
- [ ] Secret Manager: `openrouter-api-key` → `OPENROUTER_API_KEY` on Cloud Run.
- [x] GitHub Actions deploy workflow (push to `dev` / `main` after tests).
- [ ] Add **`GCP_SA_KEY`** GitHub secret; merge to `dev` and confirm deploy.
- [ ] Confirm `GET /health` and `POST /parse` from curl against Cloud Run URL.

### Week 3 — WhatsApp

- [ ] Choose provider:
  - **Twilio WhatsApp Sandbox** — fastest for first SME demo (join sandbox, send to shared number).
  - **Meta WhatsApp Cloud API** — better long-term; needs Meta Business app + verified webhook URL (Cloud Run URL works).
- [ ] Implement webhook: verify challenge (Meta) or Twilio signature.
- [ ] On text message: call parse → reply with human-readable summary + JSON block.
- [ ] Test with yourself, then one SME contact via your supply friend.

### Week 4 — SME feedback

- [ ] Prepare 5 example prompts (plumber-flavored, not electrician).
- [ ] SME session: watch them send real-style messages; note confusion and missing fields.
- [ ] Tune prompt and reply format; log transcripts (with consent) for iteration.
- [ ] Decide: proceed to Phase 1b web UI or extend WhatsApp (voice, “approve” keyword).

### GCP services (Phase 1a)

| Service | Role |
|---------|------|
| **Cloud Run** | Host FastAPI + WhatsApp webhook |
| **Secret Manager** | OpenRouter + WhatsApp credentials |
| **Artifact Registry** | Store container images |
| **Cloud Build** (optional) | CI deploy on push to `main` |
| **Cloud SQL / SQLite in volume** | Defer to Phase 1b — not needed for JSON demo |

---

## Open questions

- [ ] SaaS vs licensed vs bundled with supplier — pricing and packaging
- [ ] Mobile native app vs responsive web only for v1
- [ ] Estimates vs invoices first in QuickBooks
- [ ] Who is the buyer: owner, bookkeeper, or supplier partner?
- [ ] Compliance / retention requirements for invoices by state
- [ ] Brand name and trade-specific marketing (plumbing-only vs multi-trade later)
- [ ] WhatsApp: Twilio sandbox vs Meta Cloud API for first pilot
- [ ] WhatsApp Business number ownership (your brand vs test sandbox)

---

## Revision log

| Date | Change |
|------|--------|
| 2026-05-22 | Initial vision doc — web approval workflow, QuickBooks direction, SME validation plan |
| 2026-05-22 | Demo strategy — WhatsApp + Cloud Run in Phase 1a; Phase 1b web approval; Phase 1a checklist |
| 2026-05-22 | Dockerfile, GitHub Actions deploy to Cloud Run (`kgs-service-app`); [`GCP_DEPLOY.md`](GCP_DEPLOY.md) |
| 2026-05-22 | Pulumi stack in `infra/` for GCP foundation (APIs, AR, secrets, IAM) |
