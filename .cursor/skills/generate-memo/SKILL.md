---
name: generate-memo
description: Produce a full investment memo with required sections, gap flags, and per-claim Trust Scores.
---

# Generate Memo

1. Load opportunity + claims + axis scores from Memory.
2. Invoke Primary → Validator → Referee pipeline (Agent C).
3. Render required sections: snapshot, hypotheses, SWOT, problem/product, traction/KPIs.
4. Flag missing optional sections as `not_disclosed` — never fabricate.
5. Store structured JSON in `memos`; every claim has Trust Score + evidence locator.

**API:** `POST /skills/generate-memo/run` · wraps `POST /opportunity/{id}/analyze`
