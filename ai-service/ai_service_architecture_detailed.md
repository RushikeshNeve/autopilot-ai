# AI Service Architecture — Agentic AI Work OS

## Scope

This document covers **only the AI service** of the Agentic AI Work OS.  
It does **not** cover the frontend app or the backend API service except where they interface with the AI service.

The AI service is responsible for:

- interpreting user goals
- generating milestone-based plans
- decomposing milestones into tasks
- critiquing and revising plans
- routing tasks for execution
- invoking core capabilities such as knowledge retrieval
- resolving integrations such as Notion and RAG
- preparing the system for async workers, memory, and future multi-agent orchestration

---

# 1. Exact Architecture of the AI Service

## 1.1 Core architectural principle

The AI service is designed as an **intelligence and decisioning engine**, not as the full application state owner.

It is organized into the following internal layers:

1. **API Layer**  
   FastAPI routes that expose well-defined endpoints.

2. **Schema Layer**  
   Pydantic models that enforce structured contracts across the system.

3. **Planning Layer**  
   Goal interpretation, milestone planning, task decomposition, and plan finalization.

4. **Evaluation Layer**  
   Critique and revision loop for improving plan quality.

5. **Execution Layer**  
   Classifies tasks into suggest / auto-execute / requires approval / manual.

6. **Capability Layer**  
   Abstract system capabilities such as `retrieve_knowledge`, `generate_content`, `store_data`, `schedule`, and `notify`.

7. **Integration Layer**  
   Concrete adapters and services such as Notion and RAG.

8. **LLM Layer**  
   Prompt builders, model invocation wrapper, and structured-output parsing.

9. **RAG / Knowledge Layer**  
   Retrieval and grounded generation for common system-wide knowledge access.

10. **Persistence / Memory Layer (current and planned)**  
    Intended for PostgreSQL, Qdrant, and future memory/context pipelines.

---

## 1.2 Current high-level flow

The current AI service flow for a planning request is:

1. Receive raw goal input
2. Interpret raw goal into structured goal metadata
3. Generate milestone plan
4. Generate tasks per milestone
5. Finalize initial plan
6. Critique plan quality
7. Revise plan if score is below threshold
8. Route tasks for execution
9. Resolve capability and integration when execution is triggered
10. Return structured plan and execution decisions

---

## 1.3 Current project structure

```text
ai-service/
  app/
    main.py
    api/
      routes/
        health.py
        goals.py
        planning.py
        evaluation.py
        execution.py
    core/
      config.py
      logger.py
    schemas/
      common.py
      goal.py
      task.py
      plan.py
      evaluation.py
      execution.py
      tool.py               # planned / evolving
    services/
      llm/
        client.py
        structured_output.py
        prompts/
          goal_interpreter.py
          milestone_planner.py
          task_planner.py
          critic.py
          plan_reviser.py
          execution_router.py
      planner/
        goal_interpreter.py
        milestone_planner.py
        task_decomposer.py
        plan_finalizer.py
      evaluator/
        plan_critic.py
        plan_reviser.py
      execution/
        router.py
        approval_policy.py
        capability_registry.py
        integration_resolver.py
        executor.py
      tools/                # planned dynamic tooling layer
        generator.py
        registry.py
        validator.py
    integrations/
      notion/
        notion_adapter.py
    rag/
      service.py
      retrieval/
        retriever.py
      generation/
        answer_generator.py
```

---

# 2. Architectural View

## 2.1 Layered architecture diagram

```mermaid
flowchart TB
    A[Client / Backend API] --> B[FastAPI Route Layer]

    B --> C[Schema Validation Layer]
    C --> D[Planning Layer]
    D --> E[Evaluation Layer]
    E --> F[Execution Layer]

    F --> G[Capability Layer]
    G --> H[Integration Resolver]
    H --> I[Notion Adapter]
    H --> J[RAG Service]

    D --> K[LLM Client]
    E --> K
    F --> K

    J --> L[Retriever]
    J --> M[Answer Generator]
    M --> K

    K --> N[OpenAI Model]
```

