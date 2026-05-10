"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { useWebSocket } from "@/components/providers/websocket-provider";
import { backendApi } from "@/lib/api/backend-api";
import type { Goal, Plan, PlanningWorkspaceResult, RawPlanningResponse } from "@/lib/types";

export type PlanningWorkflowStage = "idle" | "creating_goal" | "queued" | "running" | "completed" | "error";

export interface PlanningWorkflowInput {
  workspaceId: string;
  title: string;
  goalText: string;
  constraints: string[];
  domainHint?: string | null;
  submitExecutionJobs: boolean;
}

function normalizeRawResponse(raw_ai_response: RawPlanningResponse): RawPlanningResponse {
  return raw_ai_response ?? {};
}

function normalizeResult(goal: Goal, plan: Plan, raw_ai_response: RawPlanningResponse): PlanningWorkspaceResult {
  return {
    goal,
    plan,
    raw_ai_response: normalizeRawResponse(raw_ai_response),
  };
}

export function usePlanningWorkflow() {
  const { events } = useWebSocket();
  const [stage, setStage] = useState<PlanningWorkflowStage>("idle");
  const [result, setResult] = useState<PlanningWorkspaceResult | null>(null);
  const [goal, setGoal] = useState<Goal | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const mutation = useMutation({
    onMutate: () => {
      setResult(null);
      setGoal(null);
      setJobId(null);
      setStage("creating_goal");
    },
    mutationFn: async (input: PlanningWorkflowInput) => {
      const goalResponse = await backendApi.createGoal({
        workspace_id: input.workspaceId,
        title: input.title,
        goal_text: input.goalText,
        constraints: input.constraints,
        domain_hint: input.domainHint ?? null,
        trigger_planning: false,
      });

      setGoal(goalResponse.goal);
      setStage("queued");

      const jobResponse = await backendApi.finalizePlanAsync({
        goal_id: goalResponse.goal.id,
        submit_execution_jobs: input.submitExecutionJobs,
      });

      setJobId(jobResponse.job_id);
      return {
        goal: goalResponse.goal,
        job_id: jobResponse.job_id,
      };
    },
    onError: () => {
      setStage("error");
    },
  });

  const jobQuery = useQuery({
    queryKey: ["planning-job", jobId],
    enabled: Boolean(jobId),
    queryFn: async () => backendApi.getPlanFinalizeJob(jobId as string),
    refetchInterval: (query) => {
      if (stage === "completed" || stage === "error") {
        return false;
      }
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") {
        return false;
      }
      return 2000;
    },
  });

  useEffect(() => {
    const job = jobQuery.data;
    if (!job) {
      return;
    }

    if (job.status === "queued") {
      setStage("queued");
      return;
    }

    if (job.status === "running") {
      setStage("running");
      return;
    }

    if (job.status === "completed" && job.result && goal) {
      setResult(normalizeResult(goal, job.result.plan, job.result.raw_ai_response));
      setStage("completed");
      return;
    }

    if (job.status === "failed") {
      setStage("error");
    }
  }, [goal, jobQuery.data]);

  useEffect(() => {
    if (!jobId || !goal || stage === "completed" || stage === "error") {
      return;
    }

    const relevantEvents = [...events].reverse().filter((event) => event.entity_id === jobId);
    for (const event of relevantEvents) {
      if (event.event_type === "planning_started") {
        setStage("running");
        continue;
      }

      if (event.event_type === "planning_progress") {
        setStage("running");
        continue;
      }

      if (event.event_type === "planning_completed") {
        const data = event.data as Record<string, unknown> | undefined;
        const payload = data?.result;
        if (
          payload &&
          typeof payload === "object" &&
          "plan" in payload &&
          "raw_ai_response" in payload
        ) {
          const response = payload as { plan: Plan; raw_ai_response: RawPlanningResponse };
          setResult(normalizeResult(goal, response.plan, response.raw_ai_response));
          setStage("completed");
          return;
        }
      }
    }
  }, [events, goal, jobId, stage]);

  const combinedError = mutation.error ?? jobQuery.error ?? null;

  return useMemo(
    () => ({
      stage,
      result,
      error: combinedError,
      isPlanning: mutation.isPending || stage === "queued" || stage === "running" || jobQuery.isFetching,
      submitPlanning: mutation.mutateAsync,
      reset: () => {
        mutation.reset();
        setResult(null);
        setGoal(null);
        setJobId(null);
        setStage("idle");
      },
    }),
    [combinedError, jobQuery.isFetching, mutation, result, stage],
  );
}
