-- 004 — Founder Score history, Genome snapshots, confidence intervals, 3-axis scores
-- HARD RULE: opportunity_axis_scores must never have a composite/overall column.
-- See docs/00-OVERVIEW.md §4 rule 1.

create table if not exists founder_score_history (
  id          uuid primary key default gen_random_uuid(),
  founder_id  uuid not null references founders(id) on delete cascade,
  score       numeric not null check (score >= 0 and score <= 1),
  confidence  numeric check (confidence >= 0 and confidence <= 1),
  reason      text,             -- what milestone triggered this update
  recorded_at timestamptz not null default now()
);
create index if not exists idx_founder_score_history on founder_score_history (founder_id, recorded_at desc);
-- append-only time series; unique on (founder_id, recorded_at) makes seed re-runs idempotent
-- without collapsing genuine history (each real update has a distinct timestamp).
create unique index if not exists uq_founder_score_history on founder_score_history (founder_id, recorded_at);

create table if not exists founder_genome_snapshots (
  id                       uuid primary key default gen_random_uuid(),
  founder_id               uuid not null references founders(id) on delete cascade,
  execution_velocity       numeric not null check (execution_velocity >= 0 and execution_velocity <= 1),
  execution_velocity_trend trend not null default 'stable',
  technical_depth          numeric not null check (technical_depth >= 0 and technical_depth <= 1),
  technical_depth_trend    trend not null default 'stable',
  resilience_proxy         numeric not null check (resilience_proxy >= 0 and resilience_proxy <= 1),
  resilience_proxy_trend   trend not null default 'stable',
  public_footprint_depth   numeric not null check (public_footprint_depth >= 0 and public_footprint_depth <= 1),
  public_footprint_depth_trend trend not null default 'stable',
  network_embeddedness     numeric not null check (network_embeddedness >= 0 and network_embeddedness <= 1),
  network_embeddedness_trend trend not null default 'stable',
  confidence                numeric check (confidence >= 0 and confidence <= 1),
  recorded_at               timestamptz not null default now()
);
create index if not exists idx_genome_founder on founder_genome_snapshots (founder_id, recorded_at desc);
-- time series, same idempotency pattern as founder_score_history
create unique index if not exists uq_genome_founder_recorded on founder_genome_snapshots (founder_id, recorded_at);

create table if not exists founder_confidence_intervals (
  id           uuid primary key default gen_random_uuid(),
  founder_id   uuid not null references founders(id) on delete cascade,
  score        numeric not null,
  lower_bound  numeric not null,
  upper_bound  numeric not null,
  evidence_coverage numeric,      -- 0-1, % of expected signals present
  method_notes text,
  computed_at  timestamptz not null default now()
);

create table if not exists opportunity_axis_scores (
  id              uuid primary key default gen_random_uuid(),
  opportunity_id  uuid not null references opportunities(id) on delete cascade,
  axis            axis_name not null,
  value_numeric   numeric,           -- used for founder / idea_vs_market
  value_label     text,              -- used for market: bullish | neutral | bear
  trend           trend not null default 'stable',
  confidence      numeric check (confidence >= 0 and confidence <= 1),
  computed_at     timestamptz not null default now(),
  constraint chk_axis_value check (value_numeric is not null or value_label is not null)
);
-- one row per (opportunity, axis) — this IS the enforcement of "never averaged"
create unique index if not exists opp_axis_unique on opportunity_axis_scores (opportunity_id, axis);