### Explanation

This is the current end-to-end architecture of the AI service.

- The **route layer** exposes REST endpoints.
- The **schema layer** validates inputs and outputs using Pydantic.
- The **planning layer** generates the first version of the plan.
- The **evaluation layer** critiques and revises that plan.
- The **execution layer** determines whether tasks should be suggested, executed, or approval-gated.
- The **capability layer** abstracts the system’s available actions.
- The **integration resolver** maps abstract capabilities to concrete services.
- The **RAG service** is designed as a universal core capability, not as a study-only tool.
- The **LLM client** is shared across planning, evaluation, and generation.

---

# 3. Component Diagram

## 3.1 AI service component diagram

```mermaid
classDiagram
    class FastAPIApp {
      +register_routes()
      +start()
    }

    class GoalsRoute {
      +interpret_goal()
    }

    class PlanningRoute {
      +generate_milestones()
      +generate_tasks()
      +finalize_plan()
    }

    class EvaluationRoute {
      +critique_plan()
    }

    class ExecutionRoute {
      +route_tasks()
    }

    class GoalInterpreterService {
      +interpret_goal(request)
    }

    class MilestonePlannerService {
      +generate_milestones(user_id, interpreted_goal)
    }

    class TaskDecomposerService {
      +generate_tasks_for_milestone(user_id, interpreted_goal, milestone)
    }

    class PlanFinalizerService {
      +finalize_plan(user_id, interpreted_goal, milestones, tasks)
    }

    class PlanCriticService {
      +critique_plan(user_id, plan)
    }

    class PlanReviserService {
      +revise_plan(plan, critique)
    }

    class ExecutionRouterService {
      +route_tasks(user_id, tasks)
    }

    class IntegrationResolver {
      +resolve(capability)
    }

    class ExecutionEngine {
      +execute(decision, task)
    }

    class NotionAdapter {
      +create_task(title, description)
    }

    class RAGService {
      +query(query, user_id)
    }

    class Retriever {
      +retrieve(query, user_id)
    }

    class AnswerGenerator {
      +generate(query, docs)
    }

    class LLMClient {
      +generate_text(prompt)
    }

    class StructuredOutputParser {
      +parse_structured_output(raw_text, schema)
    }

    FastAPIApp --> GoalsRoute
    FastAPIApp --> PlanningRoute
    FastAPIApp --> EvaluationRoute
    FastAPIApp --> ExecutionRoute

    GoalsRoute --> GoalInterpreterService

    PlanningRoute --> GoalInterpreterService
    PlanningRoute --> MilestonePlannerService
    PlanningRoute --> TaskDecomposerService
    PlanningRoute --> PlanFinalizerService
    PlanningRoute --> PlanCriticService
    PlanningRoute --> PlanReviserService
    PlanningRoute --> ExecutionRouterService

    EvaluationRoute --> PlanCriticService
    ExecutionRoute --> ExecutionRouterService

    GoalInterpreterService --> LLMClient
    GoalInterpreterService --> StructuredOutputParser

    MilestonePlannerService --> LLMClient
    MilestonePlannerService --> StructuredOutputParser

    TaskDecomposerService --> LLMClient
    TaskDecomposerService --> StructuredOutputParser

    PlanCriticService --> LLMClient
    PlanCriticService --> StructuredOutputParser

    PlanReviserService --> LLMClient
    PlanReviserService --> StructuredOutputParser

    ExecutionRouterService --> LLMClient
    ExecutionRouterService --> StructuredOutputParser
    ExecutionRouterService --> IntegrationResolver

    IntegrationResolver --> NotionAdapter
    IntegrationResolver --> RAGService

    ExecutionEngine --> IntegrationResolver

    RAGService --> Retriever
    RAGService --> AnswerGenerator
    AnswerGenerator --> LLMClient
```

