# 11 — Entity Model (Founder · Company · Opportunity · Thesis)

**Purpose:** clarify how profiles relate before anyone writes migrations.

---

## 1. Entity relationship diagram

```text
                    thesis_profiles
                    (VC / fund lens)
                           │
                           │ filters ranking + sourcing
                           ▼
    founders ────── founder_company_roles ────── companies
        │              (role, dates)                │
        │                                           │
        ├── founder_score_history                   │
        ├── founder_genome_snapshots                │
        ├── founder_confidence_intervals            │
        ├── domain_affinity[]  ◄── inferred from    │
        │    past companies + Genome                │
        ├── network_proximity_scores                │
        │                                           │
        └──────────── opportunities ◄───────────────┘
                    (one funding case)
                           │
              ├── claims ── claim_evidence_links ── evidence
              ├── opportunity_axis_scores (3 axes, NOT averaged)
              ├── memos
              ├── decision_log (SLA timestamps)
              └── watchlist_entries (if outbound-sourced)
```

---

## 2. Entity definitions

### `founders` — the person (persistent)
- Unified identity across GitHub, LinkedIn, deck, Wayback
- **Never resets** when they start a new company
- Key fields: `id`, `display_name`, `primary_email`, `location`, `domain_affinity[]`, `created_at`

### `founder_genome_snapshots` — capability profile (persistent, time-series)
- Dimensions: `execution_velocity`, `technical_depth`, `resilience_proxy`, `public_footprint_depth`, `network_embeddedness`
- Each with: `value`, `trend`, `confidence`, `evidence_refs[]`
- UI: radar chart on `/founders/[id]`

### `founder_score_history` — credit score for founders (persistent)
- One input to Founder axis; **not** a substitute for 3-axis Founder score
- Full time series; grows with every application/milestone

### `domain_affinity[]` — what kinds of companies they build (inferred)
- Array of `{ sector, weight, confidence, evidence_source }`
- Inferred from: past `founder_company_roles`, Wayback narratives, GitHub repos, deck history
- Used for: "find founders like this", NL queries, thesis fit on **founder-market fit**
- **Not** a hard filter alone — evidence-linked, confidence-qualified

### `companies` — a venture
- `id`, `name`, `domain`, `sector`, `stage`, `description`, `status` (`active` | `dead` | `acquired`)
- One founder may link to many companies over time

### `founder_company_roles` — builder history
- `founder_id`, `company_id`, `role` (CEO, CTO, cofounder…), `start_date`, `end_date`
- Powers: Genome resilience, domain_affinity, network graph, Wayback context

### `opportunities` — one investment decision instance
- Links: `founder_id`, `company_id`, `thesis_profile_id` (active at time of analysis)
- `source`: `inbound` | `outbound`
- `discovery_channel`, `screen_verdict`, `status` (pipeline stage)
- **3-axis scores live here** (per opportunity, not per founder)

### `thesis_profiles` — VC / fund profile (filters company types)
- See `docs/12-THESIS-SETTINGS-UI.md` for full schema
- Multiple profiles per fund; one `is_active` at a time

---

## 3. Lifecycle: founder applies with new company

```text
1. POST /application/submit { deck, company_name }
2. resolve_founder(deck + optional email) → founders.id (merge or create)
3. upsert companies row
4. insert founder_company_roles
5. create opportunities row (links founder + company + active thesis)
6. parse deck → claims with slide locators
7. fast screen → screen_verdict on opportunity
8. if pass → POST /opportunity/{id}/analyze
   ├── load founder_genome_snapshots + domain_affinity → Founder axis
   ├── load company + market research → Market axis
   └── Idea-vs-Market axis
9. validator → memo → decision_log
10. append founder_score_history (Founder Score update from this milestone)
11. recompute domain_affinity[] if new sector evidence
```

Outbound path converges at step 6+ via same screening code after `applied` state.

---

## 4. Founder profile vs opportunity scores (FAQ #6)

| | Founder profile | Opportunity analysis |
|---|---|---|
| Scope | Person across all ventures | This deck / this company |
| Key metrics | Genome, Founder Score, domain_affinity | 3-axis scores, memo, decision |
| Resets? | Never | N/A (new row per deal) |
| Relationship | Founder Score **feeds** Founder axis | Founder axis **includes** but is not equal to Founder Score |

---

## 5. Seed data requirements (Agent A)

Minimum entities for demo (see `02-DATA-FOUNDATION.md`, full catalog in **`14-SEED-DATA-SPEC.md`**):

| Seed entity | Purpose |
|---|---|
| 2 thesis profiles | Live thesis-switch demo |
| Bias-test founder pair | Execution vs network proximity |
| 1 contradiction opportunity | Validator demo |
| 1 dead company + Wayback | Resilience / domain_affinity |
| Network graph nodes/edges | Graph UI + proximity |
| 2–3 deck PDFs | Inbound flow |

---

## 6. API quick reference

| Need | Endpoint |
|---|---|
| Active thesis | `GET /thesis/active` |
| Submit application | `POST /application/submit` |
| Analyze opportunity | `POST /opportunity/{id}/analyze` |
| Founder Genome | `POST /skills/founder-genome-lookup/run` |
| Filtered founder list | GraphQL `topFounderMatches(thesis: …)` |
