# SME meeting agendas — printable run sheets

Two timeboxed agendas for validation meetings. Use with the question bank in [`SME_INTERVIEW.md`](SME_INTERVIEW.md) and demo text in [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md).

**Product one-liner:** *“Technician sends a job note (WhatsApp or web) → shop owner reviews and approves at home → invoice can go to QuickBooks.”*

---

## Run sheet 1 — Plumbing supply salesman (pre-meeting)

**Duration:** ~30 minutes  
**Goal:** Understand how shops track parts and price jobs; obtain catalog sample; secure intro to one shop owner for a follow-up demo.  
**You are not demoing to the end user yet** — this is discovery + relationship + artifacts.

### Before you join

- [ ] Calendar invite with a plain title (e.g. “Plumbing workflow — 30 min chat”).
- [ ] No live demo required (optional: have Cloud Run or local `/app/invoices` ready if he asks).
- [ ] Blank copy of [Interview notes template](#notes-template) below.
- [ ] Ask by email/text beforehand: *“Could you bring or send a sample price sheet or catalog export (redacted pricing is fine)?”*

### Agenda

| Time | Topic | What to say / do |
|------|--------|------------------|
| 0–3 min | **Intro** | Thank him. One sentence on what you’re building (one-liner above). *“I’m not selling anything today — I want to learn how shops really work from someone who sees many of them.”* |
| 3–12 min | **His view of shop workflows** | How do his customers track parts on a job? When do they capture info — on site, end of day, at home? Who builds the invoice? See [`SME_INTERVIEW.md` — A, B, C](SME_INTERVIEW.md). |
| 12–22 min | **Catalog & pricing** | Walk through [Section F](SME_INTERVIEW.md). Focus: sample sheet, column layout, field names vs counter names, list vs jobber pricing, top SKUs on a service truck. |
| 22–27 min | **Introductions & follow-up** | *“Who’s one shop owner who might try a 45-minute demo — WhatsApp note and a review screen at home?”* Confirm QB Online vs Desktop for that shop. |
| 27–30 min | **Wrap** | Recap artifacts requested. Schedule plumber/owner session. Fill notes template. |

### Must-get from this meeting

- [ ] Sample catalog / price sheet (even 10–50 rows + column headers)
- [ ] Yes/no on intro to at least one shop owner
- [ ] Rough sense: QB Online vs Desktop among his customers
- [ ] Consent to save quotes / notes: Y / N

### Optional if time

- Show a **30-second** screen share of invoice list (no WhatsApp setup on his phone).
- Mention future direction: map “P-trap” text to catalog SKU (validate interest only).

---

## Run sheet 2 — Shop owner / working plumber (full SME session)

**Duration:** ~45–60 minutes  
**Goal:** Validate capture timing, review workflow, and pricing trust; run a live demo; capture quotes for the revision log.  
**Prerequisite:** WhatsApp sandbox **or** local/Cloud Run web UI working; [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md) open.

### Before you join

- [ ] Confirm consent to save transcripts/quotes.
- [ ] Test demo path once: send prompt → invoice appears → `/app/invoices` → approve (and QBO connect only if they use QBO Online).
- [ ] Pick 2–3 prompts from [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md) (include one **incomplete** prompt if discussing end-of-job-only capture).
- [ ] Interview notes template ready (below).
- [ ] Note their **QuickBooks** product (Online / Desktop / other).

### Agenda

| Time | Topic | What to say / do |
|------|--------|------------------|
| 0–5 min | **Intro & consent** | One-liner. *“I’ll ask about how you work today, then show a rough prototype — your honest ‘this would never fly’ feedback is the goal.”* Consent to take notes / quotes. |
| 5–20 min | **Discovery** | [`SME_INTERVIEW.md` — A, B, C](SME_INTERVIEW.md): parts tracking, when they capture job info, who invoices, time to QuickBooks. Listen more than talk. |
| 20–35 min | **Live demo** | **Path A (WhatsApp):** They (or you) send a demo prompt → show reply → open `/app/invoices` on laptop/phone. **Path B (web only):** `/app/invoices/new`, paste prompt. Edit a line, show approve, optional CSV/PDF or **Send to QuickBooks** if connected. |
| 35–45 min | **Tool fit** | [`SME_INTERVIEW.md` — D](SME_INTERVIEW.md): end-of-job text vs notes as they go; fixing missed parts at home; WhatsApp vs other. **D2:** describe “add from note” concept — do not promise ship date. |
| 45–55 min | **Catalog & pricing** (if relevant) | If they use a price sheet: how they look up parts, aliases, trust auto-pricing. Tie to [Section F](SME_INTERVIEW.md) if they have a sheet handy. |
| 55–60 min | **Wrap** | Top 3 takeaways aloud. Ask: *“Would you try this on one real job next week?”* Fill notes template; schedule follow-up. |

### Demo prompt suggestions

**Standard (pick one):** Kitchen leak or water heater from [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md).

**Incomplete job (if testing end-of-job capture):**

```
Smith house — fixed kitchen sink leak, about 2 hours on site
```

Then ask: *“What parts were missing? Would you fix that tonight on one screen?”*

### Must-capture

- [ ] Reaction to WhatsApp (or web) capture: positive / mixed / negative
- [ ] Reaction to home review / approve screen
- [ ] Reaction to “add from note” (D2)
- [ ] QuickBooks: Online / Desktop / other
- [ ] Would they pay / who pays (owner vs shop)
- [ ] Consent to save transcript: Y / N

### After the meeting

- [ ] Update [`VISION.md`](VISION.md) revision log or open questions.
- [ ] Tune [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md) if new job types came up.
- [ ] If catalog sample received: note columns + SKU vs alias preference (feeds GitHub issues #13 / #14).
- [ ] File follow-up GitHub issue if a concrete feature request emerged.

---

## Notes template

Copy for each session:

```
Date:
Contact / shop:
Role: owner / tech / bookkeeper / supply salesman / other
Meeting type: Run sheet 1 (salesman) / Run sheet 2 (shop)
QuickBooks: Online / Desktop / Other: ___

How they track parts:
When they capture job info:
Who builds the invoice:
Time job done → in QuickBooks:

Demo reaction (WhatsApp / web):
Review & approve reaction:
“Add from note” reaction (Y / maybe / no):

Catalog / price sheet: received Y/N — format: ___
Intro to another contact: Y/N — who: ___

Key quotes:
Follow-ups:
Consent to save notes/transcript: Y / N
```

---

## References

- [`SME_INTERVIEW.md`](SME_INTERVIEW.md) — full question bank
- [`SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md) — demo message text
- [`VISION.md`](VISION.md) — product direction and catalog strategy
- [`WHATSAPP_SETUP.md`](WHATSAPP_SETUP.md) — demo channel setup
- [`PHASE_3.md`](PHASE_3.md) — QuickBooks connect (if demoing sync)
