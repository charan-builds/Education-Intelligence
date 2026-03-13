"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/services/apiClient";

type HealthResponse = { message: string };

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data } = await apiClient.get<HealthResponse>("/");
      return data;
    },
  });
}
