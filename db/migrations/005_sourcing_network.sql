-- 005 — Watchlist, channel intelligence, Wayback, network graph
-- See docs/03-SOURCING.md, docs/09-NETWORK-GRAPH-UI.md.

create table if not exists watchlist_entries (
  id            uuid primary key default gen_random_uuid(),
  founder_id    uuid not null references founders(id) on delete cascade,
  company_id    uuid references companies(id),
  stage         watchlist_stage not null default 'discovered',
  promoted_via  text,             -- e.g. 'network_proximity', 'github_velocity'
  conviction_score numeric,
  source        text,
  source_entity_id text,
  fetched_at    timestamptz,
  run_id        uuid,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists idx_watchlist_founder on watchlist_entries (founder_id);
create index if not exists idx_watchlist_stage on watchlist_entries (stage);

create table if not exists channel_performance (
  id                       uuid primary key default gen_random_uuid(),
  channel_id               text not null,
  channel_name             text not null,
  conversion_to_funded_rate numeric,
  sample_size              int not null default 0,
  sample_size_confidence   numeric,
  is_underexplored         boolean not null default false,
  recorded_at              timestamptz not null default now()
);

create table if not exists channel_recommendations (
  id            uuid primary key default gen_random_uuid(),
  channel_id    text not null,
  rationale     text not null,
  created_at    timestamptz not null default now()
);

create table if not exists wayback_snapshots (
  id             uuid primary key default gen_random_uuid(),
  company_id     uuid references companies(id) on delete cascade,
  domain         text not null,
  snapshot_at    timestamptz not null,
  raw_html_ref   text,             -- Bronze storage locator
  extracted_summary text,
  sentiment      text,             -- positive | neutral | mixed | negative
  confidence     numeric check (confidence >= 0 and confidence <= 1),
  source         text default 'wayback',
  fetched_at     timestamptz,
  run_id         uuid,
  created_at     timestamptz not null default now()
);
create index if not exists idx_wayback_company on wayback_snapshots (company_id);
create unique index if not exists uq_wayback_company_snapshot on wayback_snapshots (company_id, snapshot_at);

create table if not exists wayback_sentiment_timeseries (
  id            uuid primary key default gen_random_uuid(),
  company_id    uuid references companies(id) on delete cascade,
  snapshot_at   timestamptz not null,
  sentiment_score numeric,        -- -1..1
  narrative_label text,           -- stable | pivoted | inconsistent
  created_at    timestamptz not null default now()
);

create table if not exists network_nodes (
  id          uuid primary key default gen_random_uuid(),
  type        network_node_type not null,
  label       text not null,
  confidence  numeric check (confidence >= 0 and confidence <= 1),
  tags        text[] not null default '{}',   -- e.g. ['anchor', 'tier1_vc']
  ref_founder_id uuid references founders(id),
  ref_company_id uuid references companies(id),
  source      text,
  fetched_at  timestamptz,
  run_id      uuid,
  created_at  timestamptz not null default now()
);
create index if not exists idx_network_nodes_tags on network_nodes using gin (tags);

create table if not exists network_edges (
  id             uuid primary key default gen_random_uuid(),
  from_node_id   uuid not null references network_nodes(id) on delete cascade,
  to_node_id     uuid not null references network_nodes(id) on delete cascade,
  relation_type  network_edge_type not null,
  weight         numeric,
  first_seen_at  timestamptz,
  source         text,
  created_at     timestamptz not null default now()
);
create index if not exists idx_network_edges_from on network_edges (from_node_id);
create index if not exists idx_network_edges_to on network_edges (to_node_id);
create unique index if not exists uq_network_edges on network_edges (from_node_id, to_node_id, relation_type);

create table if not exists network_anchor_tags (
  id          uuid primary key default gen_random_uuid(),
  node_id     uuid not null references network_nodes(id) on delete cascade,
  tag         text not null,       -- e.g. 'tier1_vc', 'notable_founder', 'top_accelerator'
  created_at  timestamptz not null default now()
);

create table if not exists network_proximity_scores (
  id              uuid primary key default gen_random_uuid(),
  founder_id      uuid not null references founders(id) on delete cascade,
  path_count      int not null default 0,
  path_diversity  numeric,
  edge_recency    numeric,
  proximity_score numeric not null check (proximity_score >= 0 and proximity_score <= 1),
  confidence      numeric check (confidence >= 0 and confidence <= 1),
  disclosure      text not null,   -- mandatory plain-language disclosure string
  computed_at     timestamptz not null default now()
);
-- current/latest snapshot per founder (not a time series, unlike founder_score_history)
create unique index if not exists uq_proximity_founder on network_proximity_scores (founder_id);
