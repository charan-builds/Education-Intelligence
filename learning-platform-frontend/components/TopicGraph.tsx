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

export type TopicGraphNode = {
  id: number;
  name: string;
  node_type?: "topic" | "skill";
  status?: string;
  mastery_score?: number | null;
  cluster?: string;
  is_completed?: boolean;
  is_weak?: boolean;
  is_locked?: boolean;
};

export type TopicGraphEdge = {
  source_id?: number;
  target_id?: number;
  topic_id?: number;
  prerequisite_topic_id?: number;
  edge_type?: "prerequisite" | "maps_to_skill";
};

type TopicGraphProps = {
  topics: TopicGraphNode[];
  prerequisites: TopicGraphEdge[];
  weakTopicIds?: number[];
  highlightedPathIds?: number[];
  focusTopicId?: number;
  heightClassName?: string;
};

const X_GAP = 260;
const Y_GAP = 128;

function computeDepths(nodes: TopicGraphNode[], edges: TopicGraphEdge[]): Map<number, number> {
  const topicNodes = nodes.filter((node) => (node.node_type ?? "topic") === "topic");
  const incoming = new Map<number, number>();
  const adjacency = new Map<number, number[]>();

  for (const node of topicNodes) {
    incoming.set(node.id, 0);
    adjacency.set(node.id, []);
  }

  for (const edge of edges) {
    const edgeType = edge.edge_type ?? "prerequisite";
    if (edgeType !== "prerequisite") {
      continue;
    }
    const sourceId = edge.source_id ?? edge.prerequisite_topic_id;
    const targetId = edge.target_id ?? edge.topic_id;
    if (!sourceId || !targetId || !incoming.has(sourceId) || !incoming.has(targetId)) {
      continue;
    }
    adjacency.get(sourceId)?.push(targetId);
    incoming.set(targetId, (incoming.get(targetId) ?? 0) + 1);
  }

  const queue = [...topicNodes.map((n) => n.id).filter((id) => (incoming.get(id) ?? 0) === 0)].sort((a, b) => a - b);
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
      depth.set(next, Math.max(depth.get(next) ?? 0, currentDepth + 1));
      const remaining = (incoming.get(next) ?? 0) - 1;
      incoming.set(next, remaining);
      if (remaining === 0) {
        queue.push(next);
        queue.sort((a, b) => a - b);
      }
    }
  }

  for (const node of topicNodes) {
    if (!depth.has(node.id)) {
      depth.set(node.id, 0);
    }
  }
  return depth;
}

function nodePalette(node: TopicGraphNode, isWeak: boolean, isHighlighted: boolean, isFocus: boolean) {
  const isCompleted = Boolean(node.is_completed) || node.status === "completed" || node.status === "mastered";
  const isLocked = Boolean(node.is_locked) || node.status === "locked";
  if ((node.node_type ?? "topic") === "skill") {
    return {
      border: "rgba(14,165,233,0.35)",
      background: "linear-gradient(135deg, rgba(224,242,254,0.98), rgba(255,255,255,0.92))",
      color: "#0f172a",
      boxShadow: "0 18px 40px rgba(14,165,233,0.12)",
    };
  }
  if (isFocus) {
    return {
      border: "rgba(79,70,229,0.45)",
      background: "linear-gradient(135deg, rgba(224,231,255,0.98), rgba(255,255,255,0.94))",
      color: "#312e81",
      boxShadow: "0 22px 48px rgba(79,70,229,0.18)",
    };
  }
  if (isCompleted) {
    return {
      border: "rgba(16,185,129,0.4)",
      background: "linear-gradient(135deg, rgba(236,253,245,0.98), rgba(209,250,229,0.9))",
      color: "#065f46",
      boxShadow: "0 20px 44px rgba(16,185,129,0.16)",
    };
  }
  if (isLocked) {
    return {
      border: "rgba(100,116,139,0.42)",
      background: "linear-gradient(135deg, rgba(248,250,252,0.98), rgba(226,232,240,0.94))",
      color: "#334155",
      boxShadow: "0 16px 36px rgba(100,116,139,0.14)",
    };
  }
  if (isWeak) {
    return {
      border: "rgba(239,68,68,0.35)",
      background: "linear-gradient(135deg, rgba(255,241,242,0.98), rgba(255,255,255,0.9))",
      color: "#991b1b",
      boxShadow: "0 18px 40px rgba(239,68,68,0.16)",
    };
  }
  if (isHighlighted) {
    return {
      border: "rgba(16,185,129,0.35)",
      background: "linear-gradient(135deg, rgba(236,253,245,0.98), rgba(255,255,255,0.92))",
      color: "#065f46",
      boxShadow: "0 18px 40px rgba(16,185,129,0.16)",
    };
  }
  return {
    border: "rgba(148,163,184,0.28)",
    background: "linear-gradient(135deg, rgba(255,255,255,0.98), rgba(239,246,255,0.88))",
    color: "#0f172a",
    boxShadow: "0 18px 40px rgba(15,23,42,0.08)",
  };
}

