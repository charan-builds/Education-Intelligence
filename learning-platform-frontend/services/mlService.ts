import { apiClient } from "@/services/apiClient";
import type { MLOutputOverview, LearnerFeatureSnapshot, MLTrainingRun } from "@/types/ml";

export async function getMlOverview(): Promise<MLOutputOverview> {
  const { data } = await apiClient.get<MLOutputOverview>("/ml/overview");
  return data;
}

export async function createFeatureSnapshot(): Promise<LearnerFeatureSnapshot> {
  const { data } = await apiClient.post<LearnerFeatureSnapshot>("/ml/features/snapshot");
  return data;
}

export async function trainModel(model_name: string): Promise<MLTrainingRun> {
  const { data } = await apiClient.post<MLTrainingRun>("/ml/train", { model_name });
  return data;
}
