# Guide 2 · Code Samples

## 1. Expense Domain Models
```python
from __future__ import annotations
from datetime import date
from pydantic import BaseModel, Field, condecimal

class ExpenseLineItem(BaseModel):
    description: str
    amount_minor: int = Field(ge=0)
    category: str

class ExpenseRequest(BaseModel):
    employee_id: str
    currency: str = Field(pattern="^[A-Z]{3}$")
    submitted_date: date
    line_items: list[ExpenseLineItem]
    memo: str | None = None

class ExpenseReceipt(BaseModel):
    request_id: str
    status: str
    total_minor: int
    currency: str
    summary: str
```

## 2. Expense Service Implementations
```python
import asyncio
import httpx

class ExpenseService:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(base_url=self._base_url)

    async def submit(self, request: ExpenseRequest) -> ExpenseReceipt:
        payload = request.model_dump()
        resp = await self._client.post("/expenses", json=payload, timeout=20)
        resp.raise_for_status()
        return ExpenseReceipt(**resp.json())

    async def fetch_policy(self, category: str) -> dict[str, str]:
        resp = await self._client.get(f"/policies/{category}")
        resp.raise_for_status()
        return resp.json()

    async def cancel_submission(self, request_id: str) -> None:
        await self._client.post(f"/expenses/{request_id}/cancel")

    async def close(self) -> None:
        await self._client.aclose()
```

## 3. Robust Executor with Streams
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
    def __init__(self, service: ExpenseService) -> None:
        self._service = service

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        raw = context.get_user_input() or "{}"
        await event_queue.enqueue_event(new_agent_progress_message("Validating request", 5))
        try:
            request = ExpenseRequest.model_validate_json(raw)
        except Exception as exc:  # noqa: BLE001
            await event_queue.enqueue_event(new_agent_error_message(f"Validation error: {exc}"))
            return

        await event_queue.enqueue_event(new_agent_progress_message("Submitting expense", 30))
        try:
            receipt = await self._service.submit(request)
        except Exception as exc:  # noqa: BLE001
            await event_queue.enqueue_event(new_agent_error_message(f"Submission failed: {exc}"))
            return

        await event_queue.enqueue_event(new_agent_progress_message("Fetching policy", 70))
        policy = await self._service.fetch_policy(request.line_items[0].category)
        await event_queue.enqueue_event(new_json_artifact(policy))
        await event_queue.enqueue_event(new_agent_text_message(receipt.summary))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        metadata = context.get_metadata() or {}
        request_id = metadata.get("request_id")
        if request_id:
            await self._service.cancel_submission(request_id)
        await event_queue.enqueue_event(new_agent_text_message("Cancellation acknowledged."))
```

## 4. Tool & Skill Definitions
```python
from a2a.types import AgentSkill, AgentCapabilities, Tool, ToolParameter

submit_tool = Tool(
    id="submit_expense",
    name="Submit Expense",
    description="Creates an expense record with line items",
    parameters=[
        ToolParameter(name="employee_id", type="string", required=True),
        ToolParameter(name="currency", type="string", required=True),
        ToolParameter(name="line_items", type="array", required=True),
        ToolParameter(name="memo", type="string", required=False),
    ],
)

policy_tool = Tool(
    id="policy_lookup",
    name="Policy Lookup",
    description="Returns relevant policy text for a category",
    parameters=[
        ToolParameter(name="category", type="string", required=True)
    ],
)

expense_skill = AgentSkill(
    id="expense-management",
    name="Expense Management",
    description="Handles reimbursements and policy guidance",
    tags=["finance", "internal"],
    tools=[submit_tool, policy_tool],
)

capabilities = AgentCapabilities(streaming=True, attachments=True, extensions=["timestamp"])
```

## 5. Configuration Patterns
```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {
        "env_prefix": "A2A_",
        "case_sensitive": False,
    }
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 2048
    expense_service_url: str = "https://expense.internal"
    expense_api_key: str

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## 6. Dependency Injection Container
```python
class Container:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.http_client = httpx.AsyncClient(
            base_url=self.settings.expense_service_url,
            headers={"X-API-Key": self.settings.expense_api_key},
        )
        self.expense_service = ExpenseService(self.settings.expense_service_url, self.http_client)
        self.executor = ExpenseAgentExecutor(self.expense_service)

    async def shutdown(self) -> None:
        await self.expense_service.close()
```

