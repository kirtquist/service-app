# Pre-Phase 3 — local test plan

Manual checklist before pushing `feature/pre-phase3-logout-sme-docs` and opening a PR to `dev`.

**Scope:** Logout (code) + SME/docs updates. No new invoice or WhatsApp behavior.

---

## 1. Automated tests

From repo root:

```bash
pip install -e ".[dev]"
pytest -q
```

**Pass criteria:** All tests green, including new `tests/test_web_auth.py`.

---

## 2. Start local API

```bash
cp .env.example .env
# Set WEB_AUTH_PASSWORD to something you will remember for this session
# OPENROUTER_API_KEY optional for logout/docs-only testing

pip install -e ".[dev]"
service-app-api
# Default: http://127.0.0.1:8090
```

---

## 3. Logout flow (main code change)

| Step | Action | Expected |
|------|--------|----------|
| 3.1 | Open `http://127.0.0.1:8090/app/invoices` | Browser prompts for username/password |
| 3.2 | Sign in with `WEB_AUTH_USERNAME` / `WEB_AUTH_PASSWORD` | Invoice list loads |
| 3.3 | Confirm **Log out** link in header (top right) | Link visible on list and detail pages |
| 3.4 | Click **Log out** | Lands on “You are logged out” page |
| 3.5 | Click **Sign in again** | Browser prompts for credentials again (not auto-logged-in) |
| 3.6 | Sign in successfully | Invoice list works as before |

**Note:** Logout behavior depends on the browser’s HTTP Basic auth handling. If step 3.5 still auto-logs you in, try a private/incognito window or clear site credentials for `127.0.0.1` — document what you see.

---

## 4. Invoice UI hint (copy only)

| Step | Action | Expected |
|------|--------|----------|
| 4.1 | Open any invoice detail page | Under **Add line**, muted text explains manual price entry |
| 4.2 | Add a line (name, qty, price) | Line appears; totals update |

---

## 5. Documentation spot-check

| File | Check |
|------|--------|
| [`docs/SME_INTERVIEW.md`](SME_INTERVIEW.md) | Parts tracking, capture timing, “add from note” concept |
| [`docs/PHASE_1B.md`](PHASE_1B.md) | Workflow section: field vs home; pricing on parse vs manual add |
| [`docs/VISION.md`](VISION.md) | Link to SME interview doc |
| [`docs/SME_DEMO_PROMPTS.md`](SME_DEMO_PROMPTS.md) | Incomplete-job + append-note examples |

---

## 6. Regression (unchanged behavior)

| Step | Action | Expected |
|------|--------|----------|
| 6.1 | `GET http://127.0.0.1:8090/health` | `{"status":"ok"}` |
| 6.2 | Create invoice via `/app/invoices/new` (paste transcript) | Redirects to detail; lines populated if OpenRouter configured |
| 6.3 | Approve an invoice | Status → Approved; export buttons appear |
| 6.4 | Download CSV/PDF on approved invoice | Files download |

Skip 6.2 if `OPENROUTER_API_KEY` is not set locally.

---

## 7. Ready for PR

When all above pass:

```bash
git status
git add -A
git commit -m "Add web logout and SME interview documentation."
# When ready:
git push -u origin feature/pre-phase3-logout-sme-docs
gh pr create --base dev --head feature/pre-phase3-logout-sme-docs --title "..." --body "..."
```

After merge to `dev`, confirm GitHub Actions deploy succeeds and repeat **section 3** against production Cloud Run URL.
