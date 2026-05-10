export interface PlanningCritiqueIssue {
  issue_type: string;
  severity: "low" | "medium" | "high" | string;
  description: string;
  recommendation: string;
}

export interface PlanningCritiqueSummary {
  overall_score?: number | null;
  summary?: string | null;
  strengths?: string[];
  issues?: PlanningCritiqueIssue[];
  recommendation?: string | null;
}

export function parsePlanningCritiqueIssues(value: unknown): PlanningCritiqueIssue[];
export function parsePlanningCritiqueSummary(value: unknown): PlanningCritiqueSummary | null;
