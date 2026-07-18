# 02 — Data Foundation / Memory Layer (Agent A)

**Owner:** Agent A — Data
**Depends on:** `01-CONTRACTS.md` (implements its data model)
**Blocks:** every other workstream (schema must land first) — prioritize migrations on day one.
**PRD sections covered:** §7.2, §9, §16.2, §18, plus data-quality research track §13.2.

---

## Mission

Build the Memory layer: the deduplicated, enriched, timestamped, source-tagged data foundation where nothing is discarded, the Founder Score persists forever, and trend-over-time is queryable everywhere.

## Deliverables

1. **Supabase migrations** for the full data model in `01-CONTRACTS.md` §1, following file order in `16-MIGRATIONS-GUIDE.md`, including pgvector setup for deck-chunk embeddings and semantic evidence retrieval.
2. **Bronze/Silver/Gold lifecycle** (Databricks Delta tables, or Postgres-schema equivalents if Databricks time-boxes out — decide by end of Milestone 1):
   - **Bronze (raw):** exact payload as received + `source`, `source_entity_id`, `fetched_at`, `run_id`. Never mutated.
   - **Silver (normalized/linked):** canonical `founder`, `company`, `artifact` (repo/paper/deck/launch page), `event` (hackathon result, release, funding mention); dedup keys; source-level confidence.
   - **Gold (feature-ready):** founder feature vectors (velocity, depth, consistency, execution evidence), opportunity 3-axis inputs, claim↔evidence tables ready for the Trust layer. Gold syncs back into Supabase for the app.
3. **Entity resolution & deduplication service:**
   - Deterministic rules first: email/domain match, repo ownership, verified profile links.
   - LLM-assisted fuzzy matching for ambiguous cases (log the match rationale).
   - One founder profile unifies GitHub + LinkedIn + X + deck-stated identity + Wayback-derived history.
4. **Founder Score storage & history:**
   - Per founder (not per opportunity), full time series in `founder_score_history`, never resets.
   - Write API for the Intelligence workstream to append score updates; read API returns score + trend.
5. **Data quality weights** on every ingested field: `completeness`, `source_reliability`, `recency`. Sparse/low-confidence data flagged `low-confidence`, never silently used at face value.
6. **Seed dataset** in `/db/seed/` (see also `11-ENTITY-MODEL.md`, `12-THESIS-SETTINGS-UI.md`, **`14-SEED-DATA-SPEC.md`**):
   - Synthetic founder profiles (mix of: established track record, cold-start with public footprint only, cold-start with network proximity only).
   - At least one profile pair for the bias test (strong execution + zero network vs. weak execution + strong network).
   - **`domain_affinity[]`** on ≥3 founders (inferred from role history / Wayback).
   - **2 thesis profiles** (one active) from `12-THESIS-SETTINGS-UI.md` seed JSON.
   - **Seeded contradictions** (e.g., deck claims $500K ARR; public signals contradict) — the validator demo depends on this.
   - ~25 network nodes/edges incl. 5+ anchor-tagged nodes.
   - 2–3 fictional pitch decks (PDF) for inbound flow testing.

## Research Track Owned Here: Data Quality vs. Volume (PRD §13.2)

- Implement the collection-worthiness heuristic: prioritize sources with (a) independent corroboration potential, (b) low verification cost, (c) direct thesis relevance. De-prioritize high-volume/low-corroboration sources.
- Document the explicit thresholds for "low-confidence" vs. "usable" — goes into the submission notes.

## Interfaces You Provide to Other Agents

- Migrations applied + Supabase types available → unblocks everyone.
- `ingest_raw(source, payload, run_id)` helper → used by Agent B's connectors.
- Entity-resolution function `resolve_founder(candidate_identity) -> founder_id` → used by Agent B.
- Gold feature tables → consumed by Agent C (scoring) and Agent D (skills).
- `founder_score_history` append/read → used by Agent C.

## Acceptance Checks

- [ ] All tables from contracts doc exist with provenance columns enforced.
- [ ] A record ingested twice from two sources resolves to one founder profile with both sources linked.
- [ ] Bronze retains the raw payload byte-for-byte after Silver normalization.
- [ ] Founder Score history returns a time series with trend for a seeded founder.
- [ ] Seed data loads in one command and includes the contradiction cases + bias-test pair.
