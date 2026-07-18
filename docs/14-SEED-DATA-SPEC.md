# 14 — Seed Data Spec (Demo Catalog)

**Owner:** Agent A implements in `db/seed/`  
**Purpose:** one authoritative catalog so migrations, API, UI, and demo script all reference the **same IDs and stories**.

Use stable UUIDs below (or map slug → UUID in `seed.py`). Slugs are the cross-doc contract until UUIDs are assigned.

---

## 1. Thesis profiles (2)

From `12-THESIS-SETTINGS-UI.md` §6 — load exactly:

| slug | name | active | key difference |
|---|---|---|---|
| `thesis-ai-infra-eu` | Pre-seed AI Infra EU | **yes** | `exclude_sectors: ["crypto"]`, `require_signals: ["technical_founder"]`, threshold 0.65 |
| `thesis-devtools-us` | Aggressive US Seed DevTools | no | US seed devtools, threshold 0.45, aggressive risk |

---

## 2. Founders (minimum 10)

| slug | display_name | story | demo use |
|---|---|---|---|
| `founder-a-cold-start-strong` | Alex Rivera | High execution Genome, sparse network | **Bias test A** — must outrank B on Founder axis |
| `founder-b-network-heavy-weak` | Jordan Lee | Low execution, dense anchor paths | **Bias test B** — impressive graph, lower Founder axis |
| `founder-contradiction` | Elena Vasquez | NovaMetrics inbound deck | **Validator demo** — ARR contradiction |
| `founder-wayback-resilience` | Sam Okonkwo | Prior dead company DataPulse | Wayback + resilience + domain_affinity |
| `founder-established` | Priya Nair | 2 prior exits, strong public footprint | Established track record |
| `founder-established-2` | Marcus Chen | OSS maintainer, GitHub velocity | Outbound GitHub connector demo |
| `founder-cold-public-only` | Lina Hoffmann | No network, strong arXiv/GitHub | Cold-start public footprint path |
| `founder-cold-network-only` | Tomás Ruiz | Weak public signals, 2nd-degree to YC | Cold-start network proximity path |
| `founder-outbound-signal` | Aisha Khan | HN launch traction, not fundraising | Outbound → watchlist → apply |
| `founder-excluded-sector` | Crypto founder (name TBD) | Crypto sector company | Thesis `exclude_sectors` filter demo |

### Genome targets (latest snapshot)

| slug | execution_velocity | technical_depth | resilience_proxy | public_footprint | network_embeddedness |
|---|---|---|---|---|---|
| `founder-a-cold-start-strong` | 0.88 | 0.82 | 0.75 | 0.70 | **0.08** |
| `founder-b-network-heavy-weak` | 0.35 | 0.40 | 0.45 | 0.50 | **0.72** (capped in axis at ≤15%) |
| `founder-contradiction` | 0.72 | 0.68 | 0.60 | 0.65 | 0.25 |
| `founder-wayback-resilience` | 0.65 | 0.70 | **0.80** | 0.55 | 0.30 |

Network graph JSON for bias pair: `09-NETWORK-GRAPH-UI.md` §8 (IDs must match).

### domain_affinity[] (≥3 founders)

| slug | affinity examples |
|---|---|
| `founder-wayback-resilience` | `{ sector: "b2b_saas", weight: 0.7, evidence_source: "wayback" }`, `{ sector: "analytics", weight: 0.5, evidence_source: "role_history" }` |
| `founder-established` | `{ sector: "ai_infra", weight: 0.85, evidence_source: "role_history" }` |
| `founder-established-2` | `{ sector: "devtools", weight: 0.9, evidence_source: "github" }` |

---

## 3. Companies (minimum 8)

| slug | name | domain | sector | status | notes |
|---|---|---|---|---|---|
| `company-a` | Rivera Labs | riveralabs.dev | ai_infra | active | Alex's company |
| `company-b` | Lee Analytics | leeanalytics.io | analytics | active | Jordan's weak company |
| `company-novametrics` | NovaMetrics | novametrics.ai | ai_infra | active | Contradiction deck |
| `company-datapulse` | DataPulse | **datapulse.io** | b2b_saas | **dead** | Wayback CDX target |
| `company-outbound` | KernelDB | kerneldb.io | devtools | active | Aisha's HN launch |
| `company-crypto` | ChainVault | chainvault.xyz | **crypto** | active | Excluded by EU thesis |

---

## 4. Opportunities (minimum 6)

