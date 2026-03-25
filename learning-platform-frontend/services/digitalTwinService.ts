import { apiClient } from "@/services/apiClient";
import type { DigitalTwin } from "@/types/digitalTwin";

export async function getDigitalTwin(): Promise<DigitalTwin> {
  const { data } = await apiClient.get<DigitalTwin>("/digital-twin");
  return data;
}
