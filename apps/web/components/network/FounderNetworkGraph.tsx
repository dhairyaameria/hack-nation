"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
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

  // react-force-graph-2d's own auto-sizing doesn't reliably pick up the
  // parent's flex-driven width on first mount, leaving a blank canvas —
  // measure the container directly instead.
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 320 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) setSize({ width, height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  if (!data || graphData.nodes.length === 0) {
    return (
      <div className="h-[320px] rounded-lg border bg-muted/30 flex items-center justify-center text-sm text-muted-foreground">
        No network graph data for this founder yet.
      </div>
    );
  }

  return (
    <div ref={containerRef} className="h-[320px] rounded-[2px] border overflow-hidden bg-raise">
      {size.width > 0 && (
        <ForceGraph2D
          graphData={graphData}
          width={size.width}
          height={size.height}
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
        />
      )}
    </div>
  );
}
