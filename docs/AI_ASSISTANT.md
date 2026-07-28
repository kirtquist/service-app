# AI assistant layer — future plan

Potential Phase 4+ capability: a shop-facing assistant that helps review invoices, answer job questions, and take safe actions — **without** rewriting the data layer or adopting a graph database.

**Related:** [`VISION.md`](VISION.md) · [`FEATURE_OVERVIEW.md`](FEATURE_OVERVIEW.md) · [`PHASE_3.md`](PHASE_3.md)

---

## Decision (for now)

| Approach | Verdict |
|----------|---------|
| **Graph database rewrite** | **Defer.** Current domain (invoices, lines, QBO connection) is relational and small. Graph adds cost without solving near-term goals. |
| **Minimal assistant on existing stack** | **Preferred.** Postgres/SQLite + SQLAlchemy models + FastAPI tools. |
| **Vector search (optional later)** | **Add in Postgres** (`pgvector`) if semantic “similar jobs” search is needed — not a separate graph store. |

Revisit graph or hybrid storage only if a concrete feature blocks on relational queries (e.g. large parts catalog with supplier cross-references and recommendation graphs).

---

## What the assistant would do (MVP scope)

Shop owner or bookkeeper in the **web UI** (or future chat surface):

- “Show pending invoices for Baker”
- “What was the original field note on invoice #12?”
- “Add a line: 3/4 copper fitting, qty 2, $8 each” (with confirmation)
- “Summarize approved jobs this week”
- “Why did this invoice total change?” (reads edit history when available)

**Out of scope for first cut:** autonomous approval, unsupervised QBO pushes, or replacing the approval UI.

---

## Architecture — minimal layer

Keep **SQLAlchemy models** as system of record (`Invoice`, `InvoiceLine`, `QuickBooksConnection`). Add a thin **assistant module** that exposes **tools**, not raw SQL to the model.

```
User (web chat panel)
    → Assistant orchestrator (OpenRouter, same as parse)
        → Tool calls (structured)
            → Existing services (invoices/, qbo/, export/)
                → Postgres / SQLite
```

### Tool examples (future)

| Tool | Wraps |
|------|--------|
| `list_invoices` | `invoice_service.list_invoices` |
| `get_invoice` | `invoice_service.get_invoice` |
| `add_line` | `invoice_service.add_invoice_line` (confirm in UI) |
| `parse_transcript` | `parse_transcript` (reuse ingestion) |
| `qbo_connection_status` | `qbo.service.is_connected` |

Tools return **Pydantic JSON** the model can reason over. Mutating tools require explicit user confirmation in the UI before execution.

### Where it lives (sketch)

```
src/service_app/assistant/
  tools.py       # registered tool definitions + handlers
  prompts.py     # system prompt, shop context
  service.py     # chat turn: messages → tool loop → reply
```

Web: optional `/app/assistant` chat panel or sidebar on invoice detail — reuses HTTP Basic auth.

---

## What we already have (reuse)

| Building block | Today |
|----------------|--------|
| LLM provider | OpenRouter via `ingestion.py` / `llm.py` |
| Structured output | Pydantic (`ParseResponse`, invoice models) |
| Persistence | `Invoice`, `InvoiceLine`, `QuickBooksConnection` |
| Auth | HTTP Basic on `/app/*` |
| Field capture | WhatsApp + `/app/invoices/new` |

No new database engine required for v1.

---

## Optional enhancements (later)

| Enhancement | When | How |
|-------------|------|-----|
| **Semantic search** | “Jobs like this one” | `pgvector` on `source_transcript` + customer name in Cloud SQL |
| **Audit trail** | “Who changed this line?” | `invoice_events` table (relational) |
| **Catalog assistant** | “Did you mean SKU X?” | Catalog in DB + embedding match; still relational |
| **MCP / external agents** | CI or third-party tools | Expose same tool layer as HTTP or MCP server |

---

## Phasing

| Phase | Focus | Assistant |
|-------|--------|-----------|
| **3** (now) | QBO OAuth + invoice sync | — |
| **4a** | Read-only assistant | List/get/summarize invoices; explain totals |
| **4b** | Confirmed writes | Add/edit lines, status hints (user approves each action) |
| **4c** | Search + catalog | pgvector on transcripts; catalog match suggestions |

---

## Non-goals (explicit)

- Replacing the approval workflow UI
- Graph DB migration for relationship modeling
- Fully autonomous bookkeeping or QBO sync without human approve
- Multi-tenant SaaS assistant until single-shop pilot is validated

---

## Open questions

- [ ] Chat UI: dedicated page vs invoice-detail sidebar?
- [ ] Same OpenRouter model as parse, or a cheaper model for tool routing?
- [ ] Log assistant sessions for SME tuning (with consent)?
- [ ] WhatsApp as assistant surface, or web-only first?

---

## Revision log

| Date | Change |
|------|--------|
| 2026-07-28 | Initial future plan — minimal assistant on relational stack; graph DB deferred |
