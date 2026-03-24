"use client";

import React, { useMemo } from "react";

import TopicGraph from "@/components/TopicGraph";
import SurfaceCard from "@/components/ui/SurfaceCard";
import type { RoadmapStep } from "@/types/roadmap";

type TopicOption = {
  id: number;
  name: string;
};

type RoadmapFlowProps = {
  steps: RoadmapStep[];
  topics: TopicOption[];
  weakTopicIds?: number[];
};

export default function RoadmapFlow({ steps, topics, weakTopicIds = [] }: RoadmapFlowProps) {
  const graph = useMemo(() => {
    const graphTopics = steps.map((step) => ({
      id: step.topic_id,
      name: topics.find((topic) => topic.id === step.topic_id)?.name ?? `Topic ${step.topic_id}`,
    }));

    const prerequisites = steps.slice(1).map((step, index) => ({
      prerequisite_topic_id: steps[index].topic_id,
      topic_id: step.topic_id,
    }));

    return {
      graphTopics,
      prerequisites,
    };
  }, [steps, topics]);

  return (
    <SurfaceCard
      title="Interactive skill tree"
      description="An animated dependency graph that turns the roadmap into a visual progression system."
    >
      <TopicGraph
        topics={graph.graphTopics}
        prerequisites={graph.prerequisites}
        weakTopicIds={weakTopicIds}
        heightClassName="h-[420px]"
      />
    </SurfaceCard>
  );
}
