# SME interview guide — plumbing shops

Structured questions for supply-side contacts, working plumbers, and shop owners. Use alongside demo prompts in [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md).

**Product context:** [`VISION.md`](VISION.md)

---

## Before the meeting

- Confirm consent if you will save real transcripts or quotes.
- Have WhatsApp sandbox or `/app/invoices/new` ready for a live demo.
- Note whether they use **QuickBooks Online** or **Desktop** — integration path differs.

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
Role (owner / tech / bookkeeper / supplier contact):
QuickBooks: Online / Desktop / Other: ___
How they invoice today:
Parts tracking method:
End-of-job vs ongoing notes:
Reaction to WhatsApp demo:
Reaction to web review / approve:
Reaction to “add from note” concept:
Key quotes:
Follow-ups:
Consent to save transcript: Y / N
```

---

## After the meeting

- Update [`VISION.md`](VISION.md) open questions or revision log with learnings.
- Tune demo prompts in [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md) if new job types surfaced.
- Decide whether to prioritize **WhatsApp append**, **web add-from-note**, or **end-of-job only** for the next build.