## 7. AgentCard Assembly
```python
from a2a.types import AgentCard

card = AgentCard(
    name="Expense Agent",
    description="Automates reimbursements with policy validation",
    version="2.0.0",
    url="http://expense-agent.internal",
    capabilities=capabilities,
    skills=[expense_skill],
    extensions=[{"id": "timestamp", "version": "1.0.0"}],
)
```

## 8. Testing Harness
```python
import pytest
from unittest.mock import AsyncMock
from a2a.utils import new_agent_text_message

@pytest.mark.asyncio
async def test_executor_success():
    service = AsyncMock()
    service.submit.return_value = ExpenseReceipt(request_id="abc", status="approved", total_minor=1234, currency="USD", summary="Approved")
    service.fetch_policy.return_value = {"category": "travel", "limit": 5000}

    executor = ExpenseAgentExecutor(service)
    context = AsyncMock()
    context.get_user_input.return_value = ExpenseRequest(
        employee_id="E123",
        currency="USD",
        submitted_date=date.today(),
        line_items=[ExpenseLineItem(description="Taxi", amount_minor=2500, category="travel")],
    ).model_dump_json()
    context.get_metadata.return_value = {}
    queue = AsyncMock()

    await executor.execute(context, queue)
    queue.enqueue_event.assert_any_call(new_agent_text_message("Approved"))
```

## 9. Error Path Tests
```python
@pytest.mark.asyncio
async def test_executor_validation_error():
    service = AsyncMock()
    executor = ExpenseAgentExecutor(service)
    context = AsyncMock()
    context.get_user_input.return_value = "bad json"
    queue = AsyncMock()

    await executor.execute(context, queue)
    error_event = queue.enqueue_event.call_args_list[-1][0][0]
    assert "Validation error" in error_event["message"]["text"]
```

## 10. Inspector Trace Assertions
```python
async def assert_policy_artifact(events):
    json_events = [event for event in events if event["type"] == "artifact" and event["artifact"]["kind"] == "json"]
    assert json_events, "Expected policy artifact"
    assert json_events[0]["artifact"]["data"]["category"] == "travel"
```

## 11. Contract Tests with TestClient
```python
from starlette.testclient import TestClient

def test_full_stack(container: Container):
    app = create_app(container.executor, card)
    with TestClient(app) as client:
        payload = {
            "input": {
                "text": ExpenseRequest(
                    employee_id="E999",
                    currency="EUR",
                    submitted_date=str(date.today()),
                    line_items=[{"description": "Hotel", "amount_minor": 12300, "category": "lodging"}],
                ).model_dump_json()
            }
        }
        response = client.post("/tasks", json=payload)
        assert response.status_code == 202
```

## 12. EventQueue Recorder Utility
```python
class RecordingQueue(EventQueue):
    def __init__(self) -> None:
        self.events: list[dict[str, str]] = []

    async def enqueue_event(self, event):
        self.events.append(event)
```

## 13. Retry Middleware
```python
class RetryExpenseService(ExpenseService):
    async def submit(self, request: ExpenseRequest) -> ExpenseReceipt:
        for attempt in range(3):
            try:
                return await super().submit(request)
            except httpx.RequestError as exc:  # noqa: PERF203
                if attempt == 2:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
```

## 14. Streaming Decorator
```python
def stream_events(func):
    async def wrapper(executor, context, queue):
        await queue.enqueue_event(new_agent_progress_message("Started", 0))
        result = await func(executor, context, queue)
        await queue.enqueue_event(new_agent_progress_message("Finished", 100))
        return result
    return wrapper

ExpenseAgentExecutor.execute = stream_events(ExpenseAgentExecutor.execute)
```

## 15. Tool Invocation Example
```python
from a2a.client.client_factory import ClientFactory
from a2a.client.task import SendMessageRequest

async def call_submit_tool():
    client = await ClientFactory().create("http://expense-agent.internal")
    request = SendMessageRequest(
        input={
            "tool": {
                "id": "submit_expense",
                "input": {
                    "employee_id": "E321",
                    "currency": "USD",
                    "line_items": [{"description": "Lunch", "amount_minor": 1500, "category": "meals"}],
                },
            }
        }
    )
    async for event in client.send_message(request):
        print(event)
```

