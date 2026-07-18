---
name: vc-agent-router
description: >-
  Route investor natural-language questions to the correct VC Brain Cursor skill(s).
  Use when the user asks an ad-hoc diligence, sourcing, or memo question in VC Agent Chat.
---

# VC Agent Router

Map investor questions to one or more project skills under `.cursor/skills/`.

## Routing rules

| Question pattern | Skill(s) |
|---|---|
| ARR, revenue, traction claim doubt | `verify-claim` |
| Find founders like X, more deals like this | `thesis-sourcing-sweep`, `founder-genome-lookup` |
| Market size, competitors, comparables | `memo-research` |
| Full memo or investment write-up | `generate-memo` |
| Founder profile, Genome, cold-start | `founder-genome-lookup` |
| Network, who they know, 2nd degree | `network-proximity-check` |
| Old website, dead company, history | `wayback-history` |
| Pass or reject quickly | `screen-opportunity` |
| Best sourcing channels | `channel-quality-report` |
| Compare two startups | `compare-opportunities` |

## Output contract

- List chosen skill name(s)
- If no skill matches, respond: "No matching Cursor skill — cannot answer without evidence."
- Never answer factual claims without invoking a skill that returns `EvidenceRef` citations
