export type RoadmapStep = {
  id: number;
  topic_id: number;
  estimated_time_hours: number;
  difficulty: string;
  priority: number;
  deadline: string;
  progress_status: string;
};

export type Roadmap = {
  id: number;
  user_id: number;
  goal_id: number;
  generated_at: string;
  steps: RoadmapStep[];
};

export type RoadmapPageMeta = {
  total: number;
  limit: number;
  offset: number;
  next_offset: number | null;
  next_cursor: string | null;
};

export type RoadmapPageResponse = {
  items: Roadmap[];
  meta: RoadmapPageMeta;
};
