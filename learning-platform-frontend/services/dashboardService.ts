import { apiClient } from "@/services/apiClient";
import type { StudentDashboardPayload, TeacherDashboardPayload } from "@/types/dashboard";

export async function getStudentDashboard(): Promise<StudentDashboardPayload> {
  const { data } = await apiClient.get<StudentDashboardPayload>("/dashboard/student");
  return data;
}

export async function getTeacherDashboard(): Promise<TeacherDashboardPayload> {
  const { data } = await apiClient.get<TeacherDashboardPayload>("/dashboard/teacher");
  return data;
}
