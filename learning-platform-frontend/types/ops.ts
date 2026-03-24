export type FeatureFlag = {
  id: number;
  tenant_id: number;
  feature_name: string;
  enabled: boolean;
  created_at: string;
};

export type FeatureFlagPageMeta = {
  limit: number;
  offset: number;
  returned: number;
  total: number;
  has_more: boolean;
  next_offset: number | null;
};

export type FeatureFlagPageResponse = {
  items: FeatureFlag[];
  meta: FeatureFlagPageMeta;
};

export type FeatureFlagCatalogResponse = {
  items: string[];
};

export type FeatureFlagUpdatePayload = {
  enabled: boolean;
  tenant_id?: number | null;
};

export type OutboxEvent = {
  id: number;
  tenant_id: number | null;
  event_type: string;
  status: "pending" | "processing" | "dead" | "dispatched" | string;
  attempts: number;
  error_message: string | null;
  created_at: string;
  available_at: string;
  dispatched_at: string | null;
};

export type OutboxEventPageResponse = {
  items: OutboxEvent[];
};

export type OutboxStats = {
  pending: number;
  processing: number;
  dead: number;
  dispatched: number;
};

export type OutboxFlushResponse = {
  dispatched: number;
};

export type OutboxRequeueResponse = {
  requeued: number;
};

export type OutboxRecoverResponse = {
  recovered: number;
};
