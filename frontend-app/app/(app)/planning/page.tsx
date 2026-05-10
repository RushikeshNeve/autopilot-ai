"use client";

import type { FormEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { ArrowRight, Workflow } from "lucide-react";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/layout/page-header";
import { PlanOutputPanel } from "@/components/planning/plan-output-panel";
import { RunConsolePanel } from "@/components/planning/run-console-panel";
import { usePlanningWorkflow } from "@/lib/hooks/use-planning-workflow";
import { useWorkspaces } from "@/lib/hooks/use-workspaces";
import { WorkspaceSelector } from "@/components/workspaces/workspace-selector";

export default function PlanningWorkspacePage() {
  const { user } = useAuth();
  const { result, stage, error, isPlanning, submitPlanning, reset } = usePlanningWorkflow();
  const planOutputRef = useRef<HTMLDivElement | null>(null);
  const [workspaceId, setWorkspaceId] = useState("");
  const [title, setTitle] = useState("");
  const [goalText, setGoalText] = useState("");
  const [constraints, setConstraints] = useState("");
  const [domainHint, setDomainHint] = useState("");
  const [submitExecutionJobs, setSubmitExecutionJobs] = useState(true);
  const workspacesQuery = useWorkspaces(user?.id);

  useEffect(() => {
    if (!workspaceId && workspacesQuery.data && workspacesQuery.data.length > 0) {
      setWorkspaceId(workspacesQuery.data[0].id);
    }
  }, [workspaceId, workspacesQuery.data]);

  useEffect(() => {
    if (result && planOutputRef.current) {
      planOutputRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await submitPlanning({
        workspaceId,
        title,
        goalText,
        constraints: constraints
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        domainHint: domainHint || null,
        submitExecutionJobs,
      });
    } catch {
      // Error state is handled by the hook and displayed in the UI.
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Planning Workspace"
        description="Create a goal, finalize a structured plan through backend-api, and follow realtime progress as the workflow runs."
        actions={
          <>
            <Badge
              variant={stage === "error" ? "destructive" : stage === "idle" ? "outline" : isPlanning ? "warning" : "success"}
              className="gap-2"
            >
              <Workflow className="h-3.5 w-3.5" />
              {stage}
            </Badge>
            <Button variant="outline" size="sm" onClick={reset} type="button">
              Reset
            </Button>
          </>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <Card className="glass-panel xl:sticky xl:top-6 xl:self-start">
          <CardHeader>
            <CardTitle>Define the goal</CardTitle>
            <CardDescription>
              backend-api will create the goal record first, then request plan finalization from ai-service.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <WorkspaceSelector userId={user?.id} workspaceId={workspaceId} onChange={setWorkspaceId} />

              <div className="space-y-2">
                <Label htmlFor="title">Goal title</Label>
                <Input
                  id="title"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="Launch a study plan, build a feature, etc."
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="goalText">Goal description</Label>
                <Textarea
                  id="goalText"
                  value={goalText}
                  onChange={(event) => setGoalText(event.target.value)}
                  placeholder="Describe the desired outcome in plain language."
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
                  placeholder="Comma-separated constraints, for example: budget under $500, complete in 2 weeks"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="domainHint">Domain hint</Label>
                <Input
                  id="domainHint"
                  value={domainHint}
                  onChange={(event) => setDomainHint(event.target.value)}
                  placeholder="study, jobs, fitness, projects"
                />
              </div>

              <label className="flex items-center gap-3 rounded-2xl border border-border/70 bg-white/5 px-4 py-3 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  checked={submitExecutionJobs}
                  onChange={(event) => setSubmitExecutionJobs(event.target.checked)}
                  className="h-4 w-4 rounded border-border bg-background"
                />
                Submit execution jobs for approval-ready or auto-execute decisions
              </label>

              {error ? (
                <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {error instanceof Error ? error.message : "Unable to finalize plan"}
                </div>
              ) : null}

              <Button type="submit" className="w-full" disabled={isPlanning}>
                {isPlanning ? "Planning..." : "Start planning"}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <RunConsolePanel stage={stage} isWorking={isPlanning} error={error instanceof Error ? error.message : null} />
          <div ref={planOutputRef} className="scroll-mt-24">
            {result ? (
              <Card className="glass-panel border-primary/30 bg-primary/5">
                <CardHeader>
                  <CardTitle>Plan ready</CardTitle>
                  <CardDescription>
                    The structured plan is now rendered below, including milestones, tasks, critique, and execution decisions.
                  </CardDescription>
                </CardHeader>
              </Card>
            ) : null}
            <PlanOutputPanel result={result} isLoading={isPlanning} />
          </div>
          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Session context</CardTitle>
              <CardDescription>Authenticated user and workspace workflow context.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Signed in user</p>
                <p className="mt-2 font-medium">{user?.email ?? "Unknown user"}</p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Workflow state</p>
                <p className="mt-2 font-medium">{stage}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
