# A2A Guide 2 · Building Robust Single Agents

Level up the starter agent into a production-ready service. This guide distills patterns from `a2a-samples` (Python, JS, Java, .NET) and highlights how to structure executors, tools, configuration, observability, and testing.

## 1. Architectural Principles

1. **Separation of Concerns** – Keep core business logic in plain Python classes or services; let the `AgentExecutor` handle protocol translation. Example: `a2a-samples/samples/python/agents/adk_expense_reimbursement` wraps a reimbursement handler and leaves serialization to the executor.
2. **Deterministic Pipelines** – Each task should move through predictable stages: validate input → call tools/services → format outputs → emit completion or error events. Emit progress updates between stages so hosts and Inspector show real-time status.
3. **Pure Inputs/Outputs** – Treat `RequestContext` as immutable. If you must store session state, persist it in a backing store (Redis, Firestore) keyed by `task_id` rather than mutating globals.
4. **Compartmentalised Side Effects** – Wrap external API calls (LLM invocations, HTTP requests) in helper classes so you can swap them for mocks in tests and retries in production.

## 2. Executor Design Patterns

### Async Executor Skeleton
```python
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import (
    new_agent_text_message,
    new_agent_error_message,
    new_agent_progress_message,
    new_json_artifact,
)

class ExpenseAgentExecutor(AgentExecutor):
    def __init__(self, expense_service):
        self._service = expense_service

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        raw = context.get_user_input() or ""
        await event_queue.enqueue_event(new_agent_progress_message("Validating request", 10))
        try:
            request = self._service.parse(raw)
            await event_queue.enqueue_event(new_agent_progress_message("Submitting expense", 40))
            receipt = await self._service.submit(request)
            await event_queue.enqueue_event(new_agent_progress_message("Formatting response", 70))
            artifact = new_json_artifact({"status": "submitted", "id": receipt.id})
            await event_queue.enqueue_event(new_agent_text_message(receipt.summary))
            await event_queue.enqueue_event(artifact)
        except Exception as exc:
            await event_queue.enqueue_event(new_agent_error_message(self._service.humanize_error(exc)))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        self._service.abort(context.get_task_id())
        await event_queue.enqueue_event(new_agent_text_message("Cancellation acknowledged."))
```

**What to note:**
- Multiple progress checkpoints mirror Inspector output and UIs like `demo/ui` task history.
- Errors are normalized via a helper (`humanize_error`) before they leave the service.
- Cancellation triggers a project-specific abort method so downstream APIs roll back work.

### Tool & Skill Definitions

Map tool schemas tightly to your executor. `a2a-samples/samples/python/agents/analytics` demonstrates this by mirroring Pandas operations as tools.

```python
from a2a.types import Tool, ToolParameter, AgentSkill, AgentCapabilities

expense_tool = Tool(
    id="submit_expense",
    name="Submit Expense",
    description="Files an expense with amount, currency, and receipt URL.",
    parameters=[
        ToolParameter(name="amount", type="number", required=True, description="Amount in original currency"),
        ToolParameter(name="currency", type="string", required=True, description="ISO 4217 code"),
        ToolParameter(name="receipt_url", type="string", required=False)
    ],
)

expense_skill = AgentSkill(
    id="expense_management",
    name="Expense Management",
    description="Submits reimbursements and answers policy questions.",
    tags=["finance", "internal-tools"],
    tools=[expense_tool],
)

capabilities = AgentCapabilities(streaming=True, attachments=True)
```

Ensure every tool parameter uses supported types (`string`, `number`, `integer`, `boolean`, `object`, `array`). Invalid schema types will fail Inspector validation.

## 3. Configuration & Secrets

- Keep defaults in `config/congfig.py` and expose overrides via environment variables (`A2A_MODEL_NAME`, `A2A_TEMPERATURE`, etc.).
- Store secret material in `.env` and in deployment-level secret managers. Mirroring `a2a-samples`, denote required auth schemes inside the `AgentCard.security` block so hosts know how to authenticate.
- For swappable providers, read provider identifiers from configuration and branch inside the executor, similar to `samples/python/agents/analytics/model_provider.py`.

## 4. LLM & Tool Integrations

| Framework | Integration Tip | Sample |
| --- | --- | --- |
| LangChain | Use callbacks to stream intermediate steps; convert tool calls to `EventQueue` progress events. | `samples/python/agents/helloworld`, `agents/analytics` |
| LangGraph | Call `app.astream_events()` and relay yielded events. Maintain graph state per `task_id`. | `samples/python/agents/langgraph` |
| CrewAI | Crew runs can be lengthy; emit periodic progress updates and include final plan artifacts. | `samples/python/agents/crewai` |
| LlamaIndex | Convert uploaded files to `Document` objects and persist the index between tasks. | `samples/python/agents/llama_index_file_chat` |
| MCP | Use Guide 5 to wrap MCP tools; the executor becomes a proxy mapping JSON schemas. | `samples/python/agents/a2a_mcp` |
| External APIs | Encapsulate clients (OpenWeather, Google APIs, internal services) in provider modules. Rate-limit and retry with jitter. | `samples/python/agents/weather_*` |

## 5. Observability & Telemetry

- Emit structured logs including `task_id`, `skill`, `latency_ms`, and decision metadata. The traceability extension (`samples/python/extensions/traceability`) shows how to hook into request/response middleware.
- Export metrics via OpenTelemetry or language-specific tools. Examples: Python agent with OTLP exporter, Go host with Prometheus metrics (`samples/go/server`).
- Surface debugging context via the Inspector’s debug console; capture the raw JSON payload and attach it to review documentation.

## 6. Testing Strategy

1. **Unit Tests** – Mock `EventQueue` and assert emitted events. Example skeleton:
   ```python
   import pytest
   from unittest.mock import AsyncMock

   @pytest.mark.asyncio
   async def test_execute_happy_path():
       queue = AsyncMock()
       context = FakeContext(user_input="Submit $20 for lunch")
       executor = ExpenseAgentExecutor(MockService())
       await executor.execute(context, queue)
       queue.enqueue_event.assert_any_call(...)  # assert messages
   ```
2. **Contract Tests** – Use `starlette.testclient.TestClient` or `httpx.AsyncClient` to hit `/tasks` endpoints. Confirm task state transitions and payload formats.
3. **Integration Tests** – Automate Inspector via its backend WebSocket API to ensure AgentCard validation passes on CI builds.
4. **Tool Tests** – Validate schema alignment by feeding tool payloads from orchestrators (e.g., `samples/python/hosts/content_creation`) and verifying they execute end-to-end.

## 7. Resilience & Error Handling

- Implement retries with exponential backoff for external APIs. Keep track of idempotency keys per `task_id` to avoid duplicate submissions.
- Provide human-readable error messages and categorize them using `TaskErrorCode` if you emit structured errors.
- Enforce timeouts per task stage. The Inspector will surface long-running tasks; hosts may cancel after a threshold, so ensure `cancel()` cleans up resources.

## 8. Deployment Readiness Checklist

- [ ] AgentCard fields accurate (skills, version, security schemes, extensions).
- [ ] Tests covering success, validation, and failure paths.
- [ ] Logging strategy emits task, user, and agent identifiers (sanitized as needed).
- [ ] Resource usage measured locally (CPU/memory) using representative workloads; autoscaling thresholds documented.
- [ ] Rollback plan documented (previous container images or VM snapshots, prior AgentCard versions).
- [ ] Inspector trace captured and archived with release notes.

With these practices, a single agent can stand on its own in production: predictable behavior, clear contracts, observability hooks, and rigorous testing inspired by battle-tested samples.
