# 09 — Founder Network Graph UI Spec (Agent E)

**Owner:** Agent E — Frontend (builds UI) · Agent B — Sourcing (provides GraphQL + seed graph data)
**Depends on:** `01-CONTRACTS.md` §3 (GraphQL queries), `03-SOURCING.md` §5 (network graph), `06-FRONTEND-UX.md` §P1 #5
**Goal:** Ship a demo-ready, interactive founder network graph in **one session** (~3–4 hours). Live GraphQL preferred; static seed JSON is an acceptable fallback for the demo if the resolver isn't ready.

---

## 1. Where it lives in the product

| Route | Purpose |
|---|---|
| `/founders/[id]` | **Primary placement** — graph panel below Founder Genome radar + network embeddedness badge |
| `/network/[founderId]` | Optional full-screen explorer (same component, more canvas space) |

**Demo story on this screen:** *"Even cold-start founders aren't invisible — we map their collaboration graph, show 2nd-degree paths to known anchors, and disclose that network proximity is capped and separate from merit scoring."*

---

## 2. Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  Founder Network                              depth: [1] [2]       │
│  Filters: sector · geography · min confidence                    │
├────────────────────────────────────┬─────────────────────────────┤
│                                    │  Selected node              │
│                                    │  ─────────────────          │
│         FORCE GRAPH                │  Name: Sequoia Capital      │
│         (react-force-graph-2d)     │  Type: VC · Anchor          │
│                                    │                             │
│    ●  center = selected founder    │  [Show paths to anchors]    │
│    ○  collaborators / companies    │                             │
│    ★  anchor nodes (gold)          │  Proximity paths (depth 2): │
│                                    │  Jane → Bob Chen → Sequoia  │
│                                    │  edge: CO_AUTHORED → ALUMNI  │
│                                    │                             │
│                                    │  ⚠ Disclosure (always show):│
│                                    │  "Network proximity signal —│
│                                    │   reflects who this founder │
│                                    │   is connected to, not their│
│                                    │   own demonstrated capability."│
└────────────────────────────────────┴─────────────────────────────┘
```

**Responsive:** on mobile, stack graph above detail panel; graph height min `400px`.

---

## 3. Tech stack

| Piece | Choice | Why |
|---|---|---|
| Graph rendering | [`react-force-graph-2d`](https://github.com/vasturiano/react-force-graph) | ~30 lines to working graph, Next.js friendly, no D3 boilerplate |
| Data fetching | `@apollo/client` or `graphql-request` | Call existing GraphQL endpoint |
| SSR | `dynamic(..., { ssr: false })` | Force graph needs `window` |
| Styling | Tailwind + shadcn `Card`, `Badge`, `Tabs` | Matches rest of app |

```bash
cd apps/web
npm install react-force-graph-2d graphql-request
# optional: npm install @apollo/client graphql
```

---

## 4. GraphQL queries (from contracts)

### 4.1 Main graph — `FounderNetwork`

```graphql
query FounderNetwork($founderId: ID!, $depth: Int!) {
  founderNetwork(founderId: $founderId, depth: $depth) {
    nodes {
      id
      type      # Founder | VC | Accelerator | Institution | Company
      label
      confidence
      tags      # optional: ["anchor", "tier1_vc"]
    }
    edges {
      from
      to
      relationType  # FOLLOWS | CO_CONTRIBUTED | CO_AUTHORED | CO_PARTICIPATED | ALUMNI_OF | MENTIONED_BY
      weight
      firstSeenAt
    }
  }
}
```

### 4.2 Proximity paths — `NetworkProximity` (side panel + highlight)

```graphql
query NetworkProximity($founderId: ID!, $anchorTags: [String!]) {
  networkProximity(founderId: $founderId, anchorTags: $anchorTags) {
    proximityScore
    confidence
    disclosure
    paths {
      anchorNode { id type label tags }
      viaNode { id type label }
      edgeTypes
      hopCount
      lastActiveAt
    }
  }
}
```

**Client mapping:** GraphQL `nodes`/`edges` → force-graph `nodes`/`links`:

```typescript
type GraphNode = {
  id: string;
  label: string;
  type: string;
  confidence?: number;
  tags?: string[];
};

