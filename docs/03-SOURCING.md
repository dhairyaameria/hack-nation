# 03 — Sourcing & Ingestion (Agent B)

**Owner:** Agent B — Sourcing
**Depends on:** Agent A's schema + `ingest_raw`/`resolve_founder` helpers.
**PRD sections covered:** §7.4, §7.5, §10 (all), §17 (GraphQL resolvers), stretch goal §12.3.

**This is the highest-weighted workstream.** Per the brief: "If we can only nail one thing, sourcing wins... Build sourcing deep, then a thin-but-transparent Intelligence layer over it."

---

## Mission

Discover strong founders before they fundraise (outbound), accept minimal-friction applications (inbound), converge both into ONE screening funnel, and handle the cold-start founder as a first-class case.

## 1. Inbound Application

- `POST /application/submit`: `deck` (file → Supabase Storage) + `company_name`. Optional contact email only. **Do not add more required fields.**
- Deck parser: extract structured claims (team, problem, product, traction, market, ask) into `claims` with slide-number locators.
- Fast first-pass screen: cheap heuristic/LLM pass → `pass / reject / needs-more-info` + one-line reason, BEFORE the expensive 3-axis pipeline.

## 2. Outbound Connectors (build in this order)

1. **GitHub:** repo growth, commit consistency, contributor role, issue-response quality, release cadence.
2. **Launch/community (pick one):** ProductHunt or Hacker News — traction, technical audience engagement.
3. **arXiv:** relevance + paper→code follow-through.
4. **Hackathon/accelerator cohorts:** scraped or synthesized lists; finalist/winner frequency, domain consistency.

All connectors write to Bronze via `ingest_raw` with full provenance, then trigger entity resolution.

## 3. Watchlist State Machine

`discovered → scored → activation-candidate → outreach-sent → applied → screening`

- Weak/isolated signals stay at `discovered`/`scored` (watchlist only).
- Promotion to `activation-candidate` requires multiple independent corroborating signals crossing the conviction threshold (threshold parameterized by active thesis).
- **Activation:** generate an outreach artifact (templated email/DM draft, evidence-linked to the triggering signal). Doesn't need to actually send.
- **Convergence (required):** `applied` and `screening` states share the exact same code path as native inbound applications.
- `promoted_via` reason tag recorded on every promotion (e.g., `network_proximity`, `github_velocity`, `multi_signal`).

## 4. Cold-Start Founder Path (scoring-critical — judges check this)

For founders with no GitHub/funding/accelerator history:
- Score from public-footprint signals: writing quality/depth on personal sites/blogs, hackathon participation (not just wins), small consistent OSS contributions, community engagement showing technical judgment.
- Absence of signal = "unknown", never "bad". Output is confidence-qualified.
- Wayback history (below) and network proximity (below) are additional cold-start levers.

## 5. Network Proximity (Founder Genome network dimension)

Build the graph + traversal; Agent C consumes the score, Agent E renders it.

- **Nodes:** `Founder|VC|Accelerator|Institution|Company`. **Edges:** `FOLLOWS|CO_CONTRIBUTED|CO_AUTHORED|CO_PARTICIPATED|ALUMNI_OF|MENTIONED_BY`.
- **Anchor set:** curated `network_anchor_tags` (notable founders, tier-1 VCs, top accelerators) — seed ~20-30 anchors.
- 2nd-degree traversal → `network_proximity_scores`: `path_count`, `path_diversity` (distinct anchors > many paths to one), `edge_recency`, `edge_type_strength` (collaboration > passive follow). Output `proximity_score` (0-1) + confidence + actual paths as evidence.
- Implement the `networkProximity` GraphQL query (contract in `01-CONTRACTS.md` §3) including the mandatory `disclosure` string.

**Binding constraints (from OVERVIEW rules):** sourcing/attention use primarily; if it touches scoring, capped ~10-15% of Founder axis, separately labeled, always disclosed. Watchlist promotion via proximity gets `promoted_via: network_proximity`.

## 6. Wayback Historical Intelligence

- Wayback CDX API: fetch snapshot index for company domains/aliases; select representative snapshots over time.
- Extract historical positioning/product claims; compute sentiment + narrative trajectory (`stable | pivoted | inconsistent`).
- Cross-reference archived claims vs current claims → feed contradictions to Agent C's validator.
- Store `wayback_snapshots` + `wayback_sentiment_timeseries` with retrieval metadata. Respect rate limits; cache aggressively.

## 7. Sourcing & Channel Intelligence (Stretch Goal 3)

- Track `DISCOVERED_VIA` channel for every opportunity.
- Channel quality score: conversion rate to funded deal × post-funding quality proxy × sample-size confidence, with exploration bonus for under-sampled channels.
- Feedback loop: decision outcomes (from Agent C's `decision_log`) update channel priors.
- Serve `GET /channels/quality` + `ChannelQuality` GraphQL query, including underexplored-channel suggestions with rationale.

## 8. GraphQL Resolvers

Implement all queries in `01-CONTRACTS.md` §3 (reads Agent A's tables): `TopFounders`, `FounderNetwork`, `CompanyHistory`, `ChannelQuality`, `NetworkProximity`. Support filters: timeframe, geography, sector, confidence threshold.

## Acceptance Checks

- [ ] Inbound deck + company name → parsed claims with slide locators → fast screen verdict.
- [ ] At least 2 outbound connectors landing provenance-tagged Bronze records.
- [ ] Watchlist entry promoted via multi-signal corroboration; outreach artifact generated and evidence-linked.
- [ ] Outbound-activated application flows through the same screening code path as inbound.
- [ ] Cold-start founder scored from public footprint with confidence qualifier.
- [ ] `networkProximity` returns real paths (anchor, via-node, edge types) + disclosure text for a seeded founder.
- [ ] Wayback timeline with sentiment/narrative-drift for at least one seeded company.
- [ ] Channel quality ranking + at least one underexplored suggestion.
