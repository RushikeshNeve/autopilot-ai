"use client";

import { useQuery } from "@tanstack/react-query";

import { backendApi } from "@/lib/api/backend-api";
import type { Workspace } from "@/lib/types";

export function useWorkspaces(userId: string | null | undefined) {
  return useQuery<Workspace[]>({
    queryKey: ["workspaces", userId],
    enabled: Boolean(userId),
    queryFn: async () => backendApi.listWorkspaces(userId as string),
    staleTime: 30_000,
  });
}
