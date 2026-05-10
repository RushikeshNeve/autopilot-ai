"use client";

import type { FormEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";

import { PlanOutputPanel } from "@/components/planning/plan-output-panel";
import { backendApi } from "@/lib/api/backend-api";
import type { Goal, Plan, PlanFinalizeJobRead, PlanningWorkspaceResult } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/layout/page-header";

export default function PlansPage() {
  const searchParams = useSearchParams();
  const initialJobId = searchParams.get("jobId") ?? null;
  const [goalId, setGoalId] = useState("");
  const [submitExecutionJobs, setSubmitExecutionJobs] = useState(true);
  const [response, setResponse] = useState<PlanFinalizeJobRead | null>(null);
  const [jobId, setJobId] = useState<string | null>(initialJobId);
  const [planOverride, setPlanOverride] = useState<Plan | null>(null);
  const [isCreatingExecutionJobs, setIsCreatingExecutionJobs] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const planOutputRef = useRef<HTMLDivElement | null>(null);

  const jobQuery = useQuery({
    queryKey: ["plan-job", jobId],
    enabled: Boolean(jobId),
    queryFn: async () => backendApi.getPlanFinalizeJob(jobId as string),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") {
        return false;
      }
      return 2000;
    },
  });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      setResponse(null);
      setPlanOverride(null);
      const result = await backendApi.finalizePlanAsync({
        goal_id: goalId,
        submit_execution_jobs: submitExecutionJobs,
      });
      setJobId(result.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to finalize plan");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCreateExecutionJobs() {
    if (!planResult?.plan.id) {
      return;
    }

    setError(null);
    setIsCreatingExecutionJobs(true);
    try {
      const updatedPlan = await backendApi.createExecutionJobsForPlan(planResult.plan.id);
      setPlanOverride(updatedPlan);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create execution jobs");
    } finally {
      setIsCreatingExecutionJobs(false);
    }
  }

  useEffect(() => {
    if (jobQuery.data) {
      setResponse(jobQuery.data);
    }
  }, [jobQuery.data]);

  useEffect(() => {
    if (initialJobId && initialJobId !== jobId) {
      setJobId(initialJobId);
    }
  }, [initialJobId, jobId]);

  const goalQuery = useQuery({
    queryKey: ["goal", response?.goal_id],
    enabled: Boolean(response?.status === "completed" && response.result && response.goal_id),
    queryFn: async () => backendApi.getGoal(response?.goal_id as string),
  });

  const planResult = useMemo<PlanningWorkspaceResult | null>(() => {
    if (!response?.result) {
      return null;
    }

    const goal: Goal | null = goalQuery.data ?? null;
    if (!goal) {
      return null;
    }

    return {
      goal,
      plan: planOverride ?? response.result.plan,
      raw_ai_response: response.result.raw_ai_response,
    };
  }, [goalQuery.data, planOverride, response]);

  useEffect(() => {
    if (planResult && planOutputRef.current) {
      planOutputRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [planResult]);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Plans"
        description="Send a goal to backend-api for final planning, ai-service orchestration, and optional execution job submission."
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Finalize plan</CardTitle>
            <CardDescription>Use a stored goal ID to request a fresh planning result from backend-api.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="goalId">Goal ID</Label>
                <Input id="goalId" value={goalId} onChange={(event) => setGoalId(event.target.value)} required />
              </div>
              <label className="flex items-center gap-3 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  checked={submitExecutionJobs}
                  onChange={(event) => setSubmitExecutionJobs(event.target.checked)}
                  className="h-4 w-4 rounded border-border bg-background"
                />
                Submit execution jobs for auto-execute / approval-ready decisions
              </label>
              {error ? <p className="text-sm text-destructive">{error}</p> : null}
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? "Queued..." : "Queue plan finalization"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Plan response</CardTitle>
            <CardDescription>
              The job status updates live while the backend finishes the plan in the background.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {response ? (
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Job</p>
                    <p className="mt-2 font-medium">{response.job_id}</p>
                  </div>
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Status</p>
                    <p className="mt-2 font-medium">{response.status}</p>
                  </div>
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Goal</p>
                    <p className="mt-2 font-medium">{response.goal_id.slice(0, 8)}</p>
                  </div>
                </div>
              ) : null}

              {planResult ? (
                <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Execution phase</p>
                      <p className="mt-2 font-medium">
                        {planResult.plan.execution_jobs.length > 0
                          ? `${planResult.plan.execution_jobs.length} execution job(s) created`
                          : "No execution jobs created yet"}
                      </p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Create execution jobs now to move auto-execute and approval-required tasks into the runtime queue.
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleCreateExecutionJobs}
                      disabled={isCreatingExecutionJobs || planResult.plan.execution_jobs.length > 0}
                    >
                      {isCreatingExecutionJobs ? "Creating..." : "Create execution jobs"}
                    </Button>
                  </div>
                </div>
              ) : null}

              {!planResult ? (
                <div className="rounded-2xl border border-dashed border-border/70 bg-white/5 p-6 text-sm text-muted-foreground">
                  Queue a plan to inspect the structured response here.
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>
      <div ref={planOutputRef} className="scroll-mt-24">
        {planResult ? (
          <div className="mb-4 rounded-3xl border border-primary/30 bg-primary/5 p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Plan ready</p>
            <p className="mt-2 text-sm text-muted-foreground">
              The structured result is rendered below, including milestones, tasks, critique, and execution decisions.
            </p>
          </div>
        ) : null}
        <PlanOutputPanel result={planResult} isLoading={isSubmitting || jobQuery.isFetching} />
      </div>
    </div>
  );
}
