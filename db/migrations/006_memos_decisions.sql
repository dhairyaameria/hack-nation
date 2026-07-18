-- 006 — Memos and decision log (with 24h SLA timestamps)
-- See docs/04-INTELLIGENCE-TRUST.md, docs/07-EXECUTION.md §7 demo script.

create table if not exists memos (
  id              uuid primary key default gen_random_uuid(),
  opportunity_id  uuid not null references opportunities(id) on delete cascade,
  sections        jsonb not null default '[]',  -- [{ title, content, not_disclosed }]
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists idx_memos_opportunity on memos (opportunity_id);

create table if not exists decision_log (
  id              uuid primary key default gen_random_uuid(),
  opportunity_id  uuid not null references opportunities(id) on delete cascade,
  recommendation  text,             -- yes | no | needs-more-info
  confidence      numeric check (confidence >= 0 and confidence <= 1),
  key_unknowns    jsonb not null default '[]',
  bull_summary    text,
  bear_summary    text,
  signal_at       timestamptz,
  screening_at    timestamptz,
  diligence_at    timestamptz,
  decision_at     timestamptz,
  created_at      timestamptz not null default now()
);
create index if not exists idx_decision_opportunity on decision_log (opportunity_id);
