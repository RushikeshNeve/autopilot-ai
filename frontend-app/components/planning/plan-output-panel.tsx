"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import {
  Brain,
  CheckSquare,
  Copy,
  FileText,
  Layers3,
  ListChecks,
  Sparkles,
  Target,
  TriangleAlert,
} from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { parsePlanningCritiqueSummary } from "@/lib/planning/critique-parser";
import type {
  ExecutionDecision,
  InterpretedGoal,
  PlanningCritiqueIssue,
  PlanningCritiqueSummary,
  PlanningMilestone,
  PlanningTask,
  PlanningWorkspaceResult,
} from "@/lib/types";

interface PlanOutputPanelProps {
  result: PlanningWorkspaceResult | null;
  isLoading: boolean;
}

function RevealSection({ children, delayMs = 0, className = "" }: { children: ReactNode; delayMs?: number; className?: string }) {
  return (
    <div
      className={`reveal-up ${className}`.trim()}
      style={{
        animationDelay: `${delayMs}ms`,
      }}
    >
      {children}
    </div>
  );
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function asText(value: unknown, fallback = "Not provided"): string {
  return typeof value === "string" && value.trim().length > 0 ? value : fallback;
}

function toInterpretedGoal(value: unknown): InterpretedGoal | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  const record = value as Record<string, unknown>;
  return {
    primary_intent: asText(record.primary_intent),
    sub_intents: asStringArray(record.sub_intents),
    domain: typeof record.domain === "string" ? record.domain : null,
    target_outcomes: asStringArray(record.target_outcomes),
    constraints: asStringArray(record.constraints),
    estimated_horizon: typeof record.estimated_horizon === "string" ? record.estimated_horizon : null,
    urgency: typeof record.urgency === "string" ? record.urgency : null,
    confidence: typeof record.confidence === "number" ? record.confidence : null,
  };
}

function getRawInterpretedGoal(result: PlanningWorkspaceResult | null): InterpretedGoal | null {
  return toInterpretedGoal(result?.raw_ai_response.plan?.interpreted_goal);
}

function getRawMilestones(result: PlanningWorkspaceResult | null): PlanningMilestone[] {
  return result?.raw_ai_response.plan?.milestones ?? [];
}

function getRawTasks(result: PlanningWorkspaceResult | null): PlanningTask[] {
  return result?.raw_ai_response.plan?.tasks ?? [];
}

function getExecutionDecisions(result: PlanningWorkspaceResult | null): ExecutionDecision[] {
  return result?.plan.execution_decisions ?? result?.raw_ai_response.execution?.decisions ?? [];
}

function getApprovalDecisions(result: PlanningWorkspaceResult | null): ExecutionDecision[] {
  return result?.plan.approval_ready_execution_decisions ?? result?.raw_ai_response.execution?.approval_ready_execution_decisions ?? [];
}

function getCritique(result: PlanningWorkspaceResult | null): PlanningCritiqueSummary | null {
  return (
    parsePlanningCritiqueSummary(result?.raw_ai_response.critique) ??
    parsePlanningCritiqueSummary(result?.raw_ai_response.plan?.critique) ??
    null
  );
}

function issueTone(severity: PlanningCritiqueIssue["severity"]): "default" | "success" | "warning" | "destructive" | "outline" {
  switch (severity) {
    case "high":
      return "destructive";
    case "medium":
      return "warning";
    case "low":
      return "outline";
    default:
      return "default";
  }
}

function confidenceLabel(confidence?: number | null): string {
  if (confidence === null || confidence === undefined || Number.isNaN(confidence)) {
    return "n/a";
  }
  return `${Math.round(confidence * 100)}%`;
}

function decisionTone(actionMode: ExecutionDecision["action_mode"]): "default" | "success" | "warning" | "destructive" | "outline" {
  switch (actionMode) {
    case "auto_execute":
      return "success";
    case "requires_approval":
      return "warning";
    case "manual":
      return "outline";
    case "suggest":
    default:
      return "default";
  }
}

