"use client";

import type { FormEvent } from "react";
import { useMemo, useState } from "react";
import { CheckCircle2, HandCoins, RadioTower, Search, ShieldCheck, XCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/page-header";
import { backendApi } from "@/lib/api/backend-api";
import { useRealtimeEvents } from "@/lib/hooks/use-realtime-events";
import { useExecutionJob } from "@/lib/hooks/use-execution-job";
import type { ExecutionJobRead } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type ReviewOutcome = "approved" | "rejected";

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

export default function ApprovalsPage() {
  const { status: wsStatus, executionEvents } = useRealtimeEvents();
  const [jobIdInput, setJobIdInput] = useState("");
  const [trackedJobId, setTrackedJobId] = useState<string | null>(null);
  const [reviewResults, setReviewResults] = useState<Record<string, ReviewOutcome>>({});
  const [isReviewing, setIsReviewing] = useState(false);

  const jobQuery = useExecutionJob(trackedJobId);
  const approvalsQuery = useQuery({
    queryKey: ["approval-queue"],
    queryFn: async () => backendApi.listExecutionJobs("requires_approval"),
    refetchInterval: 4000,
  });

  const activeApprovalJob = jobQuery.data?.status === "requires_approval" ? jobQuery.data : null;
  const activeReviewOutcome = trackedJobId ? reviewResults[trackedJobId] : undefined;
  const reviewQueue = approvalsQuery.data ?? [];
  const reviewedCount = Object.keys(reviewResults).length;

  const recentApprovalEvents = useMemo(
    () => executionEvents.filter((event) => event.message.toLowerCase().includes("approval")),
    [executionEvents],
  );

  function handleTrackJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setTrackedJobId(jobIdInput.trim() || null);
  }

  async function handleReview(jobId: string, outcome: ReviewOutcome) {
    setIsReviewing(true);
    try {
      if (outcome === "approved") {
        await backendApi.approveExecutionJob(jobId);
      } else {
        await backendApi.rejectExecutionJob(jobId);
      }
      setReviewResults((current) => ({ ...current, [jobId]: outcome }));
      await approvalsQuery.refetch();
      if (trackedJobId === jobId) {
        await jobQuery.refetch();
      }
    } finally {
      setIsReviewing(false);
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Approvals"
        description="Review approval-required execution jobs and keep a human-in-the-loop queue for sensitive work."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">WebSocket</p>
            <div className="mt-3 flex items-center gap-2">
              <RadioTower className="h-4 w-4 text-primary" />
              <Badge variant={wsStatus === "connected" ? "success" : wsStatus === "error" ? "destructive" : "warning"}>{wsStatus}</Badge>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Pending</p>
            <p className="mt-3 text-3xl font-semibold">{reviewQueue.length}</p>
          </CardContent>
        </Card>
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Tracked</p>
            <p className="mt-3 text-3xl font-semibold">{trackedJobId ? 1 : 0}</p>
          </CardContent>
        </Card>
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Reviewed</p>
            <p className="mt-3 text-3xl font-semibold">{reviewedCount}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Approval queue</CardTitle>
            <CardDescription>
              Track a job ID, then approve or reject the decision once backend-api surfaces the task for review.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <form className="flex gap-3" onSubmit={handleTrackJob}>
              <Input
                value={jobIdInput}
                onChange={(event) => setJobIdInput(event.target.value)}
                placeholder="Approval-required job ID"
              />
              <Button type="submit" variant="outline">
                <Search className="h-4 w-4" />
                Track
              </Button>
            </form>

            <div className="grid gap-3 md:grid-cols-2">
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
                <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Queue size</p>
                <div className="mt-3 flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  <Badge variant="outline">{reviewQueue.length}</Badge>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <HandCoins className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-medium">Pending approval jobs</h3>
              </div>
              {approvalsQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Loading approval queue...</p>
              ) : reviewQueue.length === 0 ? (
                <p className="text-sm text-muted-foreground">No approval-required jobs are currently queued.</p>
              ) : (
                <div className="space-y-3">
                  {reviewQueue.map((job) => (
                    <div key={job.job_id} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-medium">{job.job_id}</p>
                          <p className="text-sm text-muted-foreground">{job.decision.reason}</p>
                        </div>
                        <Badge variant={statusVariant(job.status)}>{job.status}</Badge>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {job.decision.tool_category ? <Badge variant="secondary">{job.decision.tool_category}</Badge> : null}
                        {job.decision.tool_name ? <Badge variant="outline">{job.decision.tool_name}</Badge> : null}
                        <Badge variant="outline">{job.decision.action_mode}</Badge>
                      </div>

                      <div className="mt-4 flex flex-wrap gap-2">
                        <Button type="button" size="sm" onClick={() => handleReview(job.job_id, "approved")} disabled={isReviewing}>
                          <CheckCircle2 className="h-4 w-4" />
                          Approve
                        </Button>
                        <Button type="button" size="sm" variant="outline" onClick={() => handleReview(job.job_id, "rejected")} disabled={isReviewing}>
                          <XCircle className="h-4 w-4" />
                          Reject
                        </Button>
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
              <CardTitle>Approval detail</CardTitle>
              <CardDescription>View the currently tracked approval-required job and review state.</CardDescription>
            </CardHeader>
            <CardContent>
              {activeApprovalJob ? (
                <div className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Job ID</p>
                      <p className="mt-2 break-all font-medium">{activeApprovalJob.job_id}</p>
                    </div>
                    <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Status</p>
                      <div className="mt-2 flex items-center gap-2">
                        <Badge variant={statusVariant(activeApprovalJob.status)}>{activeApprovalJob.status}</Badge>
                        {activeReviewOutcome ? (
                          <Badge variant={activeReviewOutcome === "approved" ? "success" : "destructive"}>
                            {activeReviewOutcome}
                          </Badge>
                        ) : null}
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Decision</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Badge variant={statusVariant(activeApprovalJob.status)}>{activeApprovalJob.decision.action_mode}</Badge>
                      {activeApprovalJob.decision.tool_category ? <Badge variant="secondary">{activeApprovalJob.decision.tool_category}</Badge> : null}
                      {activeApprovalJob.decision.tool_name ? <Badge variant="outline">{activeApprovalJob.decision.tool_name}</Badge> : null}
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">{activeApprovalJob.decision.reason}</p>
                  </div>

                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Task payload</p>
                    <pre className="mt-3 max-h-[14rem] overflow-auto text-xs leading-6 text-muted-foreground">
                      {JSON.stringify(activeApprovalJob.task, null, 2)}
                    </pre>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <Button type="button" onClick={() => handleReview(activeApprovalJob.job_id, "approved")} disabled={isReviewing}>
                      <CheckCircle2 className="h-4 w-4" />
                      Approve
                    </Button>
                    <Button type="button" variant="outline" onClick={() => handleReview(activeApprovalJob.job_id, "rejected")} disabled={isReviewing}>
                      <XCircle className="h-4 w-4" />
                      Reject
                    </Button>
                  </div>

                  <p className="text-xs text-muted-foreground">Approval actions now call backend-api and update the live job state.</p>
                </div>
              ) : (
                <div className="rounded-3xl border border-dashed border-border/70 bg-white/5 p-8 text-center text-sm text-muted-foreground">
                  Track a job with status requires_approval to review it here.
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Approval-related events</CardTitle>
              <CardDescription>Realtime hints from execution events while jobs move toward human review.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {recentApprovalEvents.length === 0 ? (
                <p className="text-sm text-muted-foreground">No approval-related websocket events yet.</p>
              ) : (
                recentApprovalEvents.map((event) => (
                  <div key={`${event.entity_id}-${event.timestamp}`} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-medium">{event.message}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {event.entity_type} - {event.entity_id} - {event.timestamp}
                        </p>
                      </div>
                      <Badge variant={event.event_type === "execution_job_failed" ? "destructive" : "warning"}>
                        {event.event_type}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
