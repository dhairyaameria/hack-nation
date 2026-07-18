# 15 — Mock Fixtures (Wave 1 Frontend)

**Owner:** Agent E (consumer) · Agent A/C (keep shapes in sync)  
**Purpose:** let the dashboard ship in Wave 1 **before** real APIs exist. Fixtures must match `01-CONTRACTS.md` Pydantic shapes exactly.

---

## 1. Location

```
shared/fixtures/
  pipeline-dashboard.json      # GET /opportunities (list)
  opportunity-detail.json      # GET /opportunity/{id} aggregate
  founder-profile.json         # GET /founders/{id}
  thesis-active.json           # GET /thesis/active
  network-graph-seed.json      # copy of 09-NETWORK-GRAPH-UI §8 (GraphQL shape)
```

Agent E imports from `shared/fixtures/` in Next.js (path alias `@/shared/fixtures` or relative `../../../shared/fixtures`).

Swap to live API in Wave 2 (`08-IMPLEMENTATION-PLAN.md` task 2.E) — delete mocks only after Gate G2.

---

## 2. Usage pattern

```typescript
// apps/web/lib/api/opportunities.ts
const USE_FIXTURES = process.env.NEXT_PUBLIC_USE_FIXTURES !== "false";

export async function getPipeline() {
  if (USE_FIXTURES) {
    return (await import("@/../../shared/fixtures/pipeline-dashboard.json")).default;
  }
  return fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/opportunities`).then(r => r.json());
}
```

Default: fixtures **on** until Wave 2. Set `NEXT_PUBLIC_USE_FIXTURES=false` when API is live.

---

## 3. `pipeline-dashboard.json` shape

```json
{
  "active_thesis": {
    "id": "thesis-ai-infra-eu",
    "name": "Pre-seed AI Infra EU"
  },
  "opportunities": [
    {
      "id": "opp-alex-inbound",
      "company_name": "Rivera Labs",
      "founder_name": "Alex Rivera",
      "founder_id": "founder-a-cold-start-strong",
      "source": "inbound",
      "discovery_channel": "direct_apply",
      "triggering_signal": null,
      "screen_verdict": "pass",
      "thesis_fit_score": 0.91,
      "status": "screening",
      "axis_scores": [
        { "axis": "founder", "value": 0.84, "trend": "improving", "confidence": 0.88, "evidence": [] },
        { "axis": "market", "value": "bullish", "trend": "stable", "confidence": 0.72, "evidence": [] },
        { "axis": "idea_vs_market", "value": 0.76, "trend": "improving", "confidence": 0.70, "evidence": [] }
      ],
      "sla": {
        "signal_at": "2026-07-18T10:00:00Z",
        "screening_at": "2026-07-18T10:45:00Z",
        "diligence_at": null,
        "decision_at": null
      }
    },
    {
      "id": "opp-jordan-outbound",
      "company_name": "Lee Analytics",
      "founder_name": "Jordan Lee",
      "founder_id": "founder-b-network-heavy-weak",
      "source": "outbound",
      "discovery_channel": "network_proximity",
      "triggering_signal": "2-hop path to Sequoia via co-author",
      "screen_verdict": "pass",
      "thesis_fit_score": 0.58,
      "status": "screening",
      "axis_scores": [
        { "axis": "founder", "value": 0.41, "trend": "stable", "confidence": 0.65, "evidence": [] },
        { "axis": "market", "value": "neutral", "trend": "declining", "confidence": 0.55, "evidence": [] },
        { "axis": "idea_vs_market", "value": 0.38, "trend": "stable", "confidence": 0.50, "evidence": [] }
      ],
      "sla": { "signal_at": "2026-07-18T09:00:00Z", "screening_at": null, "diligence_at": null, "decision_at": null }
    },
    {
      "id": "opp-contradiction",
      "company_name": "NovaMetrics",
      "founder_name": "Elena Vasquez",
      "founder_id": "founder-contradiction",
      "source": "inbound",
      "discovery_channel": "direct_apply",
      "triggering_signal": null,
      "screen_verdict": "pass",
      "thesis_fit_score": 0.79,
      "status": "diligence",
      "has_contradiction": true,
      "axis_scores": [],
      "sla": { "signal_at": "2026-07-18T08:00:00Z", "screening_at": "2026-07-18T08:30:00Z", "diligence_at": "2026-07-18T09:15:00Z", "decision_at": null }
    }
  ]
}
```

**UI rules enforced in fixture:**
- Three separate `axis_scores` entries — no composite field
- Alex Founder axis (0.84) > Jordan (0.41)
- `has_contradiction: true` drives banner on detail view

---

## 4. `opportunity-detail.json` (for `opp-contradiction`)

Must include:

- `claims[]` with `ClaimTrust` shape
- At least one claim with `validation_status: "contradicted"`
- `memo.sections[]` with one section flagged `not_disclosed: true`
- `trace_id` placeholder for drill-down link

Minimal contradicting claim:

```json
{
  "claim_id": "claim-arr-500k",
  "text": "We are at $500K ARR",
  "trust_score": 0.22,
  "validation_status": "contradicted",
  "evidence": [
    {
      "source_type": "deck",
      "source_locator": "slide 8",
      "evidence_snippet": "We are at $500K ARR",
      "confidence": 0.95
    },
    {
      "source_type": "web",
      "source_locator": "https://producthunt.com/posts/novametrics",
      "evidence_snippet": "Pre-revenue — 12 design partners",
      "confidence": 0.88
    }
  ]
}
```

---

## 5. `founder-profile.json`

Include:

- `genome` — 5 dimensions + trends (match `14-SEED-DATA-SPEC.md` targets for Alex)
- `founder_score_history[]` — time series
- `domain_affinity[]`
- `network_proximity` — score + mandatory `disclosure` string
- `network_graph_founder_id` — slug for graph component

---

## 6. Sync rules

| Event | Action |
|---|---|
| Contract shape changes in `01-CONTRACTS.md` | Update fixtures + `shared/schemas` in same PR |
| Seed slug renamed in `14-SEED-DATA-SPEC.md` | Update fixtures + network JSON |
| Real API endpoint lands | Point one screen at API; keep fixture until full Gate G2 |

---

## 7. Acceptance (Agent E, Wave 1)

- [ ] Dashboard renders 3+ cards from `pipeline-dashboard.json`
- [ ] Three axis cards on detail — no averaged score anywhere
- [ ] Contradiction banner visible on NovaMetrics detail fixture
- [ ] Founder profile shows Genome radar + separate network badge
- [ ] Thesis name shown in dashboard header from `thesis-active.json`
- [ ] Toggle `NEXT_PUBLIC_USE_FIXTURES=false` documented for Wave 2 cutover
