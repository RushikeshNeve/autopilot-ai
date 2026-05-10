"use client";

import { useMemo } from "react";

import { useWebSocket } from "@/components/providers/websocket-provider";
import type { WebSocketEvent } from "@/lib/types";

const planningEventTypes = new Set([
  "planning_started",
  "planning_progress",
  "planning_completed",
]);

const executionEventTypes = new Set([
  "execution_job_submitted",
  "execution_job_running",
  "execution_job_completed",
  "execution_job_failed",
]);

const ragEventTypes = new Set(["rag_ingestion_started", "rag_ingestion_completed"]);

export interface RealtimeTimelineItem {
  event: WebSocketEvent;
  label: string;
  tone: "default" | "success" | "warning" | "destructive";
}

function formatEventLabel(event: WebSocketEvent): string {
  switch (event.event_type) {
    case "planning_started":
      return "Planning started";
    case "planning_progress":
      return "Planning progress";
    case "planning_completed":
      return "Planning completed";
    case "execution_job_submitted":
      return "Execution job submitted";
    case "execution_job_running":
      return "Execution job running";
    case "execution_job_completed":
      return "Execution job completed";
    case "execution_job_failed":
      return "Execution job failed";
    case "rag_ingestion_started":
      return "RAG ingestion started";
    case "rag_ingestion_completed":
      return "RAG ingestion completed";
    default:
      return event.event_type;
  }
}

function getTone(event: WebSocketEvent): RealtimeTimelineItem["tone"] {
  switch (event.event_type) {
    case "planning_completed":
    case "execution_job_completed":
    case "rag_ingestion_completed":
      return "success";
    case "execution_job_failed":
      return "destructive";
    case "planning_progress":
    case "execution_job_running":
    case "execution_job_submitted":
    case "planning_started":
    case "rag_ingestion_started":
      return "warning";
    default:
      return "default";
  }
}

export function useRealtimeEvents() {
  const { status, events, lastEvent, clearEvents } = useWebSocket();

  const planningEvents = useMemo(
    () => events.filter((event) => planningEventTypes.has(event.event_type)),
    [events],
  );
  const executionEvents = useMemo(
    () => events.filter((event) => executionEventTypes.has(event.event_type)),
    [events],
  );
  const ragEvents = useMemo(() => events.filter((event) => ragEventTypes.has(event.event_type)), [events]);
  const timeline = useMemo<RealtimeTimelineItem[]>(
    () =>
      [...events]
        .reverse()
        .map((event) => ({
          event,
          label: formatEventLabel(event),
          tone: getTone(event),
        })),
    [events],
  );

  return {
    status,
    events,
    lastEvent,
    clearEvents,
    planningEvents,
    executionEvents,
    ragEvents,
    timeline,
  };
}
