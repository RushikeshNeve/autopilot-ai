"use client";

import { useQuery } from "@tanstack/react-query";

import { backendApi } from "@/lib/api/backend-api";
import type { ExecutionJobRead } from "@/lib/types";

const pollingStatuses = new Set<ExecutionJobRead["status"]>(["queued", "running", "requires_approval"]);

export function useExecutionJob(jobId: string | null | undefined) {
  return useQuery({
    queryKey: ["execution-job", jobId],
    enabled: Boolean(jobId),
    queryFn: async () => {
      if (!jobId) {
        throw new Error("Job id is required");
      }
      return backendApi.getExecutionJob(jobId);
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && pollingStatuses.has(status) ? 4000 : false;
    },
  });
}
