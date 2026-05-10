"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/layout/page-header";
import { useAuth } from "@/components/providers/auth-provider";
import { backendApi } from "@/lib/api/backend-api";
import type { GoalCreateResponse } from "@/lib/types";
import { useWorkspaces } from "@/lib/hooks/use-workspaces";
import { WorkspaceSelector } from "@/components/workspaces/workspace-selector";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function GoalsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [workspaceId, setWorkspaceId] = useState("");
  const [title, setTitle] = useState("");
  const [goalText, setGoalText] = useState("");
  const [constraints, setConstraints] = useState("");
  const [domainHint, setDomainHint] = useState("");
  const [triggerPlanning, setTriggerPlanning] = useState(false);
  const [response, setResponse] = useState<GoalCreateResponse | null>(null);
  const workspacesQuery = useWorkspaces(user?.id);

  useEffect(() => {
    if (!workspaceId && workspacesQuery.data && workspacesQuery.data.length > 0) {
      setWorkspaceId(workspacesQuery.data[0].id);
    }
  }, [workspaceId, workspacesQuery.data]);

  const createGoalMutation = useMutation({
    mutationFn: async () => {
      return backendApi.createGoal({
        workspace_id: workspaceId,
        title,
        goal_text: goalText,
        constraints: constraints
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        domain_hint: domainHint || null,
        trigger_planning: triggerPlanning,
      });
    },
    onSuccess: (data) => {
      setResponse(data);
      if (data.planning_job_id) {
        router.push(`/plans?jobId=${encodeURIComponent(data.planning_job_id)}`);
      }
    },
  });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createGoalMutation.mutateAsync();
    } catch {
      // Error state is surfaced by the mutation and rendered below.
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Goals"
        description="Capture a goal and optionally trigger backend planning. Use the Planning workspace for the full realtime flow."
        actions={<Badge variant="outline">React Query ready</Badge>}
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Create goal</CardTitle>
            <CardDescription>
              backend-api will persist the goal and can optionally orchestrate planning through ai-service.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <WorkspaceSelector userId={user?.id} workspaceId={workspaceId} onChange={setWorkspaceId} />
              <div className="space-y-2">
                <Label htmlFor="title">Goal title</Label>
                <Input id="title" value={title} onChange={(event) => setTitle(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="goalText">Goal description</Label>
                <Textarea
                  id="goalText"
                  value={goalText}
                  onChange={(event) => setGoalText(event.target.value)}
                  placeholder="Describe what you want to achieve."
                  rows={6}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="constraints">Constraints</Label>
                <Textarea
                  id="constraints"
                  value={constraints}
                  onChange={(event) => setConstraints(event.target.value)}
                  placeholder="Comma-separated constraints"
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="domainHint">Domain hint</Label>
                <Input
                  id="domainHint"
                  value={domainHint}
                  onChange={(event) => setDomainHint(event.target.value)}
                  placeholder="jobs, study, fitness, projects"
                />
              </div>
              <label className="flex items-center gap-3 rounded-2xl border border-border/70 bg-white/5 px-4 py-3 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  checked={triggerPlanning}
                  onChange={(event) => setTriggerPlanning(event.target.checked)}
                  className="h-4 w-4 rounded border-border bg-background"
                />
                Trigger backend planning after storing the goal
              </label>
              {createGoalMutation.error ? (
                <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {createGoalMutation.error instanceof Error
                    ? createGoalMutation.error.message
                    : "Unable to create goal"}
                </div>
              ) : null}
              <Button type="submit" className="w-full" disabled={createGoalMutation.isPending}>
                {createGoalMutation.isPending ? "Creating goal..." : "Create goal"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Goal response</CardTitle>
            <CardDescription>
              Backend response rendered for quick inspection and frontend integration debugging.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Signed in user</p>
                <p className="mt-2 font-medium">{user?.email ?? "Unknown"}</p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Goal mode</p>
                <p className="mt-2 font-medium">{triggerPlanning ? "Goal + planning" : "Goal only"}</p>
              </div>
            </div>

            {response ? (
              <div className="space-y-4">
                <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Goal ID</p>
                  <p className="mt-2 break-all font-medium">{response.goal.id}</p>
                </div>
                <pre className="max-h-[32rem] overflow-auto rounded-2xl border border-border/70 bg-black/30 p-4 text-xs leading-6 text-muted-foreground">
                  {JSON.stringify(response, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="rounded-3xl border border-dashed border-border/70 bg-white/5 p-8 text-center text-sm text-muted-foreground">
                Create a goal to see the backend response here.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
