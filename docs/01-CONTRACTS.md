# 01 — Shared Contracts: Data Model, APIs, Conventions

**Status:** Binding interface document. All agents code against these contracts. Any change here must be announced to the whole team (it can break other workstreams). Additive changes (new optional fields, new endpoints) are safe; renames/removals are not.

---

## 1. Data Model (Supabase / Postgres)

Owner: **Agent A (Data)** implements the DDL; everyone else consumes.

### Core entities
- `founders`, `companies`, `founder_company_roles`, `opportunities`
- `thesis_profiles` — VC/fund profile: sectors, stage, geography, check size, ownership targets, risk appetite, exclude_sectors, require_signals, watchlist_promotion_threshold (see `12-THESIS-SETTINGS-UI.md`)

**`founders` key fields:** `id`, `display_name`, `primary_email`, `location`, `domain_affinity` (jsonb array: `{ sector, weight, confidence, evidence_source }` — inferred from past companies + Genome; see `11-ENTITY-MODEL.md`)

**`thesis_profiles` key fields:** full DDL in `12-THESIS-SETTINGS-UI.md`; `opportunities.thesis_profile_id` stores active thesis at analysis time

**`opportunities` deck + inbound rank fields** (migration `010`, see `19-INBOUND-RERANK.md`): `deck_url`, `deck_storage_path`, `deck_filename`, `inbound_rank`, `inbound_rank_rationale`, `inbound_ranked_at`, `inbound_rank_run_id`. `thesis_fit_score` is updated by inbound rerank; it is **not** a composite of the three axes.

### Scores & profiles
- `founder_score_history` — persistent Founder Score per founder, full time series, never resets
- `founder_confidence_intervals` — research track output (score + interval + evidence coverage)
- `opportunity_axis_scores` — founder / market / idea_vs_market, each row: value, trend (`improving|stable|declining`), confidence. NEVER a combined column.
- `founder_genome_snapshots` — per-dimension scores + trend: execution_velocity, technical_depth, resilience_proxy, public_footprint_depth, network_embeddedness

### Trust & evidence
- `claims` — extracted assertions (traction, revenue, team, market size...)
- `evidence` — source records: `source_type`, `source_locator`, `evidence_snippet`, `captured_at`, `url`
- `claim_evidence_links` — relation: `supports` | `contradicts`, with confidence
- `claim_validations` — validator output per claim: `status` (`verified|contradicted|weakly_supported|unknown`), `confidence_delta`, `contradiction_reason`, `required_followup`
- `contradiction_events`
- `reasoning_traces` — per pipeline stage: `stage`, `inputs_used` (IDs), `decision_rule_or_prompt_version`, `output_claim_ids`

### Memos & decisions
- `memos` — sections as structured JSON; missing sections flagged `not_disclosed`
- `decision_log` — includes signal-to-decision timestamps for the 24h SLA timer

### Sourcing
- `watchlist_entries` — state machine: `discovered → scored → activation-candidate → outreach-sent → applied → screening`; includes `promoted_via` reason tag (e.g. `network_proximity`)
- `channel_performance`, `channel_recommendations` — sourcing graph intelligence
- `wayback_snapshots`, `wayback_sentiment_timeseries`

### Network graph
- `network_nodes` — types: `Founder|VC|Accelerator|Institution|Company`
- `network_edges` — types: `FOLLOWS|CO_CONTRIBUTED|CO_AUTHORED|CO_PARTICIPATED|ALUMNI_OF|MENTIONED_BY`, with `weight`, `first_seen_at`
- `network_anchor_tags` — curated strong-signal nodes (notable founders, tier-1 VCs, top accelerators)
- `network_proximity_scores` — per founder: `path_count`, `path_diversity`, `edge_recency`, `proximity_score` (0-1), `confidence`, capped scoring-weight metadata

### Cursor Skills & VC Agent Chat
- `skill_definitions` — optional mirror of `.cursor/skills/*/SKILL.md` metadata for audit
- `skill_runs` — skill name, input params, data snapshot refs, output, citations, timestamp
- `chat_sessions`, `chat_messages` — VC Agent Chat conversations, each assistant message linked to its `skill_runs`

