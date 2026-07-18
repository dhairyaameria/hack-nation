# 06 — Frontend & Investor UX (Agent E)

**Owner:** Agent E — Frontend
**Depends on:** API contracts in `01-CONTRACTS.md` (build against fixtures in `15-MOCK-FIXTURES.md` until real endpoints land).
**PRD sections covered:** §7.8, §20.

**Design bar (from the brief):** "Notion-level approachability, Bloomberg-level analytical depth." A non-technical investor must navigate the entire core flow (see founder → understand score → read memo → see evidence → decide) without support. UX is 15% of judging — real, but the smallest slice; if the team is behind, data/trust features win over polish.

---

## Stack

Next.js + TypeScript + Tailwind + shadcn/ui. Deploy to Vercel. Consume REST (`/api/v1/*`) and GraphQL per contracts. Mirror shared types from `/shared/schemas`.

## Screens & Components (priority order)

### P0 — Core demo path
1. **Pipeline dashboard (home):**
   - Top sourced opportunities, inbound + outbound clearly labeled with discovery channel and triggering signal.
   - **Decision SLA timer** per opportunity: live "signal → screening → diligence → decision" clock (from `decision_log` timestamps). This proves the 24-hour claim — make it prominent.
2. **Opportunity detail:**
   - **Three axis cards** (Founder / Market / Idea-vs-Market): value, trend arrow, confidence — visually separate, NEVER a combined number. Market axis renders `bullish|neutral|bear`.
   - **Trust heatmap** by claim category (green/yellow/red via source quality, recency, corroboration).
   - **Contradiction alerts** banner — surfaced before the memo is readable.
   - **Memo view:** required sections + optional sections with explicit "not disclosed"/"unavailable" flags rendered as visible badges (never hidden).
   - **Evidence drill-down:** click any claim → exact source (deck slide, GitHub commit, tweet, Wayback snapshot) in ≤2 clicks. Uses `/recommendation/{id}/trace`.
   - **"Why this recommendation?"** trace path: recommendation → claim → evidence.
3. **Founder profile:**
   - **Founder Genome radar chart:** execution velocity, technical depth, resilience proxy, public footprint depth + Founder Score trend line beneath.
   - **Network embeddedness badge** — SEPARATE from the radar (capped/disclosed signal): small badge, click → exact 2nd-degree path (which anchor, via whom, edge type) + the mandatory disclosure text: *"Network proximity signal — reflects who this founder is connected to, not their own demonstrated capability."*
   - Founder Score history chart (persists across applications).
4. **VC Agent chat panel** (persistent, e.g. right-side drawer):
   - Free-form questions → answers showing which **Cursor skill(s)** ran + inline citations.
   - "Re-run this question" control → renders diff vs. prior answer.

### P1 — Strong differentiators
5. **Network graph explorer:** see `09-NETWORK-GRAPH-UI.md`
6. **Wayback timeline:** company historical snapshots with sentiment/narrative-drift markers
7. **Thesis Engine settings:** `/settings/thesis` — full spec in `12-THESIS-SETTINGS-UI.md`; switching active thesis visibly reorders pipeline
8. **NL query bar:** compound query input → ranked results with per-clause match explanations

### P2 — If time allows
9. **Channel intelligence view:** channel quality ranking + underexplored suggestions.
10. **"Why not?" rejection views:** specific reason + what milestone would change the outcome.
11. **Inbound application form** (public-facing): deck upload + company name, nothing else required.
12. **ElevenLabs voice briefing:** one-click "60-second partner briefing" audio from memo summary.

## Hard UX Rules

- Never render an averaged/composite score across the three axes.
- Never hide a data gap — "not disclosed" flags are visible badges.
- Every factual UI element links to its evidence.
- All copy in plain investor language, no ML jargon.

## Acceptance Checks

- [ ] Core flow navigable start-to-finish without explanation.
- [ ] Three axes always displayed independently with trends.
- [ ] Claim → evidence drill-down in ≤2 clicks.
- [ ] Genome radar + separate network badge with disclosure text.
- [ ] SLA timer live for at least one opportunity.
- [ ] VC Agent chat panel shows Cursor skill names + citations + re-run diff.
- [ ] Memo gap flags visible; contradiction alerts precede memo reading.