| slug | founder | company | source | screen_verdict | demo |
|---|---|---|---|---|---|
| `opp-alex-inbound` | Alex Rivera | Rivera Labs | inbound | pass | Bias test + strong pipeline card |
| `opp-jordan-outbound` | Jordan Lee | Lee Analytics | outbound | pass | Bias test + network graph |
| `opp-contradiction` | Elena Vasquez | NovaMetrics | inbound | pass | **Validator must catch ARR** |
| `opp-wayback` | Sam Okonkwo | new company | inbound | pass | Wayback resilience narrative |
| `opp-outbound-hn` | Aisha Khan | KernelDB | outbound | pass | Outbound signal → same funnel |
| `opp-crypto-excluded` | crypto founder | ChainVault | inbound | reject or low thesis_fit | Thesis exclusion demo |

Store `thesis_profile_id` = active thesis at analysis time on every opportunity.

---

## 5. Seeded contradiction (required)

**Opportunity:** `opp-contradiction` · **Company:** NovaMetrics

| claim_id (slug) | text (from deck) | deck locator | public evidence (contradicts) |
|---|---|---|---|
| `claim-arr-500k` | "We are at $500K ARR" | slide 8 | Product Hunt listing: "pre-revenue, 12 design partners" |
| `claim-customers-40` | "40 paying enterprise customers" | slide 9 | LinkedIn company page: "3 pilot customers" |

Validator must return `status: contradicted` for at least `claim-arr-500k`. Seed `claim_validations` + `contradiction_events` after first analyze run, or pre-seed for Wave 2 gate.

Deck file: `db/seed/decks/novametrics-deck.pdf` (Agent A generates or stubs 8–10 slides with the claims above).

---

## 6. Wayback seed (required)

**Domain:** `datapulse.io` (company-datapulse, status dead)

Seed 4–6 snapshots in `wayback_snapshots`:

| snapshot_at | narrative summary | sentiment |
|---|---|---|
| 2019-06 | "Consumer social analytics for influencers" | neutral |
| 2020-03 | "Pivoting to B2B dashboard for SMBs" | mixed |
| 2021-01 | "Sunsetting product — team exploring acqui-hire" | negative |

Narrative label: `pivoted`. Feed at least one archived claim that contradicts Sam's new deck positioning.

---

## 7. Network graph (~25 nodes)

Minimum set beyond bias pair (doc 09):

- 5+ nodes with `network_anchor_tags` (Sequoia, YC, Stanford, notable founder)
- Edges use contract types: `FOLLOWS`, `CO_CONTRIBUTED`, `CO_AUTHORED`, `CO_PARTICIPATED`, `ALUMNI_OF`, `MENTIONED_BY`
- `network_proximity_scores` rows for `founder-b-network-heavy-weak` and `founder-cold-network-only`

---

## 8. Founder Score history

Each established/cold-start founder: ≥3 `founder_score_history` rows with monotonic or explainable trend.

Alex (`founder-a-cold-start-strong`): rising trend (0.62 → 0.71 → 0.78) from GitHub velocity milestones.

---

## 9. Deck PDFs (`db/seed/decks/`)

| file | opportunity | must contain |
|---|---|---|
| `riveralabs-deck.pdf` | opp-alex-inbound | team, product, traction (modest, honest) |
| `novametrics-deck.pdf` | opp-contradiction | **$500K ARR claim on slide 8** |
| `kerneldb-deck.pdf` | opp-outbound-hn | devtools infra, HN launch reference |

Optional: `datapulse-founder-newco.pdf` for Wayback contrast.

---

## 10. Seed command contract

```bash
make db-reset   # drop + apply migrations (dev only)
make db-seed    # runs db/seed/seed.py — idempotent
```

After seed:

- `GET /thesis/active` → Pre-seed AI Infra EU
- Dashboard shows ≥5 opportunities with mixed inbound/outbound labels
- `founder-a-cold-start-strong` Founder axis > `founder-b-network-heavy-weak` (bias test)
- `opp-contradiction` has claims with locators; validator catches ARR on analyze

---

## 11. Acceptance (Agent A)

- [ ] All slugs in this doc exist in DB
- [ ] Bias pair IDs match `09-NETWORK-GRAPH-UI.md` fixture JSON
- [ ] Contradiction claims + contradicting evidence rows linked in `claim_evidence_links`
- [ ] 2 thesis profiles; exactly one active
- [ ] `domain_affinity` on ≥3 founders
- [ ] Wayback snapshots for `datapulse.io`
- [ ] Seed is idempotent (safe to re-run)