### Optional federated module
- `federated_rounds`, `federated_partner_updates`, `provenance_ledger` (hash-chained: `event_hash`, `prev_hash`, `entity_id`, `timestamp`, `source`)

### Provenance convention (every ingested record, every table fed by ingestion)
Required columns: `source`, `source_entity_id`, `fetched_at`, `run_id`.

---

## 2. REST API Contract (FastAPI)

Base path: `/api/v1`. All responses JSON. All factual payloads include evidence references where applicable.

| Endpoint | Method | Owner | Purpose |
|---|---|---|---|
| `/ingest/founder` | POST | A | Manual/connector ingestion entry |
| `/application/submit` | POST | B | Inbound: deck + company_name (minimum bar); stores `deck_url` / `deck_storage_path` |
| `/inbound/rerank` | POST | Arman | Perplexity rerank of all inbound vs active thesis (manual or cron; see `19-INBOUND-RERANK.md`) |
| `/inbound/ranked` | GET | Arman | Inbound list ordered by latest `inbound_rank` |
| `/opportunity/{id}/analyze` | POST | C | Runs 3-axis + memo pipeline |
| `/opportunity/{id}/memo` | GET | C | Structured memo (sections + gap flags) |
| `/opportunity/{id}/trust` | GET | C | Per-claim trust scores + evidence |
| `/validation/run/{opportunity_id}` | POST | C | Validator agent pass |
| `/recommendation/{id}/trace` | GET | C | Full reasoning trace |
| `/channels/quality` | GET | B | Channel quality ranking + underexplored suggestions |
| `/thesis` / `/thesis/{id}` | POST/GET/PUT | D | Thesis Engine CRUD |
| `/thesis/active` | GET | D | Current active thesis profile |
| `/thesis/{id}/activate` | POST | D | Set active thesis (deactivates others) |
| `/query/natural-language` | POST | D | Compound NL query, one pass, per-clause match explanations |
| `/agent/message` | POST | D | VC Agent Chat turn — routes to Cursor skills, returns evidence-linked answer |
| `/skills` / `/skills/{name}` | GET | D | Skill catalog + versioned definitions |
| `/skills/{name}/run` | POST | D | Direct skill execution |
| `/skill-runs/{id}` | GET | D | Inspect past run |
| `/skill-runs/{id}/rerun` | POST | D | Re-execute against fresh data + diff |
| `/research/confidence/{founder_id}` | GET | C | Confidence interval output |
| `/federated/round/*` | POST | (optional) | Federated module endpoints |

**Shared response shapes (Pydantic, kept in a shared `schemas/` package):**

```python
class EvidenceRef(BaseModel):
    source_type: str        # deck | web | interview | github | wayback | perplexity | ...
    source_locator: str     # slide number, URL, commit hash, transcript ts
    evidence_snippet: str
    confidence: float       # 0-1

class AxisScore(BaseModel):
    axis: Literal["founder", "market", "idea_vs_market"]
    value: float | str      # market axis may be bullish|neutral|bear
    trend: Literal["improving", "stable", "declining"]
    confidence: float
    evidence: list[EvidenceRef]

class ClaimTrust(BaseModel):
    claim_id: str
    text: str
    trust_score: float
    validation_status: Literal["verified", "contradicted", "weakly_supported", "unknown"]
    evidence: list[EvidenceRef]

class DomainAffinity(BaseModel):
    sector: str
    weight: float          # 0-1
    confidence: float      # 0-1
    evidence_source: str    # wayback | github | role_history | deck

class ThesisProfile(BaseModel):
    id: str | None = None
    name: str
    version: int = 1
    is_active: bool = False
    sectors: list[str]
    stage: Literal["pre_seed", "seed", "series_a"]
    geography: str
    check_size_usd: float
    ownership_target_pct: float | None = None
    risk_appetite: Literal["conservative", "balanced", "aggressive"]
    exclude_sectors: list[str] = []
    require_signals: list[str] = []
    watchlist_promotion_threshold: float = 0.65
```

---

## 3. GraphQL Contract (network layer)