### Explanation

This component diagram shows the major internal services and their relationships:

- **Routes** orchestrate but should not contain business logic.
- **Planner services** own interpretation and plan generation.
- **Evaluator services** own plan quality checks and revision.
- **Execution services** own action decisions and integration routing.
- **LLM and structured parsing** are shared infrastructure.
- **RAG and Notion** are concrete integrations currently attached to execution.

---

# 4. Use Case Diagram

## 4.1 AI service use cases

```mermaid
flowchart LR
    U[Backend API / Client]

    U --> UC1[Interpret Goal]
    U --> UC2[Generate Milestones]
    U --> UC3[Generate Tasks]
    U --> UC4[Finalize Plan]
    U --> UC5[Critique Plan]
    U --> UC6[Route Tasks]
    U --> UC7[Execute Knowledge Retrieval]
    U --> UC8[Store Data in Notion]

    UC4 --> UC1
    UC4 --> UC2
    UC4 --> UC3
    UC4 --> UC5
    UC4 --> UC6

    UC7 --> R[RAG Service]
    UC8 --> N[Notion Adapter]
```

### Explanation

The main actor interacting with this service is the **backend API** or an internal client.

Primary AI service use cases are:

- **Interpret Goal**  
  Transform user intent into a structured goal object.

- **Generate Milestones**  
  Split the goal into major phases.

- **Generate Tasks**  
  Decompose each milestone into actionable steps.

- **Finalize Plan**  
  Combine the previous steps and return a usable plan.

- **Critique Plan**  
  Evaluate plan quality and detect flaws.

- **Route Tasks**  
  Decide what the system can do automatically.

- **Execute Knowledge Retrieval**  
  Use the common RAG capability.

- **Store Data in Notion**  
  Persist tasks or outputs using a concrete adapter.

---

# 5. Sequence Diagrams

## 5.1 Goal interpretation sequence

```mermaid
sequenceDiagram
    participant Client
    participant GoalsRoute
    participant GoalInterpreterService
    participant PromptBuilder
    participant LLMClient
    participant Parser

    Client->>GoalsRoute: POST /ai/goals/interpret
    GoalsRoute->>GoalInterpreterService: interpret_goal(request)
    GoalInterpreterService->>PromptBuilder: build_goal_interpreter_prompt(request)
    PromptBuilder-->>GoalInterpreterService: prompt
    GoalInterpreterService->>LLMClient: generate_text(prompt)
    LLMClient-->>GoalInterpreterService: raw_output
    GoalInterpreterService->>Parser: parse_structured_output(raw_output, InterpretedGoal)
    Parser-->>GoalInterpreterService: interpreted_goal
    GoalInterpreterService-->>GoalsRoute: GoalInterpretResponse
    GoalsRoute-->>Client: JSON response
```

### Explanation

This sequence shows the first AI step:

- The route receives input.
- The service builds a dedicated prompt.
- The LLM client generates raw output.
- The parser validates the response into the target schema.

This pattern is reused across most AI modules.

---

## 5.2 Full planning + critique + revision flow

