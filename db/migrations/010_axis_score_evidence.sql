-- 010 — Persist evidence/disclosure on axis scores (was silently dropped
-- on every fetch — always-disclosed network contributions need to survive
-- a page refresh, not just the immediate /analyze response).
alter table opportunity_axis_scores add column if not exists evidence jsonb not null default '[]';
