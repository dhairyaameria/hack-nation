"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import { nodeColor, toForceGraphData, type GraphNode } from "./networkGraphUtils";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

interface NetworkData {
  founderNetwork: {
    nodes: GraphNode[];
    edges: { from: string; to: string; relationType: string; weight?: number }[];
  };
  networkProximity?: {
    proximityScore: number;
    confidence: number;
    disclosure: string;
    paths: unknown[];
  };
}

export function FounderNetworkGraph({
  founderId,
  data,
}: {
  founderId: string;
  data: NetworkData | null;
}) {
  const graphData = useMemo(
    () =>
      data
        ? toForceGraphData(data.founderNetwork)
        : { nodes: [] as ReturnType<typeof toForceGraphData>["nodes"], links: [] as ReturnType<typeof toForceGraphData>["links"] },
    [data]
  );

  if (!data || graphData.nodes.length === 0) {
    return (
      <div className="h-[320px] rounded-lg border bg-muted/30 flex items-center justify-center text-sm text-muted-foreground">
        No network graph data for this founder yet.
      </div>
    );
  }

  return (
    <div className="h-[320px] rounded-lg border overflow-hidden bg-slate-50">
      <ForceGraph2D
        graphData={graphData}
        nodeId="id"
        nodeLabel="label"
        nodeVal={(n: { id?: string | number; tags?: string[] }) =>
          n.id === founderId ? 12 : n.tags?.includes("anchor") ? 10 : 6
        }
        nodeColor={(n: object) => nodeColor(n as GraphNode, founderId)}
        linkColor={() => "#cbd5e1"}
        linkWidth={1}
        linkLabel="relationType"
        cooldownTicks={100}
        width={undefined}
      />
    </div>
  );
}
