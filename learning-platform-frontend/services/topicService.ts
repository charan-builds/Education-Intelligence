import { apiClient } from "@/services/apiClient";
import type {
  CreateTopicPayload,
  CreateTopicPrerequisitePayload,
  CreateQuestionPayload,
  QuestionFilters,
  ImportQuestionsPayload,
  KnowledgeGraphResponse,
  Question,
  QuestionPageResponse,
  TopicDetail,
  TopicPageResponse,
  TopicPrerequisite,
  TopicPrerequisitePageResponse,
  TopicReasoning,
  TopicSummary,
  UpdateTopicPayload,
  UpdateQuestionPayload,
} from "@/types/topic";

export async function getTopics(): Promise<TopicPageResponse> {
  const { data } = await apiClient.get<TopicPageResponse>("/topics");
  return data;
}

export async function createTopic(payload: CreateTopicPayload): Promise<TopicSummary> {
  const { data } = await apiClient.post<TopicSummary>("/topics", payload);
  return data;
}

export async function updateTopic(topicId: number, payload: UpdateTopicPayload): Promise<TopicSummary> {
  const { data } = await apiClient.put<TopicSummary>(`/topics/${topicId}`, payload);
  return data;
}

export async function deleteTopic(topicId: number): Promise<void> {
  await apiClient.delete(`/topics/${topicId}`);
}

export async function getTopicPrerequisites(topic_id?: number): Promise<TopicPrerequisitePageResponse> {
  const { data } = await apiClient.get<TopicPrerequisitePageResponse>("/topics/prerequisites", {
    params: topic_id ? { topic_id } : undefined,
  });
  return data;
}

export async function createTopicPrerequisite(
  payload: CreateTopicPrerequisitePayload,
): Promise<TopicPrerequisite> {
  const { data } = await apiClient.post<TopicPrerequisite>("/topics/prerequisites", payload);
  return data;
}

export async function deleteTopicPrerequisite(prerequisiteId: number): Promise<void> {
  await apiClient.delete(`/topics/prerequisites/${prerequisiteId}`);
}

export async function getTopic(topicId: number): Promise<TopicDetail> {
  const { data } = await apiClient.get<TopicDetail>(`/topics/${topicId}`);
  return data;
}

export async function getTopicKnowledgeGraph(): Promise<KnowledgeGraphResponse> {
  const { data } = await apiClient.get<KnowledgeGraphResponse>("/topics/graph");
  return data;
}

export async function getTopicReasoning(topicId: number): Promise<TopicReasoning> {
  const { data } = await apiClient.get<TopicReasoning>(`/topics/reasoning/${topicId}`);
  return data;
}

export async function getQuestions(filters?: QuestionFilters): Promise<QuestionPageResponse> {
  const { data } = await apiClient.get<QuestionPageResponse>("/topics/questions", {
    params: {
      ...(filters?.topic_id ? { topic_id: filters.topic_id } : {}),
      ...(filters?.question_type ? { question_type: filters.question_type } : {}),
      ...(filters?.search ? { search: filters.search } : {}),
      ...(filters?.limit ? { limit: filters.limit } : {}),
      ...(filters?.offset !== undefined ? { offset: filters.offset } : {}),
    },
  });
  return data;
}

export async function createQuestion(payload: CreateQuestionPayload): Promise<Question> {
  const { data } = await apiClient.post<Question>("/topics/questions", payload);
  return data;
}

export async function updateQuestion(questionId: number, payload: UpdateQuestionPayload): Promise<Question> {
  const { data } = await apiClient.put<Question>(`/topics/questions/${questionId}`, payload);
  return data;
}

export async function deleteQuestion(questionId: number): Promise<void> {
  await apiClient.delete(`/topics/questions/${questionId}`);
}

export async function importQuestions(payload: ImportQuestionsPayload): Promise<{ created: number }> {
  const { data } = await apiClient.post<{ created: number }>("/topics/questions/import", payload);
  return data;
}

export async function exportQuestions(topic_id?: number): Promise<string> {
  const { data } = await apiClient.get<string>("/topics/questions/export", {
    params: topic_id ? { topic_id } : undefined,
    responseType: "text",
  });
  return data;
}

export async function importQuestionsCsv(content: string): Promise<{ created: number }> {
  const { data } = await apiClient.post<{ created: number }>("/topics/questions/import.csv", content, {
    headers: { "Content-Type": "text/csv" },
  });
  return data;
}

export async function exportQuestionsCsv(topic_id?: number): Promise<string> {
  const { data } = await apiClient.get<string>("/topics/questions/export.csv", {
    params: topic_id ? { topic_id } : undefined,
    responseType: "text",
  });
  return data;
}
