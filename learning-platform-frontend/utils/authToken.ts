export const ACCESS_TOKEN_KEY = "access_token";
export const AUTH_CHANGED_EVENT = "auth-changed";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function emitAuthChanged(): void {
  if (isBrowser()) {
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  }
}

export function storeAccessToken(token: string): void {
  if (!isBrowser()) {
    return;
  }
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
  document.cookie = `${ACCESS_TOKEN_KEY}=${encodeURIComponent(token)}; Path=/; SameSite=Lax`;
  emitAuthChanged();
}

export function clearAccessToken(): void {
  if (!isBrowser()) {
    return;
  }
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  document.cookie = `${ACCESS_TOKEN_KEY}=; Path=/; Max-Age=0; SameSite=Lax`;
  emitAuthChanged();
}

export function getAccessToken(): string | null {
  if (!isBrowser()) {
    return null;
  }
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}
