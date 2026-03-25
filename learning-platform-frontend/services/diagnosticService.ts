import { apiClient } from "@/services/apiClient";
import type {
  DiagnosticAnswerPayload,
  DiagnosticAnswerResponse,
  DiagnosticQuestion,
  DiagnosticResult,
  DiagnosticSession,
} from "@/types/diagnostic";

export async function startDiagnostic(goal_id: number): Promise<DiagnosticSession> {
  const { data } = await apiClient.post<DiagnosticSession>("/diagnostic/start", { goal_id });
  return data;
}

export async function answerDiagnosticQuestion(
  test_id: number,
  answer: DiagnosticAnswerPayload,
): Promise<DiagnosticAnswerResponse> {
  const { data } = await apiClient.post<DiagnosticAnswerResponse>("/diagnostic/answer", {
    test_id,
    question_id: answer.question_id,
    user_answer: answer.user_answer,
    time_taken: answer.time_taken,
  });
  return data;
}

export async function submitAnswers(test_id: number): Promise<DiagnosticSession> {
  const { data } = await apiClient.post<DiagnosticSession>("/diagnostic/submit", {
    test_id,
  });
  return data;
}

export async function getDiagnosticResult(test_id: number): Promise<DiagnosticResult> {
  const { data } = await apiClient.get<DiagnosticResult>("/diagnostic/result", {
    params: { test_id },
  });
  return data;
}

export async function getNextDiagnosticQuestion(
  test_id: number,
): Promise<DiagnosticQuestion | null> {
  const { data } = await apiClient.get<DiagnosticQuestion | null>(`/diagnostic/next/${test_id}`);
  return data;
}

export async function getDiagnosticSession(test_id: number): Promise<DiagnosticSession> {
  const { data } = await apiClient.get<DiagnosticSession>(`/diagnostic/${test_id}`);
  return data;
}
