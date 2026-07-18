---
name: channel-quality-report
description: Rank sourcing channels by quality; suggest underexplored channels with rationale.
---

# Channel Quality Report

1. Query `channel_performance` + decision outcomes feedback loop.
2. Rank by conversion quality, not volume; exploration bonus for under-sampled channels.
3. Return top channels + underexplored suggestions with rationale.

**API:** `GET /channels/quality` · skill wrapper: `POST /skills/channel-quality-report/run`
