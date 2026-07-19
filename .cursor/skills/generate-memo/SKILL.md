---
name: generate-memo
description: Produce a full investment memo with required sections, gap flags, and per-claim Trust Scores.
---

# Generate Memo

1. Load opportunity + claims + axis scores from Memory.
2. Invoke Primary → Validator → Referee pipeline (Agent C).
3. Render **all 13 brief sections** in order (required filled when evidence exists; optional flagged when missing):
   - **Required:** Company snapshot · Investment hypotheses · SWOT · Problem & product · Traction & KPIs
   - **Optional:** Team & history · Technology & defensibility · Market sizing · Competition · Financials & round structure · Cap table · Due diligence log · Exit perspective
4. Flag missing data as `not_disclosed` — never fabricate ARR, cap table, or P&L.
5. Store structured JSON in `memos`; every claim has Trust Score + evidence locator.

**API:** `POST /skills/generate-memo/run` · wraps `POST /opportunity/{id}/analyze`
