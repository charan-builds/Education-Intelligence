export type Goal = {
  id: number;
  tenant_id: number;
  name: string;
  description: string;
};

export type CreateGoalPayload = {
  name: string;
  description: string;
};

export type UpdateGoalPayload = Partial<CreateGoalPayload>;

export type GoalTopic = {
  id: number;
  goal_id: number;
  topic_id: number;
};

export type PageMeta = {
  total: number;
  limit: number;
  offset: number;
  next_offset: number | null;
  next_cursor: string | null;
};

export type GoalPageResponse = {
  items: Goal[];
  meta: PageMeta;
};

export type GoalTopicPageResponse = {
  items: GoalTopic[];
  meta: PageMeta;
};
