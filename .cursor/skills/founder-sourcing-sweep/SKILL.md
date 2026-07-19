---
name: founder-sourcing-sweep
description: Run Perplexity (+ Tavily) founder-centric research from the active fund thesis to discover named founders with citations. Use for Founder Book sourcing.
---

# Founder Sourcing Sweep

1. Load the active thesis (sectors, stage, geography).
2. Run 3 founder-first Perplexity queries (technical founders, second-time/resilient, accelerator/research).
3. Optionally corroborate each query with Tavily web search.
4. Extract named founder + company pairs; land on watchlist with enrichment + Gold genome refresh.
5. Return leads with citations — never treat as pre-trusted facts.

**API:** `POST /skills/founder-sourcing-sweep/run` · input: optional `thesis_id`
