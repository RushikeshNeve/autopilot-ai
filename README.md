# Autopilot AI

Autopilot AI is a multi-service planning and execution platform for turning a goal into a structured plan, approval-gated execution jobs, and realtime progress updates.

It is split into three apps:

- `backend-api` - the orchestration API for auth, goals, plans, approvals, workspaces, and realtime state
- `ai-service` - the AI-heavy service for planning, critique, execution routing, RAG, and external integration adapters
- `frontend-app` - the Next.js UI for creating goals, reviewing plans, approving jobs, and watching progress

## What it does

- Create a goal and generate a structured plan
- Break the plan into milestones, tasks, and execution decisions
- Stream live planning progress over websockets
- Create execution jobs for tasks that can run automatically
- Put approval-gated tasks into a review queue
- Support RAG ingestion and grounded retrieval
- Expose integrations such as Notion, local scheduler fallback, and notification fallback

## Repository Layout

```text
.
|-- ai-service/
|-- backend-api/
|-- frontend-app/
|-- flow_to_test.txt
`-- README.md
```

## Prerequisites

- Python 3.12+
- Node.js 18+
- Docker Desktop

Optional, but useful:

- GitHub CLI if you want to create or manage the GitHub repo from the terminal

## Quick Start

### 1) Start the AI service

From `ai-service/`:

```powershell
docker compose up -d
```

This starts:

- `ai-service` on `http://127.0.0.1:8001`
- `qdrant` on `http://127.0.0.1:6333`

### 2) Start the backend API

From `backend-api/`:

```powershell
.\run-local.ps1
```

This uses a local SQLite database file and starts the API on `http://127.0.0.1:8000`.

### 3) Start the frontend

From `frontend-app/`:

```powershell
.\run-local.ps1
```

This builds the app and starts the UI on `http://127.0.0.1:3001`.

## Manual Startup

If you prefer to run each service manually:

### AI service

Set environment variables in `ai-service/.env`:

```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-5-mini
OPENAI_TIMEOUT=120
OPENAI_MAX_RETRIES=1
```

Optional integration variables:

```env
NOTION_API_KEY=...
NOTION_DB_ID=...
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

Then run:

```powershell
cd ai-service
docker compose up -d
```

### Backend API

The backend reads these common environment variables:

```env
DATABASE_URL=sqlite:///backend-api.db
AI_SERVICE_URL=http://127.0.0.1:8001
AI_FINALIZE_TIMEOUT_SECONDS=900
```

Then run:

```powershell
cd backend-api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

The frontend reads:

```env
NEXT_PUBLIC_BACKEND_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000/ws
```

Then run:

```powershell
cd frontend-app
npm install
npm run dev -- --port 3001
```

## Main User Flow

1. Register or log in
2. Create a goal
3. Wait for planning to complete
4. Review the generated plan
5. Create execution jobs
6. Approve any gated jobs
7. Track execution progress in realtime

## Key UI Areas

- Dashboard
- Goals
- Planning
- Plans
- Executions
- Approvals
- Integrations
- RAG Ingestion

## API Docs

When the backend is running:

- Backend API docs: `http://127.0.0.1:8000/docs`
- Backend redoc: `http://127.0.0.1:8000/redoc`

When the AI service is running:

- AI service docs: `http://127.0.0.1:8001/docs`

## Integrations

The current integration story includes:

- RAG ingestion and retrieval
- Notion storage support
- Local fallback adapters for generation, scheduling, and notifications

Some integrations are visible in the UI as first-class screens, while others are used internally by the execution layer.

## Testing

Frontend checks:

```powershell
cd frontend-app
npm run test:critique
npx tsc --noEmit --pretty false
```

Backend checks are Python syntax and runtime driven; the project was validated during development with local smoke tests and startup checks.

## Notes

- The backend and execution job stores are designed for local persistence during development.
- The planning flow uses websockets for live updates and keeps polling only as a fallback path.
- If you create a goal with planning enabled, the app should navigate to the generated plan automatically.

## License

No license has been added yet.
