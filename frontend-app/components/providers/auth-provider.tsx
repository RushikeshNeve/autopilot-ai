"use client";

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { backendApi } from "@/lib/api/backend-api";
import { clearStoredAuthState, getStoredAuthState, persistAuthState } from "@/lib/auth";
import type { AuthCredentials, RegisterPayload, TokenResponse, User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isReady: boolean;
  login: (payload: AuthCredentials) => Promise<TokenResponse>;
  register: (payload: RegisterPayload) => Promise<TokenResponse>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const stored = getStoredAuthState();
    if (stored) {
      setUser(stored.user);
      setToken(stored.token);
    }
    setIsReady(true);
  }, []);

  const hydrateSession = useCallback((response: TokenResponse) => {
    setUser(response.user);
    setToken(response.access_token);
    persistAuthState(response);
  }, []);

  const login = useCallback(
    async (payload: AuthCredentials) => {
      const response = await backendApi.login(payload);
      hydrateSession(response);
      return response;
    },
    [hydrateSession],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      const response = await backendApi.register(payload);
      hydrateSession(response);
      return response;
    },
    [hydrateSession],
  );

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    clearStoredAuthState();
  }, []);

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (token && user) {
      persistAuthState({
        access_token: token,
        token_type: "bearer",
        expires_in: 0,
        user,
      });
      return;
    }
    clearStoredAuthState();
  }, [isReady, token, user]);

  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated: Boolean(token && user),
    isReady,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
