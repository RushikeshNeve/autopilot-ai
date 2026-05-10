"use client";

import { Clock3, Layers3, ListChecks, Sparkles, Workflow } from "lucide-react";

import { useRealtimeEvents } from "@/lib/hooks/use-realtime-events";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface PlanningTimelinePanelProps {
  stage: "idle" | "creating_goal" | "queued" | "running" | "completed" | "error";
}

function stageLabel(stage: PlanningTimelinePanelProps["stage"]): string {
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

export function PlanningTimelinePanel({ stage }: PlanningTimelinePanelProps) {
  const { planningEvents, lastEvent } = useRealtimeEvents();
  const recentPlanningEvents = planningEvents.slice(0, 6);

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle>Planning timeline</CardTitle>
        <CardDescription>Compact stage-by-stage progress for the current planning run.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Stage</p>
            <div className="mt-3 flex items-center gap-2">
              <Workflow className="h-4 w-4 text-primary" />
              <Badge variant={stage === "completed" ? "success" : stage === "error" ? "destructive" : stage === "running" || stage === "queued" ? "warning" : "outline"}>
                {stageLabel(stage)}
              </Badge>
            </div>
          </div>
          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Planning events</p>
            <p className="mt-3 text-2xl font-semibold">{planningEvents.length}</p>
          </div>
          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Latest phase</p>
            <div className="mt-3 flex items-center gap-2">
              <Layers3 className="h-4 w-4 text-primary" />
              <Badge variant="outline">{lastEvent ? phaseLabel(lastEvent.message) : "Waiting"}</Badge>
            </div>
          </div>
          <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Last update</p>
            <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
              <Clock3 className="h-4 w-4 text-primary" />
              {lastEvent ? lastEvent.timestamp : "No updates yet"}
            </div>
          </div>
        </div>

        <div className="space-y-3">
          {recentPlanningEvents.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border/70 bg-white/5 p-4 text-sm text-muted-foreground">
              Planning progress will appear here as backend-api publishes websocket updates.
            </div>
          ) : (
            recentPlanningEvents.map((event) => (
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
            ))
          )}
        </div>

        {lastEvent ? (
          <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Latest planning note</p>
            <p className="mt-2 text-sm text-muted-foreground">{lastEvent.message}</p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
