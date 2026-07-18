---
name: wayback-history
description: Reconstruct company narrative from Wayback snapshots; sentiment trajectory and narrative drift.
---

# Wayback History

1. Fetch CDX index for company domain(s).
2. Select representative snapshots; extract positioning claims.
3. Label narrative: `stable | pivoted | inconsistent`.
4. Cross-check archived vs current claims; flag contradictions for validator.

**API:** `POST /skills/wayback-history/run` · input: `company_id` or `domain`
