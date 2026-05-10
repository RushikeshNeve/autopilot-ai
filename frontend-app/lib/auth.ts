import type { TokenResponse, User } from "@/lib/types";

const AUTH_STORAGE_KEY = "frontend-app.auth";

interface StoredAuthState {
  token: string;
  user: User;
}

export function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function getStoredAuthState(): StoredAuthState | null {
  if (!isBrowser()) {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as StoredAuthState;
    if (!parsed.token || !parsed.user) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function getStoredAuthToken(): string | null {
  return getStoredAuthState()?.token ?? null;
}

export function persistAuthState(response: TokenResponse): void {
  if (!isBrowser()) {
    return;
  }

  const value: StoredAuthState = {
    token: response.access_token,
    user: response.user,
  };
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(value));
}

export function clearStoredAuthState(): void {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.removeItem(AUTH_STORAGE_KEY);
}
