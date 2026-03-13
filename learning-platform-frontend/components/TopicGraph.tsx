"use client";

import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  Edge,
  MarkerType,
  MiniMap,
  Node,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";

export type TopicGraphNode = {
  id: number;
  name: string;
};

export type TopicGraphEdge = {
  topic_id: number;
  prerequisite_topic_id: number;
};

type TopicGraphProps = {
  topics: TopicGraphNode[];
  prerequisites: TopicGraphEdge[];
  weakTopicIds?: number[];
  heightClassName?: string;
};

const X_GAP = 260;
const Y_GAP = 120;

function computeDepths(nodes: TopicGraphNode[], edges: TopicGraphEdge[]): Map<number, number> {
  const incoming = new Map<number, number>();
  const adjacency = new Map<number, number[]>();

  for (const node of nodes) {
    incoming.set(node.id, 0);
    adjacency.set(node.id, []);
  }

  for (const edge of edges) {
    if (!incoming.has(edge.topic_id) || !incoming.has(edge.prerequisite_topic_id)) {
      continue;
    }
    adjacency.get(edge.prerequisite_topic_id)?.push(edge.topic_id);
    incoming.set(edge.topic_id, (incoming.get(edge.topic_id) ?? 0) + 1);
  }

  const queue = [...nodes.map((n) => n.id).filter((id) => (incoming.get(id) ?? 0) === 0)].sort((a, b) => a - b);
  const depth = new Map<number, number>();

  for (const id of queue) {
    depth.set(id, 0);
  }

  while (queue.length > 0) {
    const current = queue.shift();
    if (current === undefined) {
      break;
    }

    const currentDepth = depth.get(current) ?? 0;
    const nextList = [...(adjacency.get(current) ?? [])].sort((a, b) => a - b);
    for (const next of nextList) {
      const candidateDepth = currentDepth + 1;
      depth.set(next, Math.max(depth.get(next) ?? 0, candidateDepth));

      const remaining = (incoming.get(next) ?? 0) - 1;
      incoming.set(next, remaining);
      if (remaining === 0) {
        queue.push(next);
        queue.sort((a, b) => a - b);
      }
    }
  }

  // fallback for cycles/disconnected components
  for (const node of nodes) {
    if (!depth.has(node.id)) {
      depth.set(node.id, 0);
    }
  }

  return depth;
}

export default function TopicGraph({
  topics,
  prerequisites,
  weakTopicIds = [],
  heightClassName = "h-[560px]",
}: TopicGraphProps) {
  const weakSet = useMemo(() => new Set(weakTopicIds), [weakTopicIds]);

  const { nodes, edges } = useMemo(() => {
    const depths = computeDepths(topics, prerequisites);
    const columns = new Map<number, TopicGraphNode[]>();

    for (const topic of topics) {
      const d = depths.get(topic.id) ?? 0;
      if (!columns.has(d)) {
        columns.set(d, []);
      }
      columns.get(d)?.push(topic);
    }

    const graphNodes: Node[] = [];
    const sortedDepths = [...columns.keys()].sort((a, b) => a - b);

    for (const depth of sortedDepths) {
      const columnNodes = [...(columns.get(depth) ?? [])].sort((a, b) => a.id - b.id);
      columnNodes.forEach((topic, row) => {
        const isWeak = weakSet.has(topic.id);
        graphNodes.push({
          id: String(topic.id),
          data: { label: `${topic.name}${isWeak ? " (weak)" : ""}` },
          position: { x: depth * X_GAP, y: row * Y_GAP },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
          style: {
            borderRadius: 12,
            border: `1px solid ${isWeak ? "#ef4444" : "#cbd5e1"}`,
            background: isWeak ? "#fef2f2" : "#ffffff",
            color: isWeak ? "#991b1b" : "#0f172a",
            width: 210,
            fontWeight: 600,
          },
        });
      });
    }

    const graphEdges: Edge[] = prerequisites
      .filter((edge) => topics.some((t) => t.id === edge.topic_id) && topics.some((t) => t.id === edge.prerequisite_topic_id))
      .map((edge) => ({
        id: `${edge.prerequisite_topic_id}->${edge.topic_id}`,
        source: String(edge.prerequisite_topic_id),
        target: String(edge.topic_id),
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed },
        animated: weakSet.has(edge.topic_id),
        style: {
          stroke: weakSet.has(edge.topic_id) ? "#ef4444" : "#64748b",
          strokeWidth: weakSet.has(edge.topic_id) ? 2.5 : 1.8,
        },
      }));

    return { nodes: graphNodes, edges: graphEdges };
  }, [topics, prerequisites, weakSet]);

  return (
    <div className={`w-full rounded-xl border border-slate-200 bg-white ${heightClassName}`}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <MiniMap
          pannable
          zoomable
          nodeColor={(node) => ((node.style as { background?: string } | undefined)?.background ?? "#ffffff")}
        />
        <Controls />
        <Background gap={18} size={1} color="#e2e8f0" />
      </ReactFlow>
    </div>
  );
}