## 16. Policy Lookup Edge Case
```python
@pytest.mark.asyncio
async def test_policy_lookup_failure():
    service = AsyncMock()
    service.submit.return_value = ExpenseReceipt(request_id="abc", status="approved", total_minor=1, currency="USD", summary="Approved")
    service.fetch_policy.side_effect = httpx.HTTPStatusError("Not found", request=None, response=AsyncMock(status_code=404))
    executor = ExpenseAgentExecutor(service)
    context = AsyncMock()
    context.get_user_input.return_value = ExpenseRequest(
        employee_id="E123",
        currency="USD",
        submitted_date=date.today(),
        line_items=[ExpenseLineItem(description="Item", amount_minor=1, category="rare")],
    ).model_dump_json()
    queue = AsyncMock()
    await executor.execute(context, queue)
    assert any("Submission failed" not in call.args[0]["message"]["text"] for call in queue.enqueue_event.call_args_list)
```

## 17. Command-Line Runner
```python
import argparse
import asyncio

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--agent-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    client = await ClientFactory().create(args.agent_url)
    async for event in client.send_message({"input": {"text": args.payload}}):
        print(event)

if __name__ == "__main__":
    asyncio.run(main())
```

## 18. Scenario Data Generator
```python
import random

CATEGORIES = ["travel", "lodging", "meals", "supplies"]

def random_expense_request() -> ExpenseRequest:
    return ExpenseRequest(
        employee_id=f"E{random.randint(100, 999)}",
        currency=random.choice(["USD", "EUR", "JPY"]),
        submitted_date=date.today(),
        line_items=[
            ExpenseLineItem(
                description="Generated",
                amount_minor=random.randint(100, 10000),
                category=random.choice(CATEGORIES),
            )
            for _ in range(random.randint(1, 3))
        ],
        memo="Generated test case",
    )
```

## 19. Golden Transcript Fixture
```python
GOLDEN = [
    {"role": "user", "text": "Submit $12 lunch in USD"},
    {"role": "agent", "text": "Provide employee ID."},
    {"role": "user", "text": "Employee E123"},
]
```

## 20. Artifact Normalizer
```python
from a2a.utils import new_file_artifact

async def normalize_receipt(base64_pdf: str, queue: EventQueue) -> None:
    artifact = new_file_artifact(
        filename="receipt.pdf",
        mime_type="application/pdf",
        data=base64_pdf,
    )
    await queue.enqueue_event(artifact)
```

## 21. Audit Logging Hook
```python
import json

async def audit_event(event: dict[str, str]) -> None:
    with open("audit.log", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
```

## 22. Structured Error Factory
```python
def policy_error(category: str, reason: str) -> dict[str, str]:
    return new_agent_error_message(f"Policy failure for {category}: {reason}")
```

## 23. LangChain Tool Integration
```python
from langchain.tools import StructuredTool

submit_tool_lc = StructuredTool.from_function(
    name="submit_expense",
    description="Submit expense request",
    func=lambda **kwargs: kwargs,
)
```

## 24. Metrics Collector
```python
from collections import defaultdict

METRICS = defaultdict(int)

def record_metric(name: str, value: int = 1) -> None:
    METRICS[name] += value
```

## 25. Async Timeout Wrapper
```python
from asyncio import TimeoutError

async def with_timeout(coro, seconds: float):
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except TimeoutError:
        raise AgentExecutionError(code="timeout", message="Operation timed out")
```

## 26. gRPC Proxy Stub
```python
import grpc

class ExpenseGrpcProxy:
    def __init__(self, stub):
        self._stub = stub

    async def submit(self, request: ExpenseRequest) -> ExpenseReceipt:
        grpc_request = ExpenseProtoRequest(**request.model_dump())
        response = await self._stub.SubmitExpense(grpc_request)
        return ExpenseReceipt(**response_to_dict(response))
```

## 27. Multi-Tenant Context
```python
class MultiTenantContext(RequestContext):
    def __init__(self, tenant_id: str, payload: str):
        self._tenant = tenant_id
        self._payload = payload

    def get_user_input(self) -> str:
        return self._payload

    def get_metadata(self) -> dict[str, str]:
        return {"tenant_id": self._tenant}
```

## 28. Tenant Routing
```python
def resolve_service(tenant_id: str) -> ExpenseService:
    if tenant_id == "enterprise":
        return enterprise_service
    return default_service
```

## 29. Executor Factory
```python
def build_executor(context: MultiTenantContext) -> ExpenseAgentExecutor:
    service = resolve_service(context.get_metadata()["tenant_id"])
    return ExpenseAgentExecutor(service)
```

## 30. Load Testing Script
```python
async def pressure_test(url: str, iterations: int = 50) -> None:
    client = await ClientFactory().create(url)
    for i in range(iterations):
        request = SendMessageRequest(input={"text": random_expense_request().model_dump_json()})
        events = []
        async for event in client.send_message(request):
            events.append(event)
        assert any(evt["type"] == "message" for evt in events)
```
