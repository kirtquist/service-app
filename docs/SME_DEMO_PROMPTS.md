# SME demo prompts (plumber-flavored)

Use these for WhatsApp or `/app/invoices/new` testing with plumbing SMEs.

**Interview questions:** [`SME_INTERVIEW.md`](SME_INTERVIEW.md)

---

## Standard job prompts

1. **Kitchen leak**
   ```
   Smith house — kitchen sink leak, replaced P-trap and two compression fittings, about 2 hours on site
   ```

2. **Water heater**
   ```
   Johnson job — installed 50 gal water heater, used 3/4 copper fittings and expansion tank, 4 hours labor
   ```

3. **Toilet repair**
   ```
   Garcia residence, replaced toilet and supply line, 1.5 hours
   ```

4. **Main line clog**
   ```
   Miller commercial — cleared main line clog with snake, pulled back roots, 3 hours, one cleanout access
   ```

5. **Shower valve**
   ```
   Davis home — swapped out leaking shower valve cartridge and resealed trim, 1 hour
   ```

After each test, open the review link or `/app/invoices` and confirm customer name, parts, and hours look reasonable.

---

## Incomplete first message (interview scenarios)

Use when discussing whether one end-of-job message is enough.

6. **Labor only — parts forgotten**
   ```
   Smith house — fixed kitchen sink leak, about 2 hours on site
   ```
   *During interview, ask what parts they’d add later (P-trap, fittings, etc.).*

7. **Parts light — hours unclear**
   ```
   Johnson — water heater swap, used expansion tank and some copper fittings
   ```
   *Discuss whether they’d send a follow-up or fix at home on the web UI.*

---

## Append-note example (future feature — describe, don’t build yet)

After reviewing an invoice that missed items, ask if they would paste something like:

```
Also used 3/4 copper elbow, two rubber washers, and expansion tank — about one more hour on site
```

See **section D2** in [`SME_INTERVIEW.md`](SME_INTERVIEW.md).