type GraphLink = {
  source: string;  // node id
  target: string;
  relationType: string;
  weight?: number;
};

function toForceGraphData(response: FounderNetworkResponse) {
  return {
    nodes: response.founderNetwork.nodes.map((n) => ({ ...n, name: n.label })),
    links: response.founderNetwork.edges.map((e) => ({
      source: e.from,
      target: e.to,
      relationType: e.relationType,
      weight: e.weight,
    })),
  };
}
```

---

## 5. Visual design

### 5.1 Node colors (match pipeline diagram palette)

| `type` | Fill | Border | Size multiplier | Notes |
|---|---|---|---|---|
| Selected founder (center) | `#2f9e6e` (teal) | `#1a3d2e` | `1.8` | Always pinned at center on load |
| Founder | `#7c5cbf` (purple) | `#33235c` | `1.0` | |
| Company | `#3b82f6` (blue) | `#1e3a5f` | `0.9` | |
| VC | `#94a3b8` (slate) | `#475569` | `1.0` | |
| VC + `tags` includes `anchor` | `#eab308` (gold) | `#a16207` | `1.3` | ★ anchor nodes |
| Accelerator / Institution | `#f97316` (orange) | `#9a3412` | `1.0` | |

### 5.2 Edge styling

- Default: `#cbd5e1`, width `1`
- On hover: `#64748b`, width `2`
- **Highlighted path to anchor:** `#eab308`, width `3`, animated dash (optional)

### 5.3 Link labels

Show `relationType` on hover only (tooltip), not permanently — avoids clutter.

---

## 6. Interactions (demo-critical)

| Action | Behavior |
|---|---|
| **Depth toggle** (1 / 2) | Re-fetch `FounderNetwork` with new `$depth`. Depth 2 = cold-start second-degree story. |
| **Click node** | Select node → populate right panel (type, label, confidence, connected edges). |
| **"Show paths to anchors"** | Fetch `NetworkProximity` → highlight path edges on graph in gold; list paths in panel. |
| **Hover node** | Tooltip: `{label} · {type}` |
| **Hover link** | Tooltip: `{relationType}` |
| **Filters** (P1 if time) | Client-side filter nodes by `confidence >= threshold`; sector/geo if present on node metadata. |

**Bias-test demo (required for judging):** prepare two seeded founders on this page:
- **Founder A:** strong execution Genome, zero anchor paths → graph shows sparse network, Founder axis still high.
- **Founder B:** weak execution, dense paths to anchors → graph looks impressive, Founder axis lower.

Link from dashboard cards: "View network" → `/founders/{id}`.

---

## 7. Component structure

```
apps/web/
  components/network/
    FounderNetworkGraph.tsx    # main graph + state
    NetworkDetailPanel.tsx     # selected node + proximity paths + disclosure
    networkGraphUtils.ts       # colors, toForceGraphData, highlightPath
    useFounderNetwork.ts       # GraphQL fetch hook
  app/founders/[id]/page.tsx   # Genome radar + badge + graph
  app/network/[founderId]/page.tsx  # optional full-screen
  lib/fixtures/                 # optional local copy; canonical: shared/fixtures/network-graph-seed.json
```

### 7.1 Minimal graph component

