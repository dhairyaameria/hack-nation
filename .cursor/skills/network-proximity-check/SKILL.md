---
name: network-proximity-check
description: Traverse 2nd-degree founder network to anchor nodes; return paths and mandatory disclosure.
---

# Network Proximity Check

1. GraphQL `networkProximity(founderId, anchorTags)`.
2. Return paths: anchor → via-node → founder with edge types.
3. Always include disclosure: network proximity reflects connections, not demonstrated capability.
4. Use for sourcing attention; capped weight if touching Founder axis score.

**API:** `POST /skills/network-proximity-check/run`
