import { apiClient } from "@/services/apiClient";
import type {
  OnboardingEventPayload,
  UserProfile,
  UserProfilePayload,
  UserProfileProgress,
  UserProfileStatus,
} from "@/types/profile";

type UploadPhotoResponse = {
  profile_photo_url: string;
};

export async function getProfile(): Promise<UserProfile> {
  const { data } = await apiClient.get<UserProfile>("/profile");
  return data;
}

export async function saveProfile(payload: UserProfilePayload): Promise<UserProfile> {
  const { data } = await apiClient.post<UserProfile>("/profile", payload);
  return data;
}

export async function getProfileStatus(): Promise<UserProfileStatus> {
  const { data } = await apiClient.get<UserProfileStatus>("/profile/status");
  return data;
}

export async function getProfileProgress(): Promise<UserProfileProgress> {
  const { data } = await apiClient.get<UserProfileProgress>("/profile/progress");
  return data;
}

export async function trackOnboardingEvent(payload: OnboardingEventPayload): Promise<void> {
  await apiClient.post("/profile/onboarding-events", payload);
}

export async function uploadProfilePhoto(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("photo", file);
  const { data } = await apiClient.post<UploadPhotoResponse>("/profile/upload-photo", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data.profile_photo_url;
}