```tsx
"use client";

import dynamic from "next/dynamic";
import { useMemo, useState, useCallback } from "react";
import { nodeColor, toForceGraphData } from "./networkGraphUtils";
import { NetworkDetailPanel } from "./NetworkDetailPanel";
import { useFounderNetwork } from "./useFounderNetwork";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

export function FounderNetworkGraph({ founderId }: { founderId: string }) {
  const [depth, setDepth] = useState<1 | 2>(2);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [highlightLinkIds, setHighlightLinkIds] = useState<Set<string>>(new Set());

  const { data, loading } = useFounderNetwork(founderId, depth);
  const graphData = useMemo(() => (data ? toForceGraphData(data) : { nodes: [], links: [] }), [data]);

  const handleNodeClick = useCallback((node: { id: string }) => {
    setSelectedId(node.id);
  }, []);

  if (loading) return <div className="h-[400px] animate-pulse bg-muted rounded-lg" />;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 h-[480px] border rounded-lg overflow-hidden bg-slate-50">
        <ForceGraph2D
          graphData={graphData}
          nodeId="id"
          nodeLabel="label"
          nodeVal={(n) => (n.id === founderId ? 12 : n.type === "VC" && n.tags?.includes("anchor") ? 10 : 6)}
          nodeColor={(n) => nodeColor(n, founderId, selectedId)}
          linkColor={(l) => (highlightLinkIds.has(`${l.source}-${l.target}`) ? "#eab308" : "#cbd5e1")}
          linkWidth={(l) => (highlightLinkIds.has(`${l.source}-${l.target}`) ? 3 : 1)}
          linkLabel="relationType"
          onNodeClick={handleNodeClick}
          cooldownTicks={100}
        />
      </div>
      <NetworkDetailPanel
        founderId={founderId}
        selectedNodeId={selectedId}
        graphData={graphData}
        onHighlightPaths={setHighlightLinkIds}
      />
    </div>
  );
}
```

### 7.2 Detail panel must always show disclosure

The `disclosure` string from `NetworkProximity` is **non-optional UI** — render it in a muted callout box whenever proximity data exists, even if score is low.

---

## 8. Seed graph JSON (fallback for demo)

Agent B: add matching rows to `network_nodes` / `network_edges` in seed script.
Agent E: use this fixture if GraphQL isn't wired yet.

**File:** `shared/fixtures/network-graph-seed.json` (also documented in `15-MOCK-FIXTURES.md`)

```json
{
  "founder-a-cold-start-strong": {
    "founderId": "founder-a-cold-start-strong",
    "description": "Bias test: strong execution, sparse network",
    "founderNetwork": {
      "nodes": [
        { "id": "founder-a-cold-start-strong", "type": "Founder", "label": "Alex Rivera", "confidence": 0.85 },
        { "id": "company-a", "type": "Company", "label": "Rivera Labs", "confidence": 0.9 },
        { "id": "founder-peer-1", "type": "Founder", "label": "Sam Okonkwo", "confidence": 0.7 }
      ],
      "edges": [
        { "from": "founder-a-cold-start-strong", "to": "company-a", "relationType": "CO_CONTRIBUTED", "weight": 0.9, "firstSeenAt": "2025-03-01" },
        { "from": "founder-a-cold-start-strong", "to": "founder-peer-1", "relationType": "CO_PARTICIPATED", "weight": 0.6, "firstSeenAt": "2024-11-15" }
      ]
    },
    "networkProximity": {
      "proximityScore": 0.08,
      "confidence": 0.75,
      "disclosure": "Network proximity signal — reflects who this founder is connected to, not their own demonstrated capability. Shown for transparency, weighted conservatively.",
      "paths": []
    }
  },
  "founder-b-network-heavy-weak": {
    "founderId": "founder-b-network-heavy-weak",
    "description": "Bias test: weak execution, strong 2nd-degree anchor paths",
    "founderNetwork": {
      "nodes": [
        { "id": "founder-b-network-heavy-weak", "type": "Founder", "label": "Jordan Lee", "confidence": 0.6 },
        { "id": "founder-via-bob", "type": "Founder", "label": "Bob Chen", "confidence": 0.88 },
        { "id": "vc-sequoia", "type": "VC", "label": "Sequoia Capital", "confidence": 0.95, "tags": ["anchor", "tier1_vc"] },
        { "id": "accel-yc", "type": "Accelerator", "label": "Y Combinator", "confidence": 0.95, "tags": ["anchor"] },
        { "id": "company-b", "type": "Company", "label": "Lee Analytics", "confidence": 0.5 },
        { "id": "founder-collab", "type": "Founder", "label": "Mia Patel", "confidence": 0.72 }
      ],
      "edges": [
        { "from": "founder-b-network-heavy-weak", "to": "founder-via-bob", "relationType": "CO_AUTHORED", "weight": 0.85, "firstSeenAt": "2025-01-10" },
        { "from": "founder-via-bob", "to": "vc-sequoia", "relationType": "ALUMNI_OF", "weight": 0.9, "firstSeenAt": "2023-06-01" },
        { "from": "founder-b-network-heavy-weak", "to": "founder-collab", "relationType": "CO_CONTRIBUTED", "weight": 0.7, "firstSeenAt": "2024-08-20" },
        { "from": "founder-collab", "to": "accel-yc", "relationType": "PARTICIPATED_IN", "weight": 0.8, "firstSeenAt": "2024-01-05" },
        { "from": "founder-b-network-heavy-weak", "to": "company-b", "relationType": "CO_CONTRIBUTED", "weight": 0.4, "firstSeenAt": "2025-02-01" }
      ]
    },
    "networkProximity": {
      "proximityScore": 0.72,
      "confidence": 0.82,
      "disclosure": "Network proximity signal — reflects who this founder is connected to, not their own demonstrated capability. Shown for transparency, weighted conservatively.",
      "paths": [
        {
          "anchorNode": { "id": "vc-sequoia", "type": "VC", "label": "Sequoia Capital", "tags": ["anchor", "tier1_vc"] },
          "viaNode": { "id": "founder-via-bob", "type": "Founder", "label": "Bob Chen" },
          "edgeTypes": ["CO_AUTHORED", "ALUMNI_OF"],
          "hopCount": 2,
          "lastActiveAt": "2025-01-10"
        },
        {
          "anchorNode": { "id": "accel-yc", "type": "Accelerator", "label": "Y Combinator", "tags": ["anchor"] },
          "viaNode": { "id": "founder-collab", "type": "Founder", "label": "Mia Patel" },
          "edgeTypes": ["CO_CONTRIBUTED", "PARTICIPATED_IN"],
          "hopCount": 2,
          "lastActiveAt": "2024-08-20"
        }
      ]
    }
  }
}
```

