# to-do follow-up (todof.md)

Follow-up task list on top of the LOGBOOK. Mirrors "1 / 2 / bigger jumps" plan.

Legend: `[x]` done · `[ ]` pending

## ✅ Done

### Item 1 — Step 18: Scroll-to-top + footer copy fix (LOGBOOK 18)
- [x] Floating scroll-to-top button (ScrollToTop.jsx/.css)
- [x] Footer: "Ask AI coming soon" -> "Ask AI live"

### Bigger jumps — Step 19: UX & product upgrades (LOGBOOK 19)
- [x] 19.1 Deal detection (backend: recommend.py `_deal_context` / `_classify_deal`; api `DealOut`)
- [x] 19.2 Sort/filter toolbar + deal badges on results
- [x] 19.3 Animated stat count-up (useCountUp.js) in Hero
- [x] 19.4 "How It Works" explainer section
- [x] 19.5 Favorites / saved list (localStorage service + FavoritesSection + hearts/Save button)
- [x] 19.6 Shareable / bookmarkable search URLs (FinderSection)
- [x] 19.7 Verification: build ✓ oxlint ✓ pytest 206 ✓

### Follow-up fixes
- [x] 19.10 Ask AI no longer re-describes the laptop before answering (model/llm.py SYSTEM_PROMPT)

## ⏳ Remaining

### Item 2 — Chatbot (Ask AI) improvements  ← NEXT
- [ ] Decide scope: follow-up memory, more grounded answers, typing UX polish
- [ ] Any extra Ask AI polish after 19.10
- [ ] (if wanted) show retrieved laptop references instead of just a count
- [ ] (stretch) conversation-start suggestions / quick asks

### Nice-to-haves (loosely suggested earlier, not yet scoped)
- [ ] Toast notifications (e.g. "saved", "deal found") instead of relying on button state alone
- [ ] "Recently viewed" strip
- [ ] Dark mode toggle — blocked: design.md mandates light theme only (leave unless overridden)

### Optional future (from LOGBOOK "Remaining Work")
- [ ] README.md with project description + setup instructions
- [ ] CLI interface
- [ ] Docker setup for deployment