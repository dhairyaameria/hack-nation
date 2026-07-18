# 10 — Filtering Funnel (How Companies Get Filtered)

**Read this before building.** Consolidates filtering logic spread across the PRD into one judge- and engineer-friendly reference.

---

## 1. Two profiles, one opportunity

Every investment case involves **two persistent lenses** plus a **per-deal instance**:

```text
THESIS PROFILE (VC / fund)          FOUNDER PROFILE (person)
thesis_profiles                     founders + founder_genome_snapshots
"what companies we want"            "who is building + what they've built before"
         │                                    │
         └──────────────┬─────────────────────┘
                        ▼
                 OPPORTUNITY (this deck, this company, this decision)
                 opportunities + opportunity_axis_scores + memos
```

| Object | Filters | Persists? |
|---|---|---|
| **Thesis profile** | Sector, stage, geo, check size, ownership, risk, exclusions | Versioned; swappable |
| **Founder profile** | Genome dimensions, Founder Score, domain_affinity, past companies | Never resets |
| **Opportunity** | 3-axis scores, claims, memo, decision | Per deal |

**Hard rule:** never average the three opportunity axes into one number.

---

## 2. End-to-end funnel

```text
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 0: THESIS (VC profile) — applies to ALL stages below       │
│ sectors · stage · geo · check · ownership · risk · exclusions    │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
   INBOUND                                      OUTBOUND
   deck + company name                          GitHub, PH, arXiv,
        │                                       Perplexity sweep
        ▼                                           │
   LAYER 1: FAST SCREEN                             │
   pass | reject | needs-more-info                 │
        │                                           ▼
        │                                    WATCHLIST
        │                                    weak → stay discovered
        │                                    strong + corroborated → promote
        │                                           │
        └───────────────────┬───────────────────────┘
                            ▼
                   LAYER 2: 3-AXIS SCORING
                   Founder (uses Genome + thesis)
                   Market (bullish|neutral|bear)
                   Idea-vs-Market (pivot tolerance)
                            │
                            ▼
                   LAYER 3: DILIGENCE + VALIDATOR
                   claim cross-check, contradictions flagged
                            │
                            ▼
                   LAYER 4: MEMO + TRUST (per claim)
                            │
                            ▼
                   DECISION ($100K yes/no + SLA timer)
```

---

## 3. Layer 0 — Thesis profile (VC filter on company type)

**Table:** `thesis_profiles` · **Owner:** Agent D · **UI:** `docs/12-THESIS-SETTINGS-UI.md`

| Field | Filters what |
|---|---|
| `sectors[]` | Company/founder domain (AI infra, devtools…) |
| `stage` | Pre-seed, seed, etc. |
| `geography` | Where company/founder operates |
| `check_size_usd` | Round size fit ($100K default) |
| `ownership_target_pct` | Cap table / dilution expectations |
| `risk_appetite` | `conservative` \| `balanced` \| `aggressive` |
| `exclude_sectors[]` | Hard no (optional) |
| `require_signals[]` | Must-have signals e.g. `enterprise_traction` (optional) |
| `watchlist_promotion_threshold` | How strong outbound signals must be to promote |

**Where thesis applies:**

| Stage | Effect |
|---|---|
| Outbound Perplexity sweep | Query built from active thesis |
| Watchlist promotion | Threshold from thesis.risk + thesis.require_signals |
| Pipeline ranking | Companies ranked by thesis fit score |
| NL query | Compound query AND thesis both apply |
| Memo | Risk-averse thesis → bear case weighted higher |

**Demo:** switch active thesis → dashboard re-orders live.

---

## 4. Layer 1 — Discovery + fast screen

### Outbound (Agent B)
- Weak/isolated signals → `watchlist` only (`discovered` / `scored`)
- Promotion requires **multiple corroborating signals** crossing thesis threshold
- `promoted_via` tag: `network_proximity`, `github_velocity`, `multi_signal`, etc.

### Inbound (Agent B)
- **No pre-filter on who applies** — deck + company name minimum
- Deck → structured `claims`

### Fast screen (Agent B, skill: `screen-opportunity`)
- Cheap pass before expensive pipeline
- Output: `pass` \| `reject` \| `needs-more-info` + one-line reason
- Only `pass` (and optionally `needs-more-info`) continue

---

## 5. Layer 2 — 3-axis scoring (main analysis filter)

**Owner:** Agent C · **Never averaged.**

| Axis | Primary inputs | Output |
|---|---|---|
| **Founder** | Founder Genome, Founder Score, domain_affinity, capped network_embeddedness | Score + trend + confidence |
| **Market** | TAM/SAM, competitors, timing, thesis sector fit | `bullish` \| `neutral` \| `bear` + trend |
| **Idea-vs-Market** | Idea defensibility vs team pivot strength | Score + trend + confidence |

**Founder axis uses founder profile; Market/Idea axes use this opportunity's company/deck.**

### Cold-start path
Founders with no GitHub/funding/accelerator history:
- Separate scoring via public footprint + Wayback + capped network proximity
- Missing signal = `unknown`, not automatic reject
- See `03-SOURCING.md` §4 and bias-test pair in seed data

---

## 6. Layer 3 — Validator (quality filter)

**Owner:** Agent C · **Skill:** `verify-claim`

Every claim checked before memo publish:
- `verified` \| `contradicted` \| `weakly_supported` \| `unknown`
- Contradictions surfaced **before** investor reads memo
- Seeded demo case: deck ARR vs public signals

---

## 7. Layer 4 — Trust Score (per-claim filter)

Trust Score is **per claim**, not per company:
- Source reliability × corroboration × recency × validator outcome
- UI heatmap: green / yellow / red by claim category

---

## 8. Ad-hoc filters (on top of standing thesis)

| Mechanism | Endpoint / skill | Example |
|---|---|---|
| NL compound query | `POST /query/natural-language` | "technical founder, Berlin, AI infra, no prior VC" |
| VC Agent Chat | `POST /agent/message` + Cursor skills | "Find me 3 more like this founder" |
| GraphQL | `topFounderMatches(thesis: …)` | Thesis-filtered founder list |

Each result explains **why** each clause matched — not silent pass/fail.

---

## 9. What does NOT filter companies

| Anti-pattern | Why forbidden |
|---|---|
| Single averaged score | Brief FAQ #5 — hides axis disagreement |
| Network proximity alone | Capped ~15%; execution can outrank connections |
| Fabricated missing data | Flag `not_disclosed`; never guess |
| Hardcoded thesis | Brief FAQ #15 — must be configurable |

---

## 10. Implementation ownership

| Funnel layer | Agent | Key tables / endpoints |
|---|---|---|
| Thesis | D | `thesis_profiles`, `/thesis` |
| Fast screen + watchlist | B | `watchlist_entries`, `/application/submit` |
| 3-axis | C | `opportunity_axis_scores`, `/opportunity/{id}/analyze` |
| Validator + Trust | C | `claim_validations`, `claim_evidence_links` |
| NL + Agent Chat | D | `/query/natural-language`, `/agent/message` |
| Founder profile | A + B | `founders`, `founder_genome_snapshots`, `domain_affinity` |

See `docs/11-ENTITY-MODEL.md` for entity relationships.
