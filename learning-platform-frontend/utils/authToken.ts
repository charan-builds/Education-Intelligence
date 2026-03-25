export const ACCESS_TOKEN_KEY = "access_token";
export const REFRESH_TOKEN_KEY = "refresh_token";
export const AUTH_CHANGED_EVENT = "auth-changed";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function notifyAuthChanged(): void {
  if (isBrowser()) {
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  }
}
