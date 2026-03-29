import { apiClient } from "@/services/apiClient";
import type {
  AutonomousAgentResponse,
  MentorLearner,
  MentorNotificationsResponse,
  MentorProgressAnalysisResponse,
  MentorSuggestionsResponse,
} from "@/types/mentor";

type LearnerParams = {
  learnerId?: number | null;
};

function buildLearnerParams({ learnerId }: LearnerParams = {}) {
  return learnerId ? { learner_id: learnerId } : undefined;
}

export async function getMentorLearners(): Promise<MentorLearner[]> {
  const { data } = await apiClient.get<MentorLearner[]>("/mentor/learners");
  return data;
}

export async function getMentorSuggestions({ learnerId }: LearnerParams = {}): Promise<MentorSuggestionsResponse> {
  const { data } = await apiClient.get<MentorSuggestionsResponse>("/mentor/suggestions", {
    params: buildLearnerParams({ learnerId }),
  });
  return data;
}

export async function getMentorProgressAnalysis({ learnerId }: LearnerParams = {}): Promise<MentorProgressAnalysisResponse> {
  const { data } = await apiClient.get<MentorProgressAnalysisResponse>("/mentor/progress-analysis", {
    params: buildLearnerParams({ learnerId }),
  });
  return data;
}

export async function getMentorNotifications({ learnerId }: LearnerParams = {}): Promise<MentorNotificationsResponse> {
  const { data } = await apiClient.get<MentorNotificationsResponse>("/mentor/notifications", {
    params: buildLearnerParams({ learnerId }),
  });
  return data;
}

export async function getAutonomousAgentStatus({ learnerId }: LearnerParams = {}): Promise<AutonomousAgentResponse> {
  const { data } = await apiClient.get<AutonomousAgentResponse>("/mentor/agent/status", {
    params: buildLearnerParams({ learnerId }),
  });
  return data;
}

export async function runAutonomousAgent({ learnerId }: LearnerParams = {}): Promise<AutonomousAgentResponse> {
  const { data } = await apiClient.post<AutonomousAgentResponse>(
    "/mentor/agent/run",
    {},
    {
      params: buildLearnerParams({ learnerId }),
    },
  );
  return data;
}
