export type TopicPracticeQuestion = {
  id: number;
  topic_id?: number | null;
  difficulty: number;
  question_type: string;
  question_text: string;
  answer_options: string[];
};

export type TopicSummary = {
  id: number;
  tenant_id: number;
  name: string;
  description: string;
};

export type KnowledgeGraphNode = {
  id: number;
  node_type: "topic" | "skill";
  name: string;
  description: string;
  mastery_score?: number | null;
  cluster: string;
  status: string;
  is_completed?: boolean;
  is_weak?: boolean;
  is_locked?: boolean;
  skill_names: string[];
  prerequisite_count: number;
};

export type KnowledgeGraphEdge = {
  source_id: number;
  target_id: number;
  edge_type: "prerequisite" | "maps_to_skill";
  strength: number;
};

export type KnowledgeGraphCluster = {
  label: string;
  topic_count: number;
};

export type KnowledgeGraphResponse = {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  clusters: KnowledgeGraphCluster[];
  summary: {
    topic_count: number;
    skill_count: number;
    edge_count: number;
    completed_topic_count: number;
    weak_topic_count: number;
    locked_topic_count: number;
  };
};

export type TopicReasoningNode = {
  topic_id: number;
  topic_name: string;
  mastery_score?: number | null;
  status: string;
};

export type SimilarTopic = {
  topic_id: number;
  topic_name: string;
  similarity_percent: number;
  cluster: string;
  mastery_score?: number | null;
};

export type RecommendedTopic = {
  topic_id: number;
  topic_name: string;
  reason: string;
  readiness_percent: number;
};

export type TopicReasoning = {
  target_topic_id: number;
  target_topic_name: string;
  dependency_resolution: TopicReasoningNode[];
  shortest_learning_path: TopicReasoningNode[];
  missing_foundations: TopicReasoningNode[];
  inferred_missing_topics: TopicReasoningNode[];
  similar_topics: SimilarTopic[];
  clusters: string[];
  recommended_next_topics: RecommendedTopic[];
  readiness_percent: number;
};

export type CreateTopicPayload = {
  name: string;
  description: string;
};

export type UpdateTopicPayload = Partial<CreateTopicPayload>;

export type TopicPrerequisite = {
  id: number;
  topic_id: number;
  prerequisite_topic_id: number;
};

export type TopicPrerequisitePageResponse = {
  items: TopicPrerequisite[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    next_offset: number | null;
    next_cursor: string | null;
  };
};

export type CreateTopicPrerequisitePayload = {
  topic_id: number;
  prerequisite_topic_id: number;
};

export type TopicDetail = {
  id: number;
  tenant_id: number;
  name: string;
  description: string;
  examples: string[];
  practice_questions: TopicPracticeQuestion[];
};

export type TopicPageResponse = {
  items: TopicSummary[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    next_offset: number | null;
    next_cursor: string | null;
  };
};

export type Question = {
  id: number;
  topic_id: number;
  difficulty: number;
  question_type: string;
  question_text: string;
  correct_answer: string;
  accepted_answers: string[];
  answer_options: string[];
};

export type QuestionPageResponse = {
  items: Question[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    next_offset: number | null;
    next_cursor: string | null;
  };
};

export type CreateQuestionPayload = {
  topic_id: number;
  difficulty: number;
  question_type: string;
  question_text: string;
  correct_answer: string;
  accepted_answers: string[];
  answer_options: string[];
};

export type UpdateQuestionPayload = Partial<CreateQuestionPayload>;

export type ImportQuestionsPayload = {
  items: CreateQuestionPayload[];
};

export type QuestionFilters = {
  topic_id?: number;
  question_type?: string;
  search?: string;
  limit?: number;
  offset?: number;
};
