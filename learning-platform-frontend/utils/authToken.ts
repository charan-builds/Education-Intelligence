export const ACCESS_TOKEN_KEY = "access_token";
export const REFRESH_TOKEN_KEY = "refresh_token";
export const AUTH_CHANGED_EVENT = "auth-changed";
export const TOKEN_STORAGE_KEY = "token";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function notifyAuthChanged(): void {
  if (isBrowser()) {
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  }
}

export function getStoredToken(): string | null {
  if (!isBrowser()) {
    return null;
  }
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  if (isBrowser()) {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  }
}

export function clearStoredToken(): void {
  if (isBrowser()) {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}
