---
name: verify-claim
description: >-
  Re-run the Validator agent on a single claim. Use when an investor asks whether a deck
  assertion (ARR, traction, team) is trustworthy.
---

# Verify Claim

1. Load claim by `claim_id` from `claims` + linked evidence.
2. Run Validator Agent: Tavily + Perplexity cross-check, internal consistency.
3. Output `ClaimTrust`: status (`verified|contradicted|weakly_supported|unknown`), trust_score, evidence list.
4. Write `claim_validations` + `reasoning_traces`.

**Never** upgrade status without at least one external citation or explicit "unknown".

**API:** `POST /skills/verify-claim/run` · **Output:** `ClaimTrust` schema from `01-CONTRACTS.md`
