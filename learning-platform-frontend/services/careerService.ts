import { apiClient } from "@/services/apiClient";
import type { CareerOverview, InterviewPrep, JobReadiness, ResumePreview } from "@/types/career";

export async function getCareerOverview(): Promise<CareerOverview> {
  const { data } = await apiClient.get<CareerOverview>("/career/overview");
  return data;
}

export async function getCareerReadiness(): Promise<JobReadiness> {
  const { data } = await apiClient.get<JobReadiness>("/career/readiness");
  return data;
}

export async function getResumePreview(): Promise<ResumePreview> {
  const { data } = await apiClient.get<ResumePreview>("/career/resume");
  return data;
}

export async function getInterviewPrep(payload: {
  role_name: string;
  difficulty: string;
  count: number;
}): Promise<InterviewPrep> {
  const { data } = await apiClient.post<InterviewPrep>("/career/interview-prep", payload);
  return data;
}
