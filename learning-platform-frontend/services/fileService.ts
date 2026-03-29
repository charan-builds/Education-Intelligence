import { apiClient } from "@/services/apiClient";

export type UploadRequest = {
  filename: string;
  content_type: string;
  metadata?: Record<string, unknown>;
};

export type UploadRequestResponse = {
  asset_id: number;
  object_key: string;
  upload_url: string | null;
  upload_method: "PUT";
  upload_headers: Record<string, string>;
  cdn_url: string | null;
  expires_in_seconds: number;
  max_bytes: number;
};

export type FinalizedUploadResponse = {
  asset_id: number;
  object_key: string;
  cdn_url: string | null;
  size_bytes: number | null;
  metadata: Record<string, unknown>;
};

export async function createUploadRequest(payload: UploadRequest): Promise<UploadRequestResponse> {
  const { data } = await apiClient.post<UploadRequestResponse>("/files/upload-request", payload);
  return data;
}

export async function uploadAssetToSignedUrl(file: File, signedRequest: UploadRequestResponse): Promise<void> {
  if (!signedRequest.upload_url) {
    throw new Error("Object storage upload is not configured for this environment.");
  }
  const response = await fetch(signedRequest.upload_url, {
    method: signedRequest.upload_method,
    headers: signedRequest.upload_headers,
    body: file,
  });
  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}`);
  }
}

export async function finalizeUpload(asset_id: number, file: File, metadata?: Record<string, unknown>): Promise<FinalizedUploadResponse> {
  const { data } = await apiClient.post<FinalizedUploadResponse>("/files/finalize", {
    asset_id,
    size_bytes: file.size,
    metadata: metadata ?? {},
  });
  return data;
}