Owner: **Agent B** implements resolvers (reads Agent A's tables); **Agent E** consumes.

Core types: `Founder`, `Company`, `Opportunity`, `Evidence`, `Claim`, `Relationship`, `ScoreSnapshot`, `Program`, `Institution`, `Channel`.

Required queries:

```graphql
query TopFounders($thesis: ThesisInput!, $limit: Int!) {
  topFounderMatches(thesis: $thesis, limit: $limit) {
    founderId
    founderScore
    trend
    keySignals
    companies { companyId role startDate endDate }
    networkStrength
  }
}

query FounderNetwork($founderId: ID!, $depth: Int!) {
  founderNetwork(founderId: $founderId, depth: $depth) {
    nodes { id type label confidence }
    edges { from to relationType weight firstSeenAt }
  }
}

query CompanyHistory($companyId: ID!) {
  companyHistory(companyId: $companyId) {
    waybackSnapshots { snapshotAt extractedSummary sentiment confidence }
    claims { text trustScore evidence { source url capturedAt } }
  }
}

query ChannelQuality {
  channelQuality {
    channelId name conversionToFundedRate
    sampleSizeConfidence isUnderexplored recommendationRationale
  }
}

# Founder Genome — 2nd-degree network proximity to anchor nodes
query NetworkProximity($founderId: ID!, $anchorTags: [String!]) {
  networkProximity(founderId: $founderId, anchorTags: $anchorTags) {
    proximityScore
    confidence
    disclosure       # mandatory plain-language disclosure string
    paths {
      anchorNode { id type label tags }
      viaNode { id type label }
      edgeTypes
      hopCount
      lastActiveAt
    }
  }
}
```

Graph queries must support filters: timeframe, geography, sector, confidence threshold.

---

## 4. Cursor Skills Contract

**Source of truth:** `.cursor/skills/<skill-name>/SKILL.md` (Cursor Agent Skills format with YAML frontmatter).

Runtime loader parses frontmatter and registers skills for the VC Agent router. Optional JSON mirror for audit:

```json
{
  "name": "verify-claim",
  "skill_path": ".cursor/skills/verify-claim/SKILL.md",
  "input_schema": { "claim_id": "string" },
  "tool_bindings": ["tavily", "perplexity", "db.claims"],
  "output_contract": "ClaimTrust"
}
```

Rules:
- Every execution logged as a `skill_run` (inputs, snapshot refs, output, citations, timestamp).
- Outputs must use the shared Pydantic shapes so the frontend renders them uniformly.
- Skills write into `reasoning_traces` like any pipeline stage.
- UI must display the **Cursor skill folder name** that ran (e.g. `verify-claim`).

Initial catalog (11 skills in `.cursor/skills/`): `thesis-sourcing-sweep`, `memo-research`, `generate-memo`, `verify-claim`, `founder-genome-lookup`, `network-proximity-check`, `wayback-history`, `screen-opportunity`, `channel-quality-report`, `compare-opportunities`, `vc-agent-router`. Full descriptions in `05-CURSOR-SKILLS.md`.

---

## 5. Repo Structure & Conventions

```
/apps/web          # Next.js frontend (Agent E)
/apps/api          # FastAPI + GraphQL (Agents B, C, D share; module-per-workstream)
  /api/ingestion   # Agent B
  /api/intelligence# Agent C
  /api/agent       # Agent D — Cursor Skills + VC Agent Chat
  /api/graphql     # Agent B
/shared/schemas    # Pydantic + TS types (generated or mirrored) — SINGLE SOURCE OF TRUTH
/shared/fixtures   # Wave 1 JSON mocks — see 15-MOCK-FIXTURES.md
/jobs/connectors   # outbound connectors, wayback, perplexity sweeps (Agent B)
/dbx               # Databricks notebooks/pipelines (Agent A)
/db/migrations     # Supabase SQL migrations (Agent A)
/docs              # these files
```

Conventions:
- Python 3.11+, Pydantic v2, type hints everywhere.
- All external API calls (GitHub, Perplexity, Tavily, Wayback) wrapped with retry + timeout + cached responses in Bronze — reruns must not hammer external APIs.
- Environment variables: copy `.env.example` → `.env` (never commit `.env`); see `13-PRE-BUILD-CHECKLIST.md`
- Seeded demo data lives in `/db/seed/` — includes synthetic founder profiles WITH seeded contradictions (required for the validator demo).
