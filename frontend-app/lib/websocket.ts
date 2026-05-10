import type { WebSocketEvent } from "@/lib/types";

export type WebSocketConnectionStatus = "idle" | "connecting" | "connected" | "disconnected" | "error";

type EventHandler = (event: WebSocketEvent) => void;
type StatusHandler = (status: WebSocketConnectionStatus) => void;

function getWebSocketBaseUrl(): string {
  return process.env.NEXT_PUBLIC_WS_URL ?? "ws://127.0.0.1:8000/ws";
}

export class BackendWebSocketClient {
  private socket: WebSocket | null = null;
  private eventHandler: EventHandler | null = null;
  private statusHandler: StatusHandler | null = null;

  connect(token: string, eventHandler: EventHandler, statusHandler?: StatusHandler): void {
    this.disconnect();
    this.eventHandler = eventHandler;
    this.statusHandler = statusHandler ?? null;
    this.setStatus("connecting");

    const url = new URL(getWebSocketBaseUrl());
    url.searchParams.set("token", token);

    this.socket = new WebSocket(url.toString());
    this.socket.onopen = () => this.setStatus("connected");
    this.socket.onclose = () => this.setStatus("disconnected");
    this.socket.onerror = () => this.setStatus("error");
    this.socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data as string) as WebSocketEvent;
        this.eventHandler?.(parsed);
      } catch {
        // Ignore non-JSON payloads for now.
      }
    };
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
    }
    this.socket = null;
    this.setStatus("disconnected");
  }

  send(payload: unknown): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return;
    }

    this.socket.send(typeof payload === "string" ? payload : JSON.stringify(payload));
  }

  private setStatus(status: WebSocketConnectionStatus): void {
    this.statusHandler?.(status);
  }
}