export default function TopicGraph({
  topics,
  prerequisites,
  weakTopicIds = [],
  highlightedPathIds = [],
  focusTopicId,
  heightClassName = "h-[560px]",
}: TopicGraphProps) {
  const weakSet = useMemo(() => new Set(weakTopicIds), [weakTopicIds]);
  const pathSet = useMemo(() => new Set(highlightedPathIds), [highlightedPathIds]);

  const { nodes, edges } = useMemo(() => {
    const depths = computeDepths(topics, prerequisites);
    const topicColumns = new Map<number, TopicGraphNode[]>();
    const skillNodes = topics.filter((topic) => (topic.node_type ?? "topic") === "skill").sort((a, b) => a.id - b.id);

    for (const topic of topics) {
      if ((topic.node_type ?? "topic") !== "topic") {
        continue;
      }
      const depth = depths.get(topic.id) ?? 0;
      if (!topicColumns.has(depth)) {
        topicColumns.set(depth, []);
      }
      topicColumns.get(depth)?.push(topic);
    }

    const graphNodes: Node[] = [];
    const sortedDepths = [...topicColumns.keys()].sort((a, b) => a - b);
    for (const depth of sortedDepths) {
      const columnNodes = [...(topicColumns.get(depth) ?? [])].sort((a, b) => a.id - b.id);
      columnNodes.forEach((topic, row) => {
        const isWeak = weakSet.has(topic.id);
        const isHighlighted = pathSet.has(topic.id);
        const isFocus = topic.id === focusTopicId;
        const isCompleted = Boolean(topic.is_completed) || topic.status === "completed" || topic.status === "mastered";
        const isLocked = Boolean(topic.is_locked) || topic.status === "locked";
        const palette = nodePalette(topic, isWeak, isHighlighted, isFocus);
        const mastery = topic.mastery_score != null ? `${Math.round(topic.mastery_score)}%` : "new";
        const statusLabel = isCompleted
          ? "completed"
          : isWeak
            ? "weak"
            : isLocked
              ? "locked"
              : topic.status ?? "unknown";
        graphNodes.push({
          id: String(topic.id),
          data: {
            label: (
              <div className="space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold">{topic.name}</span>
                  <span className="rounded-full bg-white/70 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em]">
                    {mastery}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-2 text-[10px] uppercase tracking-[0.18em] opacity-70">
                  <span>{topic.cluster ?? "general"}</span>
                  <span>{statusLabel}</span>
                </div>
              </div>
            ),
          },
          position: { x: depth * X_GAP, y: row * Y_GAP },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
          style: {
            borderRadius: 24,
            border: `1px solid ${palette.border}`,
            background: palette.background,
            color: palette.color,
            width: 236,
            fontWeight: 600,
            boxShadow: palette.boxShadow,
            padding: "12px 14px",
            opacity: isLocked ? 0.82 : 1,
            borderStyle: isLocked ? "dashed" : "solid",
          },
        });
      });
    }

    const skillColumnX = (sortedDepths.at(-1) ?? 0) * X_GAP + X_GAP;
    skillNodes.forEach((skill, row) => {
      const palette = nodePalette(skill, false, false, false);
      graphNodes.push({
        id: `skill-${skill.id}`,
        data: {
          label: (
            <div className="space-y-1">
              <span className="text-sm font-semibold">{skill.name}</span>
              <div className="text-[10px] uppercase tracking-[0.18em] opacity-70">skill node</div>
            </div>
          ),
        },
        position: { x: skillColumnX, y: row * 96 },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        style: {
          borderRadius: 20,
          border: `1px solid ${palette.border}`,
          background: palette.background,
          color: palette.color,
          width: 204,
          boxShadow: palette.boxShadow,
          padding: "10px 12px",
        },
      });
    });

    const topicNodeIds = new Set(topics.filter((item) => (item.node_type ?? "topic") === "topic").map((item) => item.id));
    const skillNodeIds = new Set(skillNodes.map((item) => item.id));

    const graphEdges: Edge[] = prerequisites.flatMap((edge): Edge[] => {
      const edgeType = edge.edge_type ?? "prerequisite";
      const sourceId = edge.source_id ?? edge.prerequisite_topic_id;
      const targetId = edge.target_id ?? edge.topic_id;
      if (!sourceId || !targetId) {
        return [];
      }
      if (edgeType === "prerequisite") {
        if (!topicNodeIds.has(sourceId) || !topicNodeIds.has(targetId)) {
          return [];
        }
        const onPath = pathSet.has(sourceId) && pathSet.has(targetId);
        const targetNode = topics.find((item) => item.id === targetId && (item.node_type ?? "topic") === "topic");
        const targetWeak = weakSet.has(targetId) || Boolean(targetNode?.is_weak) || targetNode?.status === "weak";
        const targetLocked = Boolean(targetNode?.is_locked) || targetNode?.status === "locked";
        return [
          {
          id: `${sourceId}->${targetId}`,
          source: String(sourceId),
          target: String(targetId),
          type: "smoothstep",
          markerEnd: { type: MarkerType.ArrowClosed },
          animated: targetWeak || onPath,
          style: {
            stroke: onPath ? "#10b981" : targetWeak ? "#ef4444" : targetLocked ? "#94a3b8" : "#64748b",
            strokeWidth: onPath ? 3 : targetWeak ? 2.4 : 1.8,
            strokeDasharray: targetLocked ? "6 4" : undefined,
          },
          },
        ];
      }
      if (!topicNodeIds.has(sourceId) || !skillNodeIds.has(targetId)) {
        return [];
      }
      return [
        {
        id: `${sourceId}->skill-${targetId}`,
        source: String(sourceId),
        target: `skill-${targetId}`,
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed },
        animated: false,
        style: {
          stroke: "#0ea5e9",
          strokeWidth: 1.6,
          strokeDasharray: "4 4",
        },
        },
      ];
    });

    return { nodes: graphNodes, edges: graphEdges };
  }, [focusTopicId, pathSet, prerequisites, topics, weakSet]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-emerald-700">Completed</span>
        <span className="rounded-full bg-rose-100 px-3 py-1 text-rose-700">Weak</span>
        <span className="rounded-full bg-slate-200 px-3 py-1 text-slate-700">Locked</span>
        <span className="rounded-full bg-indigo-100 px-3 py-1 text-indigo-700">Focus</span>
      </div>
      <div
        className={`w-full overflow-hidden rounded-[28px] border border-white/70 bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.12),transparent_26%),linear-gradient(180deg,rgba(255,255,255,0.92),rgba(248,250,252,0.92))] ${heightClassName}`}
      >
        <ReactFlow nodes={nodes} edges={edges} fitView>
        <MiniMap pannable zoomable nodeColor={(node) => (String(node.id).startsWith("skill-") ? "#bae6fd" : "#c7d2fe")} />
        <Controls />
        <Background gap={18} size={1} color="#dbeafe" />
        </ReactFlow>
      </div>
    </div>
  );
}
