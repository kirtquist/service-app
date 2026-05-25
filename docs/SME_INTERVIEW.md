# SME interview guide — plumbing shops

Structured questions for supply-side contacts, working plumbers, and shop owners. Use alongside demo prompts in [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md).

**Product context:** [`VISION.md`](VISION.md)

---

## Primary SME — plumbing supply salesman

The main validation contact is a **salesman who sells plumbing supplies to working plumbers**. He is not the end user, but he is valuable for:

- Introducing working plumbers / shop owners for demos
- How shops **actually** track parts and close out jobs (what he hears from customers)
- **Distributor catalogs and price sheets** — part numbers, list prices, common SKUs, how counter staff vs field techs refer to the same item

**Ask early:** Can he share a **sample price sheet or catalog export** (CSV, PDF, or portal screenshot — redacted pricing OK initially)? Even column headers and example rows help us design import and matching.

See **section F** below for catalog-specific questions tailored to a supply rep.

---

## Before the meeting

- Confirm consent if you will save real transcripts or quotes.
- Have WhatsApp sandbox or `/app/invoices/new` ready for a live demo.
- Note whether they use **QuickBooks Online** or **Desktop** — integration path differs.
- If meeting the supply salesman: ask whether he can bring or send a **catalog sample** before or after the call.

---

## A. How they track parts on a job

- Paper list on clipboard / invoice pad?
- Mental notes until end of day?
- Photos of packaging or supplier receipt?
- Truck stock / van inventory sheet?
- Supplier counter ticket or will-call slip?
- Do they log **every** fitting (elbows, washers) or only “major” materials?
- Do they use a **fixed price sheet / supplier catalog** or guess prices at invoice time?

---

## B. When they capture job info

- On site during the job vs in the truck vs at home?
- One summary at end of job vs multiple updates across the day?
- Multi-day or return-visit jobs — one invoice or several?
- Who remembers parts if the tech forgets something — owner, office, bookkeeper?

---

## C. Close-out and billing

- Who builds the final invoice (tech vs owner vs office)?
- What must be on it before they’re comfortable sending?
- Typical time from job done → invoice in QuickBooks?
- How do they quote and invoice today (paper, QB, text, Square)?

---

## D. Tool fit (ties to Service App)

- Would they text a bot **once at end of job** or prefer to **add notes as they go**?
- If the AI misses a part, is **fixing at home on one screen** acceptable?
- When several parts were missed, would they rather **add each line manually** or **paste/type one short list** (e.g. *“also elbow, two washers, extra hour”*) and let the app parse and add them?
- WhatsApp vs something else for field capture?
- Would they trust AI-drafted line items if review is one screen away?
- Price sensitivity — who pays (owner vs shop) for a tool like this?

### D2. Concept to describe — “Add from note” (future feature)

> *“Imagine you’re reviewing tonight’s job and the tech forgot three fittings. Instead of typing each part and price, you paste a quick note like ‘also 3/4 elbow, two washers, one more hour’ and the app adds priced lines to the invoice. Would you use that?”*

Capture:

- Yes / no / maybe
- What they would type instead
- Whether they want a **preview before apply**
- Whether extra labor should **add** to existing hours vs **replace**

---

## E. Interview notes template

Copy per session:

```
Date:
Shop / contact name:
Role (owner / tech / bookkeeper / supplier rep / salesman):
QuickBooks: Online / Desktop / Other: ___
How they invoice today:
Parts tracking method:
End-of-job vs ongoing notes:
Reaction to WhatsApp demo:
Reaction to web review / approve:
Reaction to “add from note” concept:
Catalog / price sheet available: Y / N / follow-up
Key quotes:
Follow-ups:
Consent to save transcript: Y / N
```

---

## F. Catalog & price sheet (supply salesman / distributor)

Use with the **plumbing supply salesman** or anyone who can speak to distributor data.

### What they can provide

- Sample **price sheet or catalog export** (CSV, Excel, PDF, ERP extract)
- Typical **column layout**: SKU, description, list price, unit, category, manufacturer
- Whether shops get **contract / jobber pricing** vs list (we may need shop-specific sheets later)

### How parts are identified in the field vs at the counter

- Do techs say **part numbers**, **short names** (“P-trap”, “3/4 elbow”), or **full catalog descriptions**?
- What do counter staff type when a tech calls in an order?
- Common **aliases** or regional terms for the same SKU?
- Items that are **never** on the sheet (consumables, markup-only “misc parts”)?

### Pricing rules

- List price from sheet, or **cost plus markup**?
- Who maintains the sheet — shop owner, office, bookkeeper?
- How often does pricing change? Multiple suppliers per shop?

### Matching expectations (validate product direction)

Explain the gap today: *“Tech texts ‘P-trap’ — app must map that to the right row on the price sheet.”*

- Is **SKU / part number** the reliable key, or **description search**?
- Would **“Did you mean this SKU?”** on the review screen be acceptable when match is uncertain?
- Would they trust auto-pricing only when confidence is high?

### Follow-up artifacts to request

- [ ] Redacted catalog sample (10–50 rows is enough to start)
- [ ] List of **top 20 SKUs** on a typical residential service truck
- [ ] Intro to **one shop owner** willing to try WhatsApp + web review demo

---

## After the meeting

- Update [`VISION.md`](VISION.md) open questions or revision log with learnings.
- Tune demo prompts in [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md) if new job types surfaced.
- If catalog sample received: note column names and whether SKU-first or alias-first matching fits.
- Decide whether to prioritize **WhatsApp append**, **web add-from-note**, or **end-of-job only** for the next build.
- Decide next catalog step: **CSV import prototype** vs more alias keys in demo `catalog.py`.
