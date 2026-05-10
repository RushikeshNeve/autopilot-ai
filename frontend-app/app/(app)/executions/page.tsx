"use client";

import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { Activity, History, RadioTower, Search, Workflow } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { useRealtimeEvents } from "@/lib/hooks/use-realtime-events";
import { useExecutionJob } from "@/lib/hooks/use-execution-job";
import type { ExecutionJobRead } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

function statusVariant(status?: ExecutionJobRead["status"]): "default" | "success" | "warning" | "destructive" | "outline" {
  switch (status) {
    case "completed":
      return "success";
    case "failed":
      return "destructive";
    case "running":
    case "queued":
      return "warning";
    case "requires_approval":
      return "outline";
    default:
      return "default";
  }
}

export default function ExecutionsPage() {
  const { status: wsStatus, executionEvents, lastEvent } = useRealtimeEvents();
  const [jobIdInput, setJobIdInput] = useState("");
  const [trackedJobId, setTrackedJobId] = useState<string | null>(null);
  const [recentJobs, setRecentJobs] = useState<ExecutionJobRead[]>([]);

  const jobQuery = useExecutionJob(trackedJobId);

  useEffect(() => {
    if (!jobQuery.data) {
      return;
    }

    setRecentJobs((current) => {
      const next = current.filter((job) => job.job_id !== jobQuery.data.job_id);
      return [jobQuery.data, ...next].slice(0, 6);
    });
  }, [jobQuery.data]);

  const activeJob = jobQuery.data ?? null;

  const approvalJobs = useMemo(
    () => recentJobs.filter((job) => job.status === "requires_approval"),
    [recentJobs],
  );
  const runningJobs = useMemo(
    () => recentJobs.filter((job) => job.status === "running" || job.status === "queued"),
    [recentJobs],
  );
  const completedJobs = useMemo(
    () => recentJobs.filter((job) => job.status === "completed"),
    [recentJobs],
  );

  function handleTrackJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setTrackedJobId(jobIdInput.trim() || null);
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Executions"
        description="Monitor execution jobs, follow websocket progress, and poll job status when live updates are unavailable."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">WebSocket</p>
            <div className="mt-3 flex items-center gap-2">
              <RadioTower className="h-4 w-4 text-primary" />
              <Badge variant={wsStatus === "connected" ? "success" : wsStatus === "error" ? "destructive" : "warning"}>
                {wsStatus}
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Tracked</p>
            <p className="mt-3 text-3xl font-semibold">{activeJob ? 1 : 0}</p>
          </CardContent>
        </Card>
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Approval queue</p>
            <p className="mt-3 text-3xl font-semibold">{approvalJobs.length}</p>
          </CardContent>
        </Card>
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Completed</p>
            <p className="mt-3 text-3xl font-semibold">{completedJobs.length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Job monitor</CardTitle>
            <CardDescription>
              Paste an execution job ID to track queued, running, completed, failed, or approval-required work.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <form className="flex gap-3" onSubmit={handleTrackJob}>
              <Input
                value={jobIdInput}
                onChange={(event) => setJobIdInput(event.target.value)}
                placeholder="Execution job ID"
              />
              <Button type="submit" variant="outline">
                <Search className="h-4 w-4" />
                Track
              </Button>
            </form>

            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">WebSocket</p>
                <div className="mt-3 flex items-center gap-2">
                  <RadioTower className="h-4 w-4 text-primary" />
                  <Badge variant={wsStatus === "connected" ? "success" : wsStatus === "error" ? "destructive" : "warning"}>
                    {wsStatus}
                  </Badge>
                </div>
              </div>
              <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Tracked job</p>
                <div className="mt-3 flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary" />
                  <Badge variant={statusVariant(activeJob?.status)}>{activeJob?.status ?? "idle"}</Badge>
                </div>
              </div>
              <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Known jobs</p>
                <div className="mt-3 flex items-center gap-2">
                  <History className="h-4 w-4 text-primary" />
                  <Badge variant="outline">{recentJobs.length}</Badge>
                </div>
              </div>
            </div>

            {jobQuery.isFetching && trackedJobId ? (
              <div className="rounded-2xl border border-border/70 bg-white/5 p-4 text-sm text-muted-foreground">
                Polling backend-api for live job status...
              </div>
            ) : null}

            {jobQuery.error ? (
              <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {jobQuery.error instanceof Error ? jobQuery.error.message : "Unable to load execution job"}
              </div>
            ) : null}

              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Workflow className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-medium">Approval-required jobs</h3>
                </div>
              {approvalJobs.length === 0 ? (
                <p className="text-sm text-muted-foreground">No approval-required jobs have been tracked yet.</p>
              ) : (
                <div className="space-y-3">
                  {approvalJobs.map((job) => (
                    <div key={job.job_id} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-medium">{job.job_id}</p>
                          <p className="text-sm text-muted-foreground">Task routed to human review</p>
                        </div>
                        <Badge variant="outline">{job.status}</Badge>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {job.decision.tool_category ? <Badge variant="secondary">{job.decision.tool_category}</Badge> : null}
                        {job.decision.tool_name ? <Badge variant="outline">{job.decision.tool_name}</Badge> : null}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Job details</CardTitle>
              <CardDescription>Current job payload, decision, and latest backend state.</CardDescription>
            </CardHeader>
            <CardContent>
              {activeJob ? (
                <div className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Status</p>
                      <div className="mt-2 flex items-center gap-2">
                        <Badge variant={statusVariant(activeJob.status)}>{activeJob.status}</Badge>
                        {activeJob.error ? <Badge variant="destructive">Error</Badge> : null}
                      </div>
                    </div>
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Decision</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Badge variant={statusVariant(activeJob.status)}>{activeJob.decision.action_mode}</Badge>
                      {activeJob.decision.tool_category ? <Badge variant="secondary">{activeJob.decision.tool_category}</Badge> : null}
                      {activeJob.decision.tool_name ? <Badge variant="outline">{activeJob.decision.tool_name}</Badge> : null}
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">{activeJob.decision.reason}</p>
                  </div>
                </div>

                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Task payload</p>
                    <pre className="mt-3 max-h-[14rem] overflow-auto text-xs leading-6 text-muted-foreground">
                      {JSON.stringify(activeJob.task, null, 2)}
                    </pre>
                  </div>

                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Result</p>
                    <pre className="mt-3 max-h-[14rem] overflow-auto text-xs leading-6 text-muted-foreground">
                      {activeJob.result ? JSON.stringify(activeJob.result, null, 2) : "No result yet."}
                    </pre>
                  </div>

                  {activeJob.error ? (
                    <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                      {activeJob.error}
                    </div>
                  ) : null}

                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Job result</p>
                      <p className="mt-2 text-sm font-medium">
                        {activeJob.result ? "Available" : "Not yet available"}
                      </p>
                    </div>
                    <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Recent running</p>
                      <p className="mt-2 text-sm font-medium">{runningJobs.length}</p>
                    </div>
                    <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Approval jobs</p>
                      <p className="mt-2 text-sm font-medium">{approvalJobs.length}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-3xl border border-dashed border-border/70 bg-white/5 p-8 text-center text-sm text-muted-foreground">
                  Track a job to see live status, polling updates, and execution payload details.
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Realtime event feed</CardTitle>
              <CardDescription>Execution events from backend-api websocket updates.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {executionEvents.length === 0 ? (
                <p className="text-sm text-muted-foreground">No execution events yet.</p>
              ) : (
                executionEvents.map((event) => (
                  <div key={`${event.entity_id}-${event.timestamp}`} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium">{event.message}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {event.entity_type} - {event.entity_id} - {event.timestamp}
                        </p>
                      </div>
                      <Badge
                        variant={
                          event.event_type === "execution_job_completed"
                            ? "success"
                            : event.event_type === "execution_job_failed"
                              ? "destructive"
                              : "warning"
                        }
                      >
                        {event.event_type}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
              {lastEvent ? (
                <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Last websocket event</p>
                  <p className="mt-2 text-sm">{lastEvent.message}</p>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
