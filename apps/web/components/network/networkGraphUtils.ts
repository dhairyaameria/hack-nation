const NODE_COLORS: Record<string, { fill: string; anchorFill: string }> = {
  Founder: { fill: "#7c5cbf", anchorFill: "#7c5cbf" },
  Company: { fill: "#3b82f6", anchorFill: "#3b82f6" },
  VC: { fill: "#94a3b8", anchorFill: "#eab308" },
  Accelerator: { fill: "#f97316", anchorFill: "#eab308" },
  Institution: { fill: "#f97316", anchorFill: "#eab308" },
};

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  confidence?: number;
  tags?: string[];
}

export interface GraphEdge {
  from: string;
  to: string;
  relationType: string;
  weight?: number;
  firstSeenAt?: string;
}

export function nodeColor(node: GraphNode, centerId: string) {
  if (node.id === centerId) return "#2f9e6e";
  const palette = NODE_COLORS[node.type] ?? { fill: "#94a3b8", anchorFill: "#eab308" };
  const isAnchor = node.tags?.includes("anchor");
  return isAnchor ? palette.anchorFill : palette.fill;
}

export function toForceGraphData(network: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  return {
    nodes: network.nodes.map((n) => ({ ...n, name: n.label })),
    links: network.edges.map((e) => ({
      source: e.from,
      target: e.to,
      relationType: e.relationType,
      weight: e.weight,
    })),
  };
}
