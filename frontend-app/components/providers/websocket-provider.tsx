"use client";

import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { BackendWebSocketClient, type WebSocketConnectionStatus } from "@/lib/websocket";
import type { WebSocketEvent } from "@/lib/types";

interface WebSocketContextValue {
  status: WebSocketConnectionStatus;
  events: WebSocketEvent[];
  lastEvent: WebSocketEvent | null;
  clearEvents: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | undefined>(undefined);

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const { token, isAuthenticated, isReady } = useAuth();
  const [status, setStatus] = useState<WebSocketConnectionStatus>("idle");
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [client] = useState(() => new BackendWebSocketClient());

  useEffect(() => {
    if (!isReady) {
      return;
    }

    if (!isAuthenticated || !token) {
      client.disconnect();
      setStatus("idle");
      return;
    }

    client.connect(
      token,
      (event) => {
        setEvents((current) => [event, ...current].slice(0, 100));
      },
      setStatus,
    );

    return () => {
      client.disconnect();
    };
  }, [client, isAuthenticated, isReady, token]);

  const value = useMemo<WebSocketContextValue>(
    () => ({
      status,
      events,
      lastEvent: events[0] ?? null,
      clearEvents: () => setEvents([]),
    }),
    [status, events],
  );

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
}

export function useWebSocket(): WebSocketContextValue {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
}
