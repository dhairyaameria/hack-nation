---
name: screen-opportunity
description: Fast first-pass screen on an opportunity — pass, reject, or needs-more-info with one-line reason.
---

# Screen Opportunity

1. Cheap LLM/heuristic pass before full 3-axis pipeline.
2. Output: `pass | reject | needs-more-info` + reason.
3. Log to `reasoning_traces`.

**API:** `POST /skills/screen-opportunity/run`
