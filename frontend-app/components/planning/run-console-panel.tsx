"use client";

import { Activity, AlertCircle, Clock3, Layers3, RadioTower, RotateCw, Workflow } from "lucide-react";

import { useRealtimeEvents } from "@/lib/hooks/use-realtime-events";
import type { PlanningWorkflowStage } from "@/lib/hooks/use-planning-workflow";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface RunConsolePanelProps {
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

function phaseLabel(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes("interpreting goal")) return "Goal interpretation";
  if (lower.includes("goal interpreted")) return "Goal interpretation complete";
  if (lower.includes("generating milestones")) return "Milestones";
  if (lower.includes("tasks generated") || lower.includes("decomposing tasks")) return "Task decomposition";
  if (lower.includes("plan assembled")) return "Plan assembly";
  if (lower.includes("critique")) return "Critique";
  if (lower.includes("routing execution")) return "Execution routing";
  if (lower.includes("execution jobs")) return "Execution jobs";
  if (lower.includes("planning finalized")) return "Completed";
  return "Planning";
}

export function RunConsolePanel({ stage, isWorking, error }: RunConsolePanelProps) {
  const { status, planningEvents, lastEvent } = useRealtimeEvents();
  const recentPlanningEvents = planningEvents.slice(0, 5);

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle>Run console</CardTitle>
        <CardDescription>
          One compact view for websocket health, workflow stage, and the current planning timeline.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">WebSocket</p>
            <div className="mt-3 flex items-center gap-2">
              <RadioTower className="h-4 w-4 text-primary" />
              <Badge variant={status === "connected" ? "success" : status === "error" ? "destructive" : "warning"}>{status}</Badge>
            </div>
          </div>

          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Stage</p>
            <div className="mt-3 flex items-center gap-2">
              <Workflow className="h-4 w-4 text-primary" />
              <Badge variant={getStageVariant(stage)}>{getStageLabel(stage)}</Badge>
            </div>
          </div>

          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Latest phase</p>
            <div className="mt-3 flex items-center gap-2">
              <Layers3 className="h-4 w-4 text-primary" />
              <Badge variant="outline">{lastEvent ? phaseLabel(lastEvent.message) : "Waiting"}</Badge>
            </div>
          </div>

          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Progress</p>
            <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
              <Clock3 className="h-4 w-4 text-primary" />
              {isWorking ? "Streaming live updates" : "Idle and ready"}
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
              <p className="mt-1 text-sm font-medium">{lastEvent ? lastEvent.message : "No realtime events received yet."}</p>
            </div>
            {lastEvent ? <Badge variant="outline">{lastEvent.event_type}</Badge> : null}
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-medium">Timeline</h3>
            <Badge variant="outline" className="gap-2">
              <RotateCw className={cn("h-3 w-3", isWorking ? "animate-spin" : "")} />
              Live feed
            </Badge>
          </div>

          {recentPlanningEvents.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border/70 bg-white/5 p-4 text-sm text-muted-foreground">
              Planning progress will appear here once backend-api publishes websocket updates.
            </div>
          ) : (
            <div className="space-y-3">
              {recentPlanningEvents.map((event) => (
                <div key={`${event.entity_id}-${event.timestamp}-${event.event_type}`} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="outline">{phaseLabel(event.message)}</Badge>
                        <Badge variant={event.event_type === "planning_completed" ? "success" : "warning"}>{event.event_type}</Badge>
                      </div>
                      <p className="text-sm font-medium">{event.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {event.entity_type} - {event.entity_id} - {event.timestamp}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
