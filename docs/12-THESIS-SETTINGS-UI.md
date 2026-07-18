# 12 — Thesis Engine / VC Profile (Schema + Settings UI)

**Owner:** Agent D (API) · Agent E (Settings UI)  
**Purpose:** the VC profile that filters **what types of companies** the fund pursues.

---

## 1. Concept

The **Thesis Engine** is the fund's standing filter. Every outbound sweep, watchlist promotion, pipeline ranking, and memo tone flows through the **active thesis profile**.

A fund may maintain multiple thesis profiles but only one `is_active = true` at a time.

---

## 2. Database schema (`thesis_profiles`)

```sql
create table thesis_profiles (
  id                    uuid primary key default gen_random_uuid(),
  name                  text not null,           -- e.g. "Pre-seed AI Infra EU"
  version               int not null default 1,
  is_active             boolean not null default false,

  -- core thesis (brief required fields)
  sectors               text[] not null,         -- e.g. ['ai_infra', 'devtools']
  stage                 text not null,           -- pre_seed | seed | series_a
  geography             text not null,           -- e.g. 'EU', 'US', 'global'
  check_size_usd        numeric not null,        -- e.g. 100000
  ownership_target_pct  numeric,                 -- e.g. 5.0
  risk_appetite         text not null,           -- conservative | balanced | aggressive

  -- extended filters (optional, our edge)
  exclude_sectors       text[] default '{}',
  require_signals       text[] default '{}',     -- e.g. ['technical_founder', 'enterprise_traction']
  watchlist_promotion_threshold numeric default 0.65,  -- 0-1, outbound promotion bar

  -- metadata
  notes                 text,
  created_at            timestamptz default now(),
  updated_at            timestamptz default now()
);

-- only one active thesis at a time (enforce in app or partial unique index)
create unique index one_active_thesis on thesis_profiles (is_active) where is_active = true;
```

### `opportunities` foreign key
```sql
alter table opportunities add column thesis_profile_id uuid references thesis_profiles(id);
```
Store which thesis was active when the opportunity was analyzed (for replay/audit).

---

## 3. Pydantic shape

```python
class ThesisProfile(BaseModel):
    id: str | None = None
    name: str
    version: int = 1
    is_active: bool = False
    sectors: list[str]
    stage: Literal["pre_seed", "seed", "series_a"]
    geography: str
    check_size_usd: float
    ownership_target_pct: float | None = None
    risk_appetite: Literal["conservative", "balanced", "aggressive"]
    exclude_sectors: list[str] = []
    require_signals: list[str] = []
    watchlist_promotion_threshold: float = 0.65
    notes: str | None = None
```

GraphQL input `ThesisInput` mirrors this for `topFounderMatches`.

---

## 4. API endpoints (Agent D)

| Endpoint | Method | Behavior |
|---|---|---|
| `/thesis` | GET | List all thesis profiles |
| `/thesis` | POST | Create new profile |
| `/thesis/{id}` | GET | Get by id |
| `/thesis/{id}` | PUT | Update (bumps version) |
| `/thesis/{id}/activate` | POST | Set active; deactivates others |
| `/thesis/active` | GET | Return current active thesis |

### Thesis fit score (used in ranking)
Compute `thesis_fit_score` (0–1) per opportunity:

```text
thesis_fit =
  sector_match(opportunity, thesis.sectors, exclude_sectors)
  × stage_match
  × geo_match
  × require_signals_match
  × (1 - penalty if excluded sector hit)
```

Expose on opportunity list API for dashboard sorting.

---

## 5. Settings UI (`/settings/thesis`) — Agent E

### Layout

```text
┌─────────────────────────────────────────────────────────────┐
│  Fund Thesis                                    [+ New]      │
├─────────────────────────────────────────────────────────────┤
│  Active: ● Pre-seed AI Infra EU          [Switch ▼] [Edit]   │
├─────────────────────────────────────────────────────────────┤
│  Sectors          [AI Infra ×] [Devtools ×] [+ Add]          │
│  Exclude          [Crypto ×]                               │
│  Stage            (●) Pre-seed  ( ) Seed  ( ) Series A       │
│  Geography        [ EU ▼ ]                                   │
│  Check size       $ [ 100,000 ]                              │
│  Ownership target [ 5 ] %                                    │
│  Risk appetite    [ Conservative | ● Balanced | Aggressive ]   │
│  Require signals  [ technical_founder × ] [+ Add]            │
│  Watchlist threshold  ────●──── 0.65                        │
│                                                              │
│  [ Save ]  [ Activate this thesis ]                          │
└─────────────────────────────────────────────────────────────┘
```

### Demo behavior (required)
- **Activate** a different thesis → pipeline dashboard re-sorts opportunities within 2s
- Show `thesis_fit_score` badge on each opportunity card
- Show active thesis name in dashboard header

### P1 if time
- Side-by-side compare two theses on same opportunity set
- Version history dropdown

---

## 6. Seed thesis profiles (Agent A)

```json
[
  {
    "name": "Pre-seed AI Infra EU",
    "is_active": true,
    "sectors": ["ai_infra", "devtools"],
    "stage": "pre_seed",
    "geography": "EU",
    "check_size_usd": 100000,
    "ownership_target_pct": 5,
    "risk_appetite": "balanced",
    "exclude_sectors": ["crypto"],
    "require_signals": ["technical_founder"],
    "watchlist_promotion_threshold": 0.65
  },
  {
    "name": "Aggressive US Seed DevTools",
    "is_active": false,
    "sectors": ["devtools", "developer_platforms"],
    "stage": "seed",
    "geography": "US",
    "check_size_usd": 100000,
    "ownership_target_pct": 7,
    "risk_appetite": "aggressive",
    "exclude_sectors": [],
    "require_signals": [],
    "watchlist_promotion_threshold": 0.45
  }
]
```

---

## 7. Acceptance checks

- [ ] CRUD works; only one active thesis at a time
- [ ] Every new `opportunity` stores `thesis_profile_id`
- [ ] Outbound Perplexity sweep reads active thesis
- [ ] Watchlist promotion uses `watchlist_promotion_threshold`
- [ ] Dashboard re-ranks on thesis switch (demo checklist item)
- [ ] `exclude_sectors` hard-filters matching companies from top list
- [ ] `require_signals` shown as match/miss per opportunity in UI
