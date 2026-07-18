---
name: founder-genome-lookup
description: Return Founder Genome dimensions, trends, evidence, and Founder Score history for a founder.
---

# Founder Genome Lookup

1. Load `founder_genome_snapshots` + `founder_score_history`.
2. Return dimensions: execution velocity, technical depth, resilience proxy, public footprint depth.
3. Include network embeddedness separately with disclosure text (capped signal).
4. For cold-start founders, show confidence intervals and explicit "unknown" gaps.

**API:** `POST /skills/founder-genome-lookup/run` · input: `founder_id`
