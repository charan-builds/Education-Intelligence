import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

import { notifyAuthChanged } from "@/utils/authToken";

export type ApiError = {
  message: string;
  status?: number;
  details?: unknown;
};

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

const baseURL = process.env.NEXT_PUBLIC_API_URL;

if (!baseURL) {
  // eslint-disable-next-line no-console
  console.warn("NEXT_PUBLIC_API_URL is not defined");
}

export const apiClient = axios.create({
  baseURL,
  timeout: 10000,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

const sessionClient = axios.create({
  baseURL,
  timeout: 10000,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

let refreshPromise: Promise<void> | null = null;

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function applyCsrfHeader(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
  const method = (config.method ?? "get").toUpperCase();
  if (!["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    return config;
  }
  const csrfToken = readCookie("csrf_token");
  if (csrfToken) {
    config.headers["X-CSRF-Token"] = csrfToken;
  }
  return config;
}

function normalizeError(error: AxiosError): ApiError {
  return {
    message:
      (error.response?.data as { detail?: string } | undefined)?.detail ||
      error.message ||
      "Unexpected API error",
    status: error.response?.status,
    details: error.response?.data,
  };
}

function isAuthEndpoint(url?: string): boolean {
  if (!url) {
    return false;
  }
  return ["/auth/login", "/auth/logout", "/auth/refresh", "/auth/register"].some((path) => url.includes(path));
}

async function clearSessionAndRedirect(): Promise<void> {
  if (typeof window === "undefined") {
    return;
  }
  try {
    await sessionClient.post("/auth/logout");
  } catch {
    // Ignore logout cleanup failures and continue redirecting.
  }
  window.localStorage.removeItem("active_tenant_id");
  notifyAuthChanged();
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  if (!window.location.pathname.startsWith("/auth")) {
    window.location.href = `/auth?next=${next}`;
  }
}

async function refreshSession(): Promise<void> {
  if (!refreshPromise) {
    refreshPromise = sessionClient
      .post("/auth/refresh")
      .then(() => {
        notifyAuthChanged();
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const activeTenantId = localStorage.getItem("active_tenant_id");
    if (activeTenantId) {
      config.headers["X-Tenant-ID"] = activeTenantId;
    }
  }
  return applyCsrfHeader(config);
});

sessionClient.interceptors.request.use((config: InternalAxiosRequestConfig) => applyCsrfHeader(config));

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const normalized = normalizeError(error);
    const original = error.config as RetriableRequestConfig | undefined;

    if (
      normalized.status === 401 &&
      typeof window !== "undefined" &&
      original &&
      !original._retry &&
      !isAuthEndpoint(original.url)
    ) {
      original._retry = true;
      try {
        await refreshSession();
        return apiClient(original);
      } catch {
        await clearSessionAndRedirect();
      }
    }

    if (normalized.status === 401 && typeof window !== "undefined") {
      await clearSessionAndRedirect();
    }

    return Promise.reject(normalized);
  },
);
