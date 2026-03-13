export type Goal = {
  id: number;
  name: string;
  description: string;
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
