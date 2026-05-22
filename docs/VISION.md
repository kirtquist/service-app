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
| **Web UI** | Primary product surface (framework TBD — Django or FastAPI + frontend; favor whatever ships approval UI fastest) |
| **Secrets** | Env / vault for API keys; no raw keys in app DB |
| **Integrations** | Export first, then QBO API |

---

## Roadmap (product phases)

### Phase 0 — Today (repo scaffold)

- OpenRouter parsing, mock catalog, CLI demo, DB stubs, secrets pattern.

### Phase 1 — Approval MVP

- Auth (single shop)
- Invoice list and detail in browser
- Status workflow: draft → pending → approved
- Manual create/edit line items
- Wire `parse_service_call()` to create **draft** invoices from transcript

### Phase 2 — Export

- PDF invoice for customer
- CSV formatted for QuickBooks import

### Phase 3 — QuickBooks Online

- Connect company (OAuth)
- Push approved invoices; track sync state

### Phase 4 — Field capture & polish

- Speech-to-text integration
- Photos / attachments
- Smarter catalog and regional pricing
- SaaS / multi-tenant if validated

---

## Open questions

- [ ] SaaS vs licensed vs bundled with supplier — pricing and packaging
- [ ] Mobile native app vs responsive web only for v1
- [ ] Estimates vs invoices first in QuickBooks
- [ ] Who is the buyer: owner, bookkeeper, or supplier partner?
- [ ] Compliance / retention requirements for invoices by state
- [ ] Brand name and trade-specific marketing (plumbing-only vs multi-trade later)

---

## Revision log

| Date | Change |
|------|--------|
| 2026-05-22 | Initial vision doc — web approval workflow, QuickBooks direction, SME validation plan |