```mermaid
sequenceDiagram
    participant Client
    participant PlanningRoute
    participant GoalInterpreter
    participant MilestonePlanner
    participant TaskDecomposer
    participant PlanFinalizer
    participant PlanCritic
    participant PlanReviser
    participant ExecutionRouter

    Client->>PlanningRoute: POST /ai/planning/finalize
    PlanningRoute->>GoalInterpreter: interpret_goal(goal_request)
    GoalInterpreter-->>PlanningRoute: interpreted_goal

    PlanningRoute->>MilestonePlanner: generate_milestones(user_id, interpreted_goal)
    MilestonePlanner-->>PlanningRoute: milestones

    loop For each milestone
        PlanningRoute->>TaskDecomposer: generate_tasks_for_milestone(...)
        TaskDecomposer-->>PlanningRoute: task list
    end

    PlanningRoute->>PlanFinalizer: finalize_plan(user_id, interpreted_goal, milestones, tasks)
    PlanFinalizer-->>PlanningRoute: initial_plan

    PlanningRoute->>PlanCritic: critique_plan(user_id, initial_plan)
    PlanCritic-->>PlanningRoute: critique

    alt critique score below threshold
        PlanningRoute->>PlanReviser: revise_plan(initial_plan, critique)
        PlanReviser-->>PlanningRoute: revised_plan
    else score acceptable
        PlanningRoute-->>PlanningRoute: keep initial_plan
    end

    PlanningRoute->>ExecutionRouter: route_tasks(user_id, final_plan.tasks)
    ExecutionRouter-->>PlanningRoute: execution decisions

    PlanningRoute-->>Client: finalized plan + execution decisions
```

### Explanation

This is the core orchestration sequence of the AI service:

1. Interpret the goal
2. Generate milestones
3. Generate tasks per milestone
4. Assemble initial plan
5. Critique it
6. Revise it if necessary
7. Route tasks for execution
8. Return plan plus decision metadata

This is the current central intelligence pipeline of the project.

---

## 5.3 Execution + integration resolution sequence

```mermaid
sequenceDiagram
    participant Client
    participant ExecutionRoute
    participant ExecutionRouter
    participant Policy
    participant Resolver
    participant ExecutionEngine
    participant NotionAdapter
    participant RAGService

    Client->>ExecutionRoute: POST /ai/execution/route
    ExecutionRoute->>ExecutionRouter: route_tasks(user_id, tasks)
    ExecutionRouter->>Policy: enforce approval policy
    Policy-->>ExecutionRouter: safe decisions
    ExecutionRouter-->>ExecutionRoute: execution decisions
    ExecutionRoute-->>Client: decisions

    Note over Client,ExecutionEngine: Execution may be triggered immediately or by backend later

    Client->>ExecutionEngine: execute(decision, task)
    ExecutionEngine->>Resolver: resolve(decision.tool_category)

    alt store_data
        Resolver-->>ExecutionEngine: NotionAdapter
        ExecutionEngine->>NotionAdapter: create_task(title, description)
        NotionAdapter-->>ExecutionEngine: notion result
    else retrieve_knowledge
        Resolver-->>ExecutionEngine: RAGService
        ExecutionEngine->>RAGService: query(task.description, user_id)
        RAGService-->>ExecutionEngine: grounded answer + sources
    end

    ExecutionEngine-->>Client: execution result
```

### Explanation

The execution path is intentionally split into two stages:

- **Routing stage**  
  Decide what should happen and whether approval is required.

- **Execution stage**  
  Resolve abstract capabilities to concrete integrations and carry out the action.

This keeps AI decisioning separate from actual side effects.

---

# 6. Activity Diagram

## 6.1 Planning and execution activity flow

```mermaid
flowchart TD
    A[Receive goal request] --> B[Validate payload]
    B --> C[Interpret goal]
    C --> D[Generate milestones]
    D --> E[Generate tasks per milestone]
    E --> F[Finalize initial plan]
    F --> G[Critique plan]

    G --> H{Score >= threshold?}
    H -- Yes --> I[Keep plan]
    H -- No --> J[Revise plan]
    J --> I

    I --> K[Route tasks for execution]
    K --> L{Task executable?}

    L -- No --> M[Return manual / suggested tasks]
    L -- Yes --> N[Resolve capability]
    N --> O{Capability type}
    O -- retrieve_knowledge --> P[Invoke RAG]
    O -- store_data --> Q[Invoke Notion]
    O -- others --> R[Invoke relevant integration]

    P --> S[Return result]
    Q --> S
    R --> S
    M --> S
```

### Explanation

This activity diagram shows the control flow of the AI service from request intake to decisioned execution.  
The most important branching points are:

