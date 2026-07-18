---
name: thesis-sourcing-sweep
description: >-
  Run Perplexity research from the active fund thesis to discover new founder/company leads
  with citations. Use for outbound sourcing and "find me more like this" queries.
---

# Thesis Sourcing Sweep

1. Load active thesis from `thesis_profiles` (sectors, stage, geography, check size, risk).
2. Build structured Perplexity queries (launches, hiring, hackathons, community mentions).
3. Call Perplexity API; extract answer + native citations.
4. Ingest each lead via `ingest_raw(source="perplexity", ...)` — watchlist candidates only, not pre-trusted.
5. Return ranked leads with `EvidenceRef` per citation URL.

**API:** `POST /skills/thesis-sourcing-sweep/run` · **Tools:** Perplexity, Supabase Bronze
