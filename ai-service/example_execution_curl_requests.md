# Example Execution API Requests

Base URL:

```bash
http://127.0.0.1:8001
```

## 1) Auto-execute RAG task

```bash
curl.exe -X POST "http://127.0.0.1:8001/ai/execution/jobs" -H "Content-Type: application/json" -d "{\"user_id\":\"user_demo_1\",\"task\":{\"task_id\":\"task_rag_001\",\"milestone_id\":\"ms_001\",\"title\":\"Research Python queue patterns\",\"description\":\"Find grounded information on using queue.Queue for worker pipelines.\",\"task_type\":\"study\",\"priority\":\"high\",\"estimated_minutes\":30,\"dependencies\":[],\"requires_approval\":false,\"suggested_tools\":[]},\"decision\":{\"task_id\":\"task_rag_001\",\"action_mode\":\"auto_execute\",\"tool_category\":\"retrieve_knowledge\",\"tool_name\":\"rag\",\"domain\":\"engineering\",\"reason\":\"Safe to retrieve knowledge automatically\",\"confidence\":0.94}}"
```

## 2) Auto-execute Notion task

```bash
curl.exe -X POST "http://127.0.0.1:8001/ai/execution/jobs" -H "Content-Type: application/json" -d "{\"user_id\":\"user_demo_1\",\"task\":{\"task_id\":\"task_notion_001\",\"milestone_id\":\"ms_001\",\"title\":\"Store meeting notes\",\"description\":\"Save the meeting summary to Notion for later reference.\",\"task_type\":\"execution\",\"priority\":\"high\",\"estimated_minutes\":30,\"dependencies\":[],\"requires_approval\":false,\"suggested_tools\":[]},\"decision\":{\"task_id\":\"task_notion_001\",\"action_mode\":\"auto_execute\",\"tool_category\":\"store_data\",\"tool_name\":\"notion\",\"domain\":\"operations\",\"reason\":\"Safe to store task data automatically\",\"confidence\":0.92}}"
```

## 3) Manual task

```bash
curl.exe -X POST "http://127.0.0.1:8001/ai/execution/jobs" -H "Content-Type: application/json" -d "{\"user_id\":\"user_demo_1\",\"task\":{\"task_id\":\"task_manual_001\",\"milestone_id\":\"ms_001\",\"title\":\"Review project plan\",\"description\":\"User should review and approve the project plan manually.\",\"task_type\":\"review\",\"priority\":\"high\",\"estimated_minutes\":30,\"dependencies\":[],\"requires_approval\":false,\"suggested_tools\":[]},\"decision\":{\"task_id\":\"task_manual_001\",\"action_mode\":\"manual\",\"tool_category\":\"generate_content\",\"tool_name\":null,\"domain\":\"planning\",\"reason\":\"User review is required\",\"confidence\":0.81}}"
```

## 4) Requires approval task

```bash
curl.exe -X POST "http://127.0.0.1:8001/ai/execution/jobs" -H "Content-Type: application/json" -d "{\"user_id\":\"user_demo_1\",\"task\":{\"task_id\":\"task_approval_001\",\"milestone_id\":\"ms_001\",\"title\":\"Send external email\",\"description\":\"This task requires explicit approval before sending.\",\"task_type\":\"execution\",\"priority\":\"high\",\"estimated_minutes\":30,\"dependencies\":[],\"requires_approval\":true,\"suggested_tools\":[]},\"decision\":{\"task_id\":\"task_approval_001\",\"action_mode\":\"requires_approval\",\"tool_category\":\"notify\",\"tool_name\":null,\"domain\":\"communication\",\"reason\":\"Approval is required before outbound communication\",\"confidence\":0.99}}"
```

## Poll job status

```bash
curl "http://127.0.0.1:8001/ai/execution/jobs/{job_id}"
```

## Smoke test script

```bash
python sample_execution_test.py --base-url http://127.0.0.1:8001
```
