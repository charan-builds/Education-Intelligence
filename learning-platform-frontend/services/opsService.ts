import { apiClient } from "@/services/apiClient";
import type {
  FeatureFlag,
  FeatureFlagCatalogResponse,
  FeatureFlagPageResponse,
  FeatureFlagUpdatePayload,
  OutboxEventPageResponse,
  OutboxFlushResponse,
  OutboxRecoverResponse,
  OutboxRequeueResponse,
  OutboxStats,
} from "@/types/ops";

export async function getFeatureFlags(params?: {
  tenant_id?: number;
  limit?: number;
  offset?: number;
}): Promise<FeatureFlagPageResponse> {
  const { data } = await apiClient.get<FeatureFlagPageResponse>("/ops/feature-flags", {
    params,
  });
  return data;
}

export async function getFeatureFlagCatalog(): Promise<FeatureFlagCatalogResponse> {
  const { data } = await apiClient.get<FeatureFlagCatalogResponse>("/ops/feature-flags/catalog");
  return data;
}

export async function updateFeatureFlag(
  flagName: string,
  payload: FeatureFlagUpdatePayload,
): Promise<FeatureFlag> {
  const { data } = await apiClient.post<FeatureFlag>(`/ops/feature-flags/${flagName}`, payload);
  return data;
}

export async function getOutboxEvents(params?: {
  event_status?: "pending" | "processing" | "dead" | "dispatched";
  limit?: number;
  offset?: number;
}): Promise<OutboxEventPageResponse> {
  const { data } = await apiClient.get<OutboxEventPageResponse>("/ops/outbox", {
    params,
  });
  return data;
}

export async function getOutboxStats(): Promise<OutboxStats> {
  const { data } = await apiClient.get<OutboxStats>("/ops/outbox/stats");
  return data;
}

export async function flushOutbox(limit = 100): Promise<OutboxFlushResponse> {
  const { data } = await apiClient.post<OutboxFlushResponse>("/ops/outbox/flush", null, {
    params: { limit },
  });
  return data;
}

export async function requeueDeadOutbox(limit = 100): Promise<OutboxRequeueResponse> {
  const { data } = await apiClient.post<OutboxRequeueResponse>("/ops/outbox/requeue-dead", null, {
    params: { limit },
  });
  return data;
}

export async function recoverStuckOutbox(limit = 500): Promise<OutboxRecoverResponse> {
  const { data } = await apiClient.post<OutboxRecoverResponse>("/ops/outbox/recover-stuck", null, {
    params: { limit },
  });
  return data;
}
