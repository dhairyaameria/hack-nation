---
name: compare-opportunities
description: Side-by-side comparison of two or more opportunities on 3-axis scores and trust — never averaged.
---

# Compare Opportunities

1. Load `opportunity_axis_scores` for each ID (Founder, Market, Idea-vs-Market separately with trends).
2. Load top claims + Trust Scores per opportunity.
3. Present comparison table — **no composite score**.

**API:** `POST /skills/compare-opportunities/run` · input: `opportunity_ids[]`
