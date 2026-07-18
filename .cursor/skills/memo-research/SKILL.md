---
name: memo-research
description: Gather market sizing, competitor clusters, and comparable funding rounds with citations for memo generation.
---

# Memo Research

1. Accept `company_id` or `opportunity_id`.
2. Perplexity: market size, competitors, recent rounds in sector/geo.
3. Tavily: corroborate top claims.
4. Return structured research bundle with `EvidenceRef` per fact — feed into `generate-memo`.

**API:** `POST /skills/memo-research/run`