**Hook fallback pattern:**

```typescript
// useFounderNetwork.ts
const USE_FIXTURE = process.env.NEXT_PUBLIC_USE_NETWORK_FIXTURE === "true";

export function useFounderNetwork(founderId: string, depth: 1 | 2) {
  if (USE_FIXTURE) {
    const fixture = seedData[founderId];
    return { data: fixture?.founderNetwork, loading: false };
  }
  // else: graphql-request to /graphql
}
```

Set `NEXT_PUBLIC_USE_NETWORK_FIXTURE=true` until Agent B's resolver is live.

---

## 9. Integration with Founder profile page

On `/founders/[id]`, section order:

1. Header (name, Founder Score + trend)
2. **Founder Genome radar** (5 dimensions)
3. **Network embeddedness badge** (capped score, click scrolls to graph)
4. **Founder Network Graph** (this spec)
5. Opportunities / application history

The badge and graph tell the same story: badge = summary number; graph = evidence behind it.

---

## 10. Acceptance checks (Agent E)

- [ ] Graph renders for at least two seeded founders (bias-test pair) without manual layout.
- [ ] Depth toggle switches between 1-hop and 2-hop neighborhoods.
- [ ] Anchor nodes visually distinct (gold).
- [ ] Click node → detail panel updates.
- [ ] "Show paths to anchors" highlights edges + lists path with edge types.
- [ ] Disclosure callout always visible when proximity data exists.
- [ ] Works with fixture JSON (`NEXT_PUBLIC_USE_NETWORK_FIXTURE=true`) and with live GraphQL when available.
- [ ] Demo: Alex (sparse graph, high Founder axis) vs Jordan (dense graph, lower Founder axis) side by side in dry run.

---

## 11. Build time estimate

| Task | Time |
|---|---|
| Install lib + fixture hook | 20 min |
| `FounderNetworkGraph` + colors | 60 min |
| `NetworkDetailPanel` + proximity highlight | 60 min |
| Wire into `/founders/[id]` | 30 min |
| Polish (depth toggle, loading, responsive) | 30 min |
| **Total** | **~3–4 hours** |

---

## 12. Cut if behind schedule

Keep: graph on founder profile with fixture JSON + disclosure + one anchor path highlight.
Cut: full-screen `/network/[id]`, filters, animated dashes, Apollo (use `graphql-request` only).
