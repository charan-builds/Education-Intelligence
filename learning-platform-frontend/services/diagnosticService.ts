import { apiClient } from "@/services/apiClient";
import type { DiagnosticAnswerPayload, DiagnosticResult, DiagnosticSession } from "@/types/diagnostic";

export async function startDiagnostic(goal_id: number): Promise<DiagnosticSession> {
  const { data } = await apiClient.post<DiagnosticSession>("/diagnostic/start", { goal_id });
  return data;
}

export async function submitAnswers(
  test_id: number,
  answers: DiagnosticAnswerPayload[],
): Promise<DiagnosticSession> {
  const { data } = await apiClient.post<DiagnosticSession>("/diagnostic/submit", {
    test_id,
    answers,
  });
  return data;
}

export async function getDiagnosticResult(test_id: number): Promise<DiagnosticResult> {
  const { data } = await apiClient.get<DiagnosticResult>("/diagnostic/result", {
    params: { test_id },
  });
  return data;
}