- **Critique threshold** for deciding whether revision is needed
- **Execution eligibility** for deciding whether a task should be run
- **Capability routing** for selecting the correct integration

---

# 7. State Diagram

## 7.1 Plan lifecycle state machine

```mermaid
stateDiagram-v2
    [*] --> Received
    Received --> Interpreted
    Interpreted --> MilestonesGenerated
    MilestonesGenerated --> TasksGenerated
    TasksGenerated --> DraftPlanCreated
    DraftPlanCreated --> Critiqued
    Critiqued --> Revised: score below threshold
    Critiqued --> Finalized: score acceptable
    Revised --> Finalized
    Finalized --> Routed
    Routed --> AwaitingApproval: some actions require approval
    Routed --> ReadyForExecution: auto-executable actions present
    AwaitingApproval --> ReadyForExecution
    ReadyForExecution --> Executed
    Executed --> [*]
```

### Explanation

This state machine describes the lifecycle of a plan inside the AI service:

- the plan begins as raw input
- becomes interpreted and structured
- is expanded into milestones and tasks
- is critiqued and optionally revised
- is routed for action
- may wait for human approval
- then becomes ready for execution

This state model is also useful later for backend persistence and audit history.

---

# 8. Data Model Diagram

## 8.1 Core schema relationships

```mermaid
classDiagram
    class GoalInterpretRequest {
      +user_id: str
      +goal_text: str
      +constraints: list[str]
      +domain_hint: str
    }

    class InterpretedGoal {
      +primary_intent: str
      +sub_intents: list[str]
      +domain: str
      +target_outcomes: list[str]
      +constraints: list[str]
      +estimated_horizon: str
      +urgency: str
      +confidence: float
      +reasoning_summary: str
    }

    class Milestone {
      +milestone_id: str
      +title: str
      +description: str
      +priority: str
      +estimated_duration_days: int
    }

    class TaskItem {
      +task_id: str
      +milestone_id: str
      +title: str
      +description: str
      +task_type: str
      +priority: str
      +estimated_minutes: int
      +dependencies: list[str]
      +requires_approval: bool
      +suggested_tools: list[str]
    }

    class FinalizedPlan {
      +user_id: str
      +interpreted_goal: InterpretedGoal
      +milestones: list[Milestone]
      +tasks: list[TaskItem]
      +assumptions: list[str]
      +risks: list[str]
      +next_best_action: str
    }

    class CritiqueIssue {
      +issue_type: str
      +severity: str
      +description: str
      +recommendation: str
    }

    class PlanCritique {
      +overall_score: float
      +issues: list[CritiqueIssue]
      +strengths: list[str]
      +summary: str
    }

    class ExecutionDecision {
      +task_id: str
      +action_mode: str
      +tool_category: str
      +tool_name: str
      +domain: str
      +reason: str
      +confidence: float
    }

    GoalInterpretRequest --> InterpretedGoal
    InterpretedGoal --> Milestone
    Milestone --> TaskItem
    InterpretedGoal --> FinalizedPlan
    Milestone --> FinalizedPlan
    TaskItem --> FinalizedPlan
    FinalizedPlan --> PlanCritique
    TaskItem --> ExecutionDecision
```

### Explanation

This diagram represents the main schema flow of the AI service:

- raw goal input becomes an `InterpretedGoal`
- interpreted goal expands into milestones
- milestones expand into tasks
- tasks and milestones combine into `FinalizedPlan`
- `FinalizedPlan` is evaluated through `PlanCritique`
- each task is mapped to an `ExecutionDecision`

This is the backbone of the service contract design.

---

# 9. RAG Architecture Diagram

## 9.1 Common knowledge retrieval architecture

```mermaid
flowchart LR
    A[Task / Query] --> B[Capability: retrieve_knowledge]
    B --> C[RAG Service]
    C --> D[Retriever]
    C --> E[Answer Generator]

    D --> F[Vector DB / Knowledge Store]
    D --> G[Uploaded Docs / Notes / Notion / Future sources]

    E --> H[LLM Client]
    H --> I[OpenAI Model]

    D -- Retrieved chunks --> E
    E --> J[Grounded answer + sources]
```