function buildPlanSnapshot(params: {
  goalTitle: string;
  status: string;
  milestoneCount: number;
  taskCount: number;
  decisionCount: number;
  approvalCount: number;
  critiqueScore: number | null;
}): string {
  return [
    `Goal: ${params.goalTitle}`,
    `Status: ${params.status}`,
    `Milestones: ${params.milestoneCount}`,
    `Tasks: ${params.taskCount}`,
    `Execution decisions: ${params.decisionCount}`,
    `Approval-ready: ${params.approvalCount}`,
    params.critiqueScore !== null && params.critiqueScore !== undefined ? `Critique score: ${params.critiqueScore}` : null,
  ]
    .filter(Boolean)
    .join("\n");
}

function DecisionList({ decisions }: { decisions: ExecutionDecision[] }) {
  if (decisions.length === 0) {
    return <p className="text-sm text-muted-foreground">No execution decisions returned.</p>;
  }

  return (
    <div className="space-y-3">
      {decisions.map((decision) => (
        <div key={`${decision.task_id}-${decision.tool_name ?? decision.tool_category ?? decision.action_mode}`} className="rounded-2xl border border-border/70 bg-white/5 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={decisionTone(decision.action_mode)}>{decision.action_mode}</Badge>
            {decision.tool_category ? <Badge variant="outline">{decision.tool_category}</Badge> : null}
            {decision.tool_name ? <Badge variant="secondary">{decision.tool_name}</Badge> : null}
          </div>
          <div className="mt-3 space-y-2">
            <p className="text-sm font-medium">{decision.reason}</p>
            <p className="text-xs text-muted-foreground">
              Task {decision.task_id} - Domain {decision.domain ?? "n/a"} - Confidence {confidenceLabel(decision.confidence)}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function PlanOutputPanel({ result, isLoading }: PlanOutputPanelProps) {
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const interpretedGoal = getRawInterpretedGoal(result);
  const milestones = getRawMilestones(result);
  const tasks = getRawTasks(result);
  const critique = getCritique(result);
  const executionDecisions = getExecutionDecisions(result);
  const approvalDecisions = getApprovalDecisions(result);
  const executionJobs = result?.plan.execution_jobs ?? [];
  const assumptions = result?.raw_ai_response.plan?.assumptions ?? [];
  const risks = result?.raw_ai_response.plan?.risks ?? [];
  const nextBestAction = result?.raw_ai_response.plan?.next_best_action ?? null;
  const milestoneCount = milestones.length;
  const taskCount = tasks.length;
  const decisionCount = executionDecisions.length;
  const approvalCount = approvalDecisions.length;
  const executionJobCount = executionJobs.length;
  const critiqueScore = critique?.overall_score ?? null;

  async function handleCopySnapshot() {
    if (!result || typeof navigator === "undefined" || !navigator.clipboard) {
      return;
    }

    await navigator.clipboard.writeText(
      buildPlanSnapshot({
        goalTitle: result.goal.title,
        status: result.plan.status,
        milestoneCount,
        taskCount,
        decisionCount,
        approvalCount,
        critiqueScore,
      }),
    );
    setCopyState("copied");
    window.setTimeout(() => setCopyState("idle"), 1600);
  }

  return (
    <Card className="glass-panel">
      <CardHeader>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle>Plan output</CardTitle>
            <CardDescription>
              Rendered from backend-api response shapes so the frontend can stay typed and predictable.
            </CardDescription>
          </div>
          {result ? (
            <Button type="button" variant="outline" size="sm" onClick={handleCopySnapshot}>
              <Copy className="h-4 w-4" />
              {copyState === "copied" ? "Copied snapshot" : "Copy snapshot"}
            </Button>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {!result ? (
          <div className="rounded-3xl border border-dashed border-border/70 bg-white/5 p-8 text-center">
            <Sparkles className="mx-auto h-10 w-10 text-primary" />
            <p className="mt-4 text-base font-medium">No plan yet</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Submit a goal to generate a structured plan, milestones, tasks, and execution decisions.
            </p>
          </div>
        ) : null}

        {result ? (
          <>
            <RevealSection delayMs={0} className="rounded-3xl border border-primary/20 bg-gradient-to-br from-primary/10 via-background to-secondary/10 p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="default">{result.plan.status}</Badge>
                    <Badge variant="outline">Goal {result.plan.goal_id.slice(0, 8)}</Badge>
                    {executionDecisions.some((decision) => decision.action_mode === "auto_execute") ? (
                      <Badge variant="success">Auto execution enabled</Badge>
                    ) : (
                      <Badge variant="warning">Human-gated decisions</Badge>
                    )}
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Goal</p>
                    <p className="mt-2 text-xl font-semibold">{result.goal.title}</p>
                    <p className="mt-2 max-w-3xl text-sm text-muted-foreground">{result.goal.goal_text}</p>
                  </div>
                </div>

                <div className="grid min-w-[18rem] gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <div className="rounded-2xl border border-border/70 bg-white/60 p-4 backdrop-blur">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Milestones</p>
                    <p className="mt-2 text-2xl font-semibold">{milestoneCount}</p>
                  </div>
                  <div className="rounded-2xl border border-border/70 bg-white/60 p-4 backdrop-blur">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Tasks</p>
                    <p className="mt-2 text-2xl font-semibold">{taskCount}</p>
                  </div>
                  <div className="rounded-2xl border border-border/70 bg-white/60 p-4 backdrop-blur">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Decisions</p>
                    <p className="mt-2 text-2xl font-semibold">{decisionCount}</p>
                  </div>
                </div>
              </div>
            </RevealSection>

            <RevealSection delayMs={80} className="rounded-3xl border border-border/70 bg-background/80 p-5">
              <div className="flex items-center gap-3">
                <Brain className="h-5 w-5 text-primary" />
                <h3 className="text-base font-semibold">Interpreted goal</h3>
              </div>
              {interpretedGoal ? (
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Primary intent</p>
                      <p className="mt-1 text-sm">{interpretedGoal.primary_intent}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Domain</p>
                      <p className="mt-1 text-sm">{interpretedGoal.domain ?? "n/a"}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Horizon</p>
                      <p className="mt-1 text-sm">{interpretedGoal.estimated_horizon ?? "n/a"}</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Sub-intents</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {interpretedGoal.sub_intents.length > 0 ? (
                          interpretedGoal.sub_intents.map((item) => (
                            <Badge key={item} variant="outline">
                              {item}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-sm text-muted-foreground">None returned</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Target outcomes</p>
                      <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                        {interpretedGoal.target_outcomes.length > 0 ? (
                          interpretedGoal.target_outcomes.map((item) => <li key={item}>- {item}</li>)
                        ) : (
                          <li>- None returned</li>
                        )}
                      </ul>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Constraints</p>
                      <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                        {interpretedGoal.constraints.length > 0 ? (
                          interpretedGoal.constraints.map((item) => <li key={item}>- {item}</li>)
                        ) : (
                          <li>- None returned</li>
                        )}
                      </ul>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">Confidence {confidenceLabel(interpretedGoal.confidence)}</Badge>
                      {interpretedGoal.urgency ? <Badge variant="warning">{interpretedGoal.urgency}</Badge> : null}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-muted-foreground">No interpreted goal details were returned.</p>
              )}
            </RevealSection>

            <div className="grid gap-4 xl:grid-cols-2">
              <RevealSection delayMs={120} className="rounded-3xl border border-border/70 bg-background/80 p-5">
                <div className="flex items-center gap-3">
                  <Layers3 className="h-5 w-5 text-primary" />
                  <h3 className="text-base font-semibold">Milestones</h3>
                </div>
                <div className="mt-4 space-y-3">
                  {milestones.length > 0 ? (
                    milestones.map((milestone, index) => (
                      <div key={`${milestone.id ?? milestone.title}-${index}`} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium">{milestone.title}</p>
                            <p className="mt-1 text-sm text-muted-foreground">{milestone.description ?? "No description provided."}</p>
                          </div>
                          <Badge variant="outline">{milestone.status ?? `#${milestone.order ?? index + 1}`}</Badge>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No milestones returned.</p>
                  )}
                </div>
              </RevealSection>

              <RevealSection delayMs={160} className="rounded-3xl border border-border/70 bg-background/80 p-5">
                <div className="flex items-center gap-3">
                  <ListChecks className="h-5 w-5 text-primary" />
                  <h3 className="text-base font-semibold">Tasks</h3>
                </div>
                <div className="mt-4 space-y-3">
                  {tasks.length > 0 ? (
                    tasks.map((task, index) => (
                      <div key={`${task.id ?? task.title}-${index}`} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium">{task.title}</p>
                            <p className="mt-1 text-sm text-muted-foreground">{task.description ?? "No description provided."}</p>
                          </div>
                          <div className="flex flex-col items-end gap-2">
                            {task.priority ? <Badge variant="secondary">{task.priority}</Badge> : null}
                            {task.status ? <Badge variant="outline">{task.status}</Badge> : null}
                          </div>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                          {task.estimated_effort ? <span>Effort: {task.estimated_effort}</span> : null}
                          {task.milestone_id ? <span>Milestone: {task.milestone_id}</span> : null}
                        </div>
                        {task.dependencies && task.dependencies.length > 0 ? (
                          <div className="mt-3">
                            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Dependencies</p>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {task.dependencies.map((dependency) => (
                                <Badge key={dependency} variant="outline">
                                  {dependency}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        ) : null}
                        {task.acceptance_criteria && task.acceptance_criteria.length > 0 ? (
                          <div className="mt-3">
                            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Acceptance criteria</p>
                            <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                              {task.acceptance_criteria.map((item) => (
                                <li key={item}>- {item}</li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No tasks returned.</p>
                  )}
                </div>
              </RevealSection>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <RevealSection delayMs={200} className="rounded-3xl border border-border/70 bg-background/80 p-5">
                <div className="flex items-center gap-3">
                  <CheckSquare className="h-5 w-5 text-primary" />
                  <h3 className="text-base font-semibold">Execution decisions</h3>
                </div>
                <div className="mt-4">
                  <DecisionList decisions={executionDecisions} />
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-3">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Auto execute</p>
                    <p className="mt-2 text-lg font-semibold">
                      {executionDecisions.filter((decision) => decision.action_mode === "auto_execute").length}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-3">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Needs approval</p>
                    <p className="mt-2 text-lg font-semibold">{approvalCount}</p>
                  </div>
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-3">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Execution jobs</p>
                    <p className="mt-2 text-lg font-semibold">{executionJobCount}</p>
                  </div>
                </div>
              </RevealSection>

              <RevealSection delayMs={240} className="rounded-3xl border border-border/70 bg-background/80 p-5">
                <div className="flex items-center gap-3">
                  <Target className="h-5 w-5 text-primary" />
                  <h3 className="text-base font-semibold">Approval-ready decisions</h3>
                </div>
                <div className="mt-4">
                  <DecisionList decisions={approvalDecisions} />
                </div>
              </RevealSection>
            </div>

            <RevealSection delayMs={280} className="rounded-3xl border border-border/70 bg-background/80 p-5">
              <div className="flex items-center gap-3">
                <ListChecks className="h-5 w-5 text-primary" />
                <h3 className="text-base font-semibold">Execution jobs</h3>
              </div>
              <div className="mt-4 space-y-3">
                {executionJobs.length > 0 ? (
                  executionJobs.map((job) => (
                    <div key={job.job_id} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="outline">{job.status}</Badge>
                        <Badge variant="secondary">{job.action_mode}</Badge>
                      </div>
                      <p className="mt-3 text-sm font-medium">{job.task_id}</p>
                      <p className="text-xs text-muted-foreground">Job {job.job_id}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No execution jobs created yet.</p>
                )}
              </div>
            </RevealSection>

            <div className="grid gap-4 xl:grid-cols-3">
              <RevealSection delayMs={320} className="rounded-3xl border border-border/70 bg-background/80 p-5">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-primary" />
                  <h3 className="text-base font-semibold">Assumptions</h3>
                </div>
                <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                  {assumptions.length > 0 ? assumptions.map((item) => <li key={item}>- {item}</li>) : <li>- None returned</li>}
                </ul>
              </RevealSection>

              <RevealSection delayMs={360} className="rounded-3xl border border-border/70 bg-background/80 p-5">
                <div className="flex items-center gap-3">
                  <TriangleAlert className="h-5 w-5 text-primary" />
                  <h3 className="text-base font-semibold">Risks</h3>
                </div>
                <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                  {risks.length > 0 ? risks.map((item) => <li key={item}>- {item}</li>) : <li>- None returned</li>}
                </ul>
              </RevealSection>

              <RevealSection delayMs={400} className="rounded-3xl border border-border/70 bg-background/80 p-5">
                <div className="flex items-center gap-3">
                  <Sparkles className="h-5 w-5 text-primary" />
                  <h3 className="text-base font-semibold">Next best action</h3>
                </div>
                <p className="mt-4 text-sm text-muted-foreground">{asText(nextBestAction, "No next-best-action returned.")}</p>
                {critiqueScore !== null ? (
                  <div className="mt-4 rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Critique score</p>
                    <p className="mt-2 text-lg font-semibold">{critiqueScore}</p>
                  </div>
                ) : null}
              </RevealSection>
            </div>

            {critique ? (
              <RevealSection delayMs={440} className="rounded-3xl border border-border/70 bg-background/80 p-5">
                <div className="flex items-center gap-3">
                  <Sparkles className="h-5 w-5 text-primary" />
                  <h3 className="text-base font-semibold">Critique summary</h3>
                  {critique.overall_score !== null && critique.overall_score !== undefined ? (
                    <Badge variant="outline">Score {critique.overall_score}</Badge>
                  ) : null}
                </div>
                <p className="mt-4 text-sm text-muted-foreground">
                  {critique.summary ?? "No critique summary was included in the response."}
                </p>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Strengths</p>
                    <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                      {critique.strengths && critique.strengths.length > 0 ? (
                        critique.strengths.map((item) => <li key={item}>- {item}</li>)
                      ) : (
                        <li>- None returned</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Actionable issues</p>
                    <div className="mt-2 space-y-2">
                      {critique.issues && critique.issues.length > 0 ? (
                        critique.issues.map((issue) => (
                          <div key={`${issue.issue_type}-${issue.description}`} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant={issueTone(issue.severity)}>{issue.severity}</Badge>
                              <Badge variant="outline">{issue.issue_type}</Badge>
                            </div>
                            <p className="mt-3 text-sm font-medium">{issue.description}</p>
                            <p className="mt-2 text-sm text-muted-foreground">{issue.recommendation}</p>
                          </div>
                        ))
                      ) : (
                        <div className="rounded-2xl border border-border/70 bg-white/5 p-4 text-sm text-muted-foreground">
                          No structured issues were returned.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                {critique.recommendation ? (
                  <div className="mt-4 rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Recommendation</p>
                    <p className="mt-2 text-sm text-muted-foreground">{critique.recommendation}</p>
                  </div>
                ) : null}
                {critique.issues && critique.issues.length > 0 ? (
                  <div className="mt-4 rounded-2xl border border-primary/20 bg-primary/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Suggested next actions</p>
                    <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                      {critique.issues.slice(0, 3).map((issue) => (
                        <li key={`${issue.issue_type}-${issue.recommendation}`}>- {issue.recommendation}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </RevealSection>
            ) : null}

            <RevealSection delayMs={480}>
              <details className="rounded-3xl border border-border/70 bg-background/80 p-5">
                <summary className="cursor-pointer text-sm font-medium">Raw planning response</summary>
                <pre className="mt-4 max-h-[24rem] overflow-auto rounded-2xl border border-border/70 bg-black/30 p-4 text-xs leading-6 text-muted-foreground">
                  {JSON.stringify(result.raw_ai_response, null, 2)}
                </pre>
              </details>
            </RevealSection>
          </>
        ) : null}

        {isLoading ? (
          <div className="rounded-3xl border border-border/70 bg-white/5 p-5 text-sm text-muted-foreground">
            Generating plan...
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
