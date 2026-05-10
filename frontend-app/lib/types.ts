export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
}

export interface Workspace {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface GoalCreateRequest {
  workspace_id: string;
  title: string;
  goal_text: string;
  constraints: string[];
  domain_hint?: string | null;
  trigger_planning: boolean;
}

export interface Goal {
  id: string;
  workspace_id: string;
  title: string;
  goal_text: string;
  constraints: string[];
  domain_hint?: string | null;
  status: string;
  interpreted_goal?: Record<string, unknown> | null;
  ai_response?: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface GoalCreateResponse {
  goal: Goal;
  plan?: Plan | null;
  planning_job_id?: string | null;
}

export interface PlanFinalizeRequest {
  goal_id: string;
  submit_execution_jobs: boolean;
}

export interface PlanFinalizeJobCreateResponse {
  job_id: string;
  status: "queued";
}

export interface ExecutionDecision {
  task_id: string;
  action_mode: "suggest" | "auto_execute" | "requires_approval" | "manual";
  tool_category?: string | null;
  tool_name?: string | null;
  domain?: string | null;
  reason: string;
  confidence: number;
}

export interface InterpretedGoal {
  primary_intent: string;
  sub_intents: string[];
  domain?: string | null;
  target_outcomes: string[];
  constraints: string[];
  estimated_horizon?: string | null;
  urgency?: string | null;
  confidence?: number | null;
}

export interface PlanningTask {
  id?: string | null;
  title: string;
  description?: string | null;
  milestone_id?: string | null;
  status?: string | null;
  priority?: string | null;
  estimated_effort?: string | null;
  dependencies?: string[];
  acceptance_criteria?: string[];
}

export interface PlanningMilestone {
  id?: string | null;
  title: string;
  description?: string | null;
  status?: string | null;
  order?: number | null;
  tasks?: PlanningTask[];
}

export interface PlanningCritiqueSummary {
  overall_score?: number | null;
  summary?: string | null;
  strengths?: string[];
  issues?: PlanningCritiqueIssue[];
  recommendation?: string | null;
}

export interface PlanningCritiqueIssue {
  issue_type: string;
  severity: "low" | "medium" | "high" | string;
  description: string;
  recommendation: string;
}

export interface RawPlanningResponse {
  plan?: {
    interpreted_goal?: InterpretedGoal | Record<string, unknown> | null;
    milestones?: PlanningMilestone[];
    tasks?: PlanningTask[];
    assumptions?: string[];
    risks?: string[];
    next_best_action?: string | null;
    critique?: PlanningCritiqueSummary | string | null;
  } | null;
  execution?: {
    decisions?: ExecutionDecision[];
    approval_ready_execution_decisions?: ExecutionDecision[];
  } | null;
  critique?: PlanningCritiqueSummary | string | null;
}

export interface PlanningWorkspaceResult {
  goal: Goal;
  plan: Plan;
  raw_ai_response: RawPlanningResponse;
}

export interface ExecutionJobSummary {
  job_id: string;
  status: string;
  task_id: string;
  action_mode: string;
}

export interface ExecutionJobRead {
  job_id: string;
  user_id: string;
  task: Record<string, unknown>;
  decision: ExecutionDecision;
  status: "queued" | "running" | "completed" | "failed" | "requires_approval";
  result?: Record<string, unknown> | null;
  error?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface IntegrationStatus {
  name: string;
  capability: "retrieve_knowledge" | "generate_content" | "store_data" | "schedule" | "notify";
  tool_name: string;
  status: "available" | "configured" | "local_fallback" | "missing_config" | "unavailable";
  description: string;
  configured: boolean;
  requires_approval: boolean;
  notes: string[];
  details: Record<string, unknown>;
}

export interface Plan {
  id: string;
  goal_id: string;
  status: string;
  request_payload: Record<string, unknown>;
  response_payload?: Record<string, unknown> | null;
  execution_decisions: ExecutionDecision[];
  approval_ready_execution_decisions: ExecutionDecision[];
  execution_jobs: ExecutionJobSummary[];
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PlanFinalizeResponse {
  plan: Plan;
  raw_ai_response: RawPlanningResponse;
}

export interface PlanFinalizeJobRead {
  job_id: string;
  goal_id: string;
  workspace_id: string;
  user_id: string;
  status: "queued" | "running" | "completed" | "failed";
  result?: PlanFinalizeResponse | null;
  error?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface RagIngestResponse {
  status: "ingested";
  document_id: string;
  filename: string;
  source: string;
  user_id?: string | null;
  chunk_count: number;
  chunk_ids: string[];
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  text: string;
  score: number;
  title?: string | null;
  user_id?: string | null;
  domain?: string | null;
  source?: string | null;
  metadata?: Record<string, unknown>;
}

export interface RagQueryRequest {
  query: string;
  user_id?: string | null;
  top_k?: number;
}

export interface RagQueryResponse {
  query: string;
  answer: string;
  sources: RetrievedChunk[];
  user_id?: string | null;
}

export interface WebSocketEvent {
  event_type:
    | "planning_started"
    | "planning_progress"
    | "planning_completed"
    | "execution_job_submitted"
    | "execution_job_running"
    | "execution_job_completed"
    | "execution_job_failed"
    | "rag_ingestion_started"
    | "rag_ingestion_completed";
  entity_type: string;
  entity_id: string;
  message: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface AuthCredentials {
  email: string;
  password: string;
}

export interface RegisterPayload extends AuthCredentials {
  full_name?: string | null;
}

export interface WorkspaceCreateRequest {
  user_id: string;
  name: string;
  description?: string | null;
}
