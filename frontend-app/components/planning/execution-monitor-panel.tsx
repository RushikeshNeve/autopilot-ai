"use client";

import { Activity, AlertCircle, Clock3, RadioTower, RotateCw } from "lucide-react";

import { useRealtimeEvents } from "@/lib/hooks/use-realtime-events";
import type { PlanningWorkflowStage } from "@/lib/hooks/use-planning-workflow";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ExecutionMonitorPanelProps {
  stage: PlanningWorkflowStage;
  isWorking: boolean;
  error?: string | null;
}

function getStageLabel(stage: PlanningWorkflowStage): string {
  switch (stage) {
    case "creating_goal":
      return "Creating goal";
    case "queued":
      return "Queued";
    case "running":
      return "Running";
    case "completed":
      return "Completed";
    case "error":
      return "Needs attention";
    case "idle":
    default:
      return "Idle";
  }
}

function getStageVariant(stage: PlanningWorkflowStage): "default" | "success" | "warning" | "destructive" {
  switch (stage) {
    case "completed":
      return "success";
    case "error":
      return "destructive";
    case "creating_goal":
    case "queued":
    case "running":
      return "warning";
    case "idle":
    default:
      return "default";
  }
}

export function ExecutionMonitorPanel({ stage, isWorking, error }: ExecutionMonitorPanelProps) {
  const { status, timeline, lastEvent } = useRealtimeEvents();

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle>Realtime execution monitor</CardTitle>
        <CardDescription>
          Tracks backend-api websocket updates while the planning workflow runs.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">WebSocket</p>
            <div className="mt-3 flex items-center gap-2">
              <RadioTower className="h-4 w-4 text-primary" />
              <Badge variant={status === "connected" ? "success" : status === "error" ? "destructive" : "warning"}>
                {status}
              </Badge>
            </div>
          </div>
          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Workflow stage</p>
            <div className="mt-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              <Badge variant={getStageVariant(stage)}>{getStageLabel(stage)}</Badge>
            </div>
          </div>
          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Progress</p>
            <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
              <Clock3 className="h-4 w-4 text-primary" />
              {isWorking ? "Waiting for realtime updates..." : "Idle and ready"}
            </div>
          </div>
        </div>

        {error ? (
          <div className="flex items-start gap-3 rounded-2xl border border-destructive/30 bg-destructive/10 p-4">
            <AlertCircle className="mt-0.5 h-4 w-4 text-destructive" />
            <div>
              <p className="font-medium text-destructive">Planning failed</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        ) : null}

        <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Latest event</p>
              <p className="mt-1 text-sm font-medium">
                {lastEvent ? lastEvent.message : "No realtime events received yet."}
              </p>
            </div>
            {lastEvent ? <Badge variant="outline">{lastEvent.event_type}</Badge> : null}
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Progress timeline</h3>
            <Badge variant="outline" className="gap-2">
              <RotateCw className={cn("h-3 w-3", isWorking ? "animate-spin" : "")} />
              Live feed
            </Badge>
          </div>

          <div className="space-y-3">
            {timeline.length === 0 ? (
              <div className="rounded-2xl border border-border/70 bg-white/5 p-4 text-sm text-muted-foreground">
                Realtime planning and execution events will appear here once backend-api publishes them.
              </div>
            ) : (
              timeline.map(({ event, label, tone }) => (
                <div key={`${event.entity_id}-${event.timestamp}-${event.event_type}`} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <p className="font-medium">{label}</p>
                      <p className="text-sm text-muted-foreground">{event.message}</p>
                    </div>
                    <Badge
                      variant={
                        tone === "success"
                          ? "success"
                          : tone === "warning"
                            ? "warning"
                            : tone === "destructive"
                              ? "destructive"
                              : "outline"
                      }
                    >
                      {event.event_type}
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {event.entity_type} - {event.entity_id} - {event.timestamp}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
