"use client";

import Link from "next/link";
import { Loader2, RefreshCw, FolderPlus } from "lucide-react";

import { useWorkspaces } from "@/lib/hooks/use-workspaces";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface WorkspaceSelectorProps {
  userId?: string | null;
  workspaceId: string;
  onChange: (workspaceId: string) => void;
  label?: string;
  description?: string;
  className?: string;
}

export function WorkspaceSelector({
  userId,
  workspaceId,
  onChange,
  label = "Workspace",
  description = "Choose the workspace that owns this goal or planning run.",
  className,
}: WorkspaceSelectorProps) {
  const workspacesQuery = useWorkspaces(userId);
  const workspaces = workspacesQuery.data ?? [];

  return (
    <div className={className}>
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium">{label}</p>
            <p className="text-xs text-muted-foreground">{description}</p>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={() => workspacesQuery.refetch()} disabled={!userId}>
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>

        {workspacesQuery.isLoading ? (
          <div className="flex items-center gap-3 rounded-xl border border-border/70 bg-background/70 px-4 py-3 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading workspaces...
          </div>
        ) : workspaces.length > 0 ? (
          <select
            value={workspaceId}
            onChange={(event) => onChange(event.target.value)}
            className="flex h-10 w-full rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm outline-none transition-colors focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary"
            disabled={!userId}
          >
            <option value="">Select a workspace</option>
            {workspaces.map((workspace) => (
              <option key={workspace.id} value={workspace.id}>
                {workspace.name} {workspace.description ? `- ${workspace.description}` : ""}
              </option>
            ))}
          </select>
        ) : (
          <Card className="border-dashed border-border/70 bg-background/50">
            <CardContent className="flex flex-col gap-3 p-4">
              <div>
                <p className="text-sm font-medium">No workspaces yet</p>
                <p className="text-xs text-muted-foreground">Create a workspace first, then come back here to continue.</p>
              </div>
              <Button asChild variant="outline" className="w-fit">
                <Link href="/workspaces">
                  <FolderPlus className="h-4 w-4" />
                  Create workspace
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {workspacesQuery.isError ? (
          <p className="text-xs text-destructive">
            Unable to load workspaces. {workspacesQuery.error instanceof Error ? workspacesQuery.error.message : ""}
          </p>
        ) : null}
      </div>
    </div>
  );
}