### Explanation

RAG is positioned as a **common system capability**, not as a study-only integration.

It is meant to support:

- study planning
- concept explanation
- contextual answering
- future memory-augmented planning
- knowledge grounding across all domains

This makes the RAG layer reusable everywhere in the AI service.

---

# 10. Deployment View

## 10.1 AI service deployment context

```mermaid
flowchart TB
    FE[Frontend App] --> BE[Backend API]
    BE --> AI[AI Service]

    AI --> OAI[OpenAI API]
    AI --> NOTION[Notion API]
    AI --> QDRANT[Qdrant / Vector DB - planned/current]
    AI --> PG[PostgreSQL - planned/current]
    AI --> REDIS[Redis / Queue - planned]
```

### Explanation

Although this document focuses on the AI service, deployment-wise it sits between the application backend and its external intelligence/integration dependencies.

- **Backend API** handles authentication and primary app orchestration
- **AI service** handles intelligence and execution decisioning
- **OpenAI** provides generation and critique reasoning
- **Notion** is used for concrete task persistence
- **Qdrant/PostgreSQL/Redis** support retrieval, memory, and async execution

---

# 11. Design Decisions

## 11.1 Why planning is milestone-based

Milestone-first decomposition is more reliable than generating a full task tree in one shot because:

- it reduces LLM drift
- it creates clearer structure
- it supports critique and revision more cleanly
- it improves explainability for users

---

## 11.2 Why critique is a separate phase

The critique layer exists because generation alone is not enough.

Benefits:
- catches vague tasks
- catches missing dependencies
- improves reliability
- makes the system feel more like an actual planner rather than a prompt wrapper

---

## 11.3 Why execution is capability-based

The AI service should reason in terms of **capabilities**, not raw APIs.

Example:
- `retrieve_knowledge`
- `store_data`
- `notify`
- `schedule`

This prevents the LLM from being tightly coupled to Gmail, Notion, LinkedIn, or other specific APIs.

---

## 11.4 Why RAG is core, not domain-specific

RAG is a universal need across domains:

- study
- jobs
- fitness
- projects
- general planning

By making it a core system capability, the architecture becomes cleaner and more reusable.

---

## 11.5 Why AI should not directly call arbitrary APIs

The system separates:
- **decisioning** from
- **execution**

This reduces:
- hallucinated integrations
- unsafe actions
- brittle architecture
- uncontrolled side effects

---

# 12. Current Strengths and Gaps

## 12.1 Current strengths

The current AI service already has strong architectural qualities:

- clean route/service separation
- strict schema-driven outputs
- layered planning pipeline
- critique and revision loop
- execution decisioning
- capability-based integration direction
- RAG as a common system capability

---

## 12.2 Current gaps / next extensions

The next major improvements for the AI service are:

1. **Memory Layer**
   - PostgreSQL for structured memory
   - Qdrant for semantic memory
   - context builder for personalization

2. **Async Execution**
   - queue-based workers
   - task status tracking
   - retries and execution logs

3. **Tool Registry / Dynamic Tool Synthesis**
   - controlled tool generation
   - validation layer
   - reusable registry

4. **Multi-agent orchestration**
   - planner agent
   - executor agent
   - critic agent
   - memory/retrieval agent

5. **Observability**
   - trace IDs
   - prompt logging
   - token usage
   - latency metrics
   - execution audits

---

# 13. Recommended final mental model

The AI service today should be understood as:

> A schema-driven, layered intelligence service that interprets user goals, creates and evaluates plans, routes tasks into abstract capabilities, and uses controlled integrations such as RAG and Notion to support grounded execution.

That is the exact architecture of the project’s AI service as it stands now.
