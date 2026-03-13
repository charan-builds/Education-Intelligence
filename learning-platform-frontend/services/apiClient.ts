import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

export type ApiError = {
  message: string;
  status?: number;
  details?: unknown;
};

const baseURL = process.env.NEXT_PUBLIC_API_URL;

if (!baseURL) {
  // Keep startup explicit in development/build if env is missing.
  // The app can still run but requests will fail fast.
  // eslint-disable-next-line no-console
  console.warn("NEXT_PUBLIC_API_URL is not defined");
}

export const apiClient = axios.create({
  baseURL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const normalized: ApiError = {
      message:
        (error.response?.data as { detail?: string } | undefined)?.detail ||
        error.message ||
        "Unexpected API error",
      status: error.response?.status,
      details: error.response?.data,
    };

    if (normalized.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }

    return Promise.reject(normalized);
  },
);
