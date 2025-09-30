# Guide 3 · Python Code Samples

```python
"""Multi-agent orchestration utilities for Guide 3.
This module illustrates host orchestration, registry management, routing,
telemetry, and testing patterns using only Python code.
"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
import os
import pathlib
import random
import string
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Iterable, Protocol

LOG = logging.getLogger("guide3")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Registry models and loading
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class AgentConfig:
    agent_id: str
    url: str
    tags: set[str]
    health_url: str | None
    security_headers: dict[str, str] = field(default_factory=dict)

    def matches(self, tag: str) -> bool:
        return tag in self.tags


class AgentRegistry:
    """Registry managing remote agent metadata."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentConfig] = {}

    def register(self, config: AgentConfig) -> None:
        LOG.debug("Registering agent %s", config.agent_id)
        self._agents[config.agent_id] = config

    def list(self) -> list[AgentConfig]:
        return list(self._agents.values())

    def by_tag(self, tag: str) -> list[AgentConfig]:
        return [cfg for cfg in self._agents.values() if cfg.matches(tag)]

    def get(self, agent_id: str) -> AgentConfig:
        return self._agents[agent_id]


# ---------------------------------------------------------------------------
# Client factory interfaces and stubs
# ---------------------------------------------------------------------------

class Event(Protocol):
    type: str
    payload: dict[str, Any]


@dataclass
class TaskEvent:
    type: str
    payload: dict[str, Any]


class StreamingClient(Protocol):
    async def send_message(self, request: dict[str, Any]) -> AsyncIterator[TaskEvent]:
        ...

    async def cancel_task(self, task_id: str) -> None:
        ...


@dataclass
class FakeClient:
    agent_id: str

    async def send_message(self, request: dict[str, Any]) -> AsyncIterator[TaskEvent]:
        LOG.info("%s handling request %s", self.agent_id, request)
        yield TaskEvent("working", {"progress": 10, "agent": self.agent_id})
        await asyncio.sleep(0.05)
        yield TaskEvent("message", {"text": f"{self.agent_id} received: {request['input']['text']}"})
        yield TaskEvent("completed", {"status": "done", "agent": self.agent_id})

    async def cancel_task(self, task_id: str) -> None:
        LOG.info("%s cancelling %s", self.agent_id, task_id)


class ClientFactory:
    def __init__(self) -> None:
        self._cache: dict[str, FakeClient] = {}

    async def create(self, agent: AgentConfig) -> FakeClient:
        if agent.agent_id not in self._cache:
            self._cache[agent.agent_id] = FakeClient(agent.agent_id)
        return self._cache[agent.agent_id]


# ---------------------------------------------------------------------------
# Intent classification and routing
# ---------------------------------------------------------------------------

@dataclass
class Intent:
    tag: str
    confidence: float
    slots: dict[str, Any] = field(default_factory=dict)


def classify_intent(text: str) -> Intent:
    lowered = text.lower()
    if "expense" in lowered or "receipt" in lowered:
        return Intent("finance", 0.92)
    if "weather" in lowered or "forecast" in lowered:
        return Intent("weather", 0.88)
    if "plan" in lowered and "trip" in lowered:
        return Intent("travel", 0.86, {"type": "trip"})
    return Intent("general", 0.5)


# ---------------------------------------------------------------------------
# Orchestrator executor
# ---------------------------------------------------------------------------

@dataclass
class RouteResult:
    agent_id: str
    events: list[TaskEvent]


class MultiAgentOrchestrator:
    def __init__(self, registry: AgentRegistry, factory: ClientFactory) -> None:
        self.registry = registry
        self.factory = factory
        self.activity_log: list[RouteResult] = []
        self._active: dict[str, list[tuple[str, str]]] = defaultdict(list)

    async def execute(self, user_text: str, task_id: str) -> list[TaskEvent]:
        intent = classify_intent(user_text)
        LOG.info("Routing intent %s (confidence %.2f)", intent.tag, intent.confidence)
        candidates = self.registry.by_tag(intent.tag)
        if not candidates:
            LOG.warning("No agents for tag %s", intent.tag)
            return [TaskEvent("error", {"message": "No agents available"})]
        selected = candidates[0]
        client = await self.factory.create(selected)
        request = {"input": {"text": user_text}, "metadata": {"trace_id": task_id}}
        events: list[TaskEvent] = []
        async for event in client.send_message(request):
            events.append(event)
        self.activity_log.append(RouteResult(selected.agent_id, events))
        self._active[task_id].append((selected.agent_id, f"remote-{task_id}"))
        return events

    async def fan_out(self, user_text: str, task_id: str) -> list[RouteResult]:
        intents = user_text.split(" and ")
        results: list[RouteResult] = []
        for idx, piece in enumerate(intents):
            intent = classify_intent(piece)
            for agent in self.registry.by_tag(intent.tag):
                client = await self.factory.create(agent)
                events = []
                async for event in client.send_message({"input": {"text": piece}, "metadata": {"trace_id": f"{task_id}-{idx}"}}):
                    events.append(event)
                results.append(RouteResult(agent.agent_id, events))
        return results

    async def cancel(self, task_id: str) -> None:
        for agent_id, remote in self._active.get(task_id, []):
            client = await self.factory.create(self.registry.get(agent_id))
            await client.cancel_task(remote)
        self._active.pop(task_id, None)


# ---------------------------------------------------------------------------
# Telemetry and metrics helpers
# ---------------------------------------------------------------------------

@dataclass
class Metric:
    name: str
    values: list[float] = field(default_factory=list)

    def observe(self, value: float) -> None:
        self.values.append(value)

    def average(self) -> float:
        return sum(self.values) / len(self.values) if self.values else 0.0


class MetricsCollector:
    def __init__(self) -> None:
        self.metrics: dict[str, Metric] = {}

    def observe(self, name: str, value: float) -> None:
        metric = self.metrics.setdefault(name, Metric(name))
        metric.observe(value)

    def report(self) -> dict[str, float]:
        return {name: metric.average() for name, metric in self.metrics.items()}


# ---------------------------------------------------------------------------
# Health checking
# ---------------------------------------------------------------------------

async def check_health(agent: AgentConfig) -> bool:
    await asyncio.sleep(0.01)
    if agent.health_url and "down" in agent.health_url:
        return False
    return True


async def ensure_agents_healthy(registry: AgentRegistry) -> dict[str, bool]:
    results = {}
    for agent in registry.list():
        results[agent.agent_id] = await check_health(agent)
    return results


# ---------------------------------------------------------------------------
# Persistence models for task mappings
# ---------------------------------------------------------------------------

@dataclass
class TaskRecord:
    task_id: str
    user_input: str
    routed_agents: list[str]
    created_at: float
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskStore:
    def __init__(self) -> None:
        self.records: dict[str, TaskRecord] = {}

    def add(self, task_id: str, user_input: str, agents: list[str]) -> None:
        self.records[task_id] = TaskRecord(task_id, user_input, agents, time.time())

    def list_recent(self, limit: int = 5) -> list[TaskRecord]:
        return sorted(self.records.values(), key=lambda rec: rec.created_at, reverse=True)[:limit]


# ---------------------------------------------------------------------------
# CLI simulation for orchestrator
# ---------------------------------------------------------------------------

async def interactive_cli(orchestrator: MultiAgentOrchestrator) -> None:
    print("Type messages to route, or 'quit'.")
    while True:
        text = input("you> ")
        if text.strip() in {"quit", "exit"}:
            break
        task_id = f"task-{len(orchestrator.activity_log) + 1}"
        events = await orchestrator.execute(text, task_id)
        for event in events:
            print(f"{event.type}: {event.payload}")


# ---------------------------------------------------------------------------
# Helper to create registry from environment variables (python only)
# ---------------------------------------------------------------------------

def registry_from_env() -> AgentRegistry:
    registry = AgentRegistry()
    agents_raw = os.environ.get("A2A_AGENT_REGISTRY", "")
    if not agents_raw:
        registry.register(
            AgentConfig(
                agent_id="expense",
                url="http://localhost:10002",
                tags={"finance", "reimbursement"},
                health_url="http://localhost:10002/healthz",
                security_headers={"X-API-Key": "placeholder"},
            )
        )
        registry.register(
            AgentConfig(
                agent_id="weather",
                url="http://localhost:10003",
                tags={"weather", "travel"},
                health_url="http://localhost:10003/healthz",
            )
        )
        return registry
    for item in agents_raw.split(";"):
        agent_id, url, tags = item.split(",", maxsplit=2)
        registry.register(
            AgentConfig(
                agent_id=agent_id,
                url=url,
                tags=set(tags.split("|")),
                health_url=f"{url}/healthz",
            )
        )
    return registry


# ---------------------------------------------------------------------------
# Testing utilities
# ---------------------------------------------------------------------------

async def _test_execute_single() -> None:
    registry = registry_from_env()
    orchestrator = MultiAgentOrchestrator(registry, ClientFactory())
    events = await orchestrator.execute("Need an expense report", "task-1")
    assert any(event.type == "completed" for event in events)


async def _test_fan_out() -> None:
    registry = registry_from_env()
    orchestrator = MultiAgentOrchestrator(registry, ClientFactory())
    results = await orchestrator.fan_out("Check weather and submit expense", "task-2")
    assert len(results) >= 2


async def _test_cancel() -> None:
    registry = registry_from_env()
    orchestrator = MultiAgentOrchestrator(registry, ClientFactory())
    await orchestrator.execute("Submit expense", "task-3")
    await orchestrator.cancel("task-3")


# ---------------------------------------------------------------------------
# Timeline reconstruction
# ---------------------------------------------------------------------------

@dataclass
class TimelineEntry:
    timestamp: float
    agent_id: str
    message: str


def build_timeline(results: Iterable[RouteResult]) -> list[TimelineEntry]:
    timeline: list[TimelineEntry] = []
    ts = time.time()
    for result in results:
        for event in result.events:
            if event.type == "message":
                timeline.append(TimelineEntry(ts, result.agent_id, event.payload["text"]))
                ts += 0.01
    return timeline


# ---------------------------------------------------------------------------
# Utility for random transcript generation
# ---------------------------------------------------------------------------

def random_transcript(agent_id: str, count: int = 3) -> list[TaskEvent]:
    events: list[TaskEvent] = []
    for index in range(count):
        text = f"{agent_id} response #{index}"
        events.append(TaskEvent("message", {"text": text, "agent": agent_id}))
    return events


# ---------------------------------------------------------------------------
# Simulation of multi-agent plan
# ---------------------------------------------------------------------------

async def simulate_multi_agent_plan() -> list[RouteResult]:
    registry = registry_from_env()
    factory = ClientFactory()
    orchestrator = MultiAgentOrchestrator(registry, factory)
    pieces = [
        "Check weather for Paris",
        "Estimate expenses for conference",
        "Summarize itinerary",
    ]
    combined: list[RouteResult] = []
    for piece in pieces:
        result = await orchestrator.execute(piece, make_task_id())
        agent_id = orchestrator.activity_log[-1].agent_id
        combined.append(RouteResult(agent_id, result))
    return combined


# ---------------------------------------------------------------------------
# Helper functions reused across other guides
# ---------------------------------------------------------------------------

def make_task_id(prefix: str = "task") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{prefix}-{suffix}"


# ---------------------------------------------------------------------------
# Materialising reports to disk for documentation
# ---------------------------------------------------------------------------

REPORT_DIR = pathlib.Path(__file__).resolve().parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)


def write_activity_report(orchestrator: MultiAgentOrchestrator) -> pathlib.Path:
    lines = ["# Activity Report"]
    for result in orchestrator.activity_log:
        lines.append(f"Agent {result.agent_id} produced {len(result.events)} events")
        for event in result.events:
            lines.append(f"- {event.type}: {event.payload}")
    report_path = REPORT_DIR / "activity.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Inline demonstration when run as script
# ---------------------------------------------------------------------------

async def main() -> None:
    registry = registry_from_env()
    factory = ClientFactory()
    orchestrator = MultiAgentOrchestrator(registry, factory)
    await orchestrator.execute("Please submit an expense for lunch", make_task_id())
    await orchestrator.execute("Need tomorrow's weather", make_task_id())
    write_activity_report(orchestrator)
    await orchestrator.cancel("non-existent")
    metrics = MetricsCollector()
    metrics.observe("latency_ms", 120)
    metrics.observe("latency_ms", 150)
    LOG.info("Metrics report %s", metrics.report())


if __name__ == "__main__":
    asyncio.run(main())
```

```python
"""Additional orchestration helpers."""

from __future__ import annotations

import itertools
import statistics

# ---------------------------------------------------------------------------
# Host analytics utilities
# ---------------------------------------------------------------------------

@dataclass
class HostAnalytics:
    orchestrator: MultiAgentOrchestrator

    def agent_usage(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for result in self.orchestrator.activity_log:
            counts[result.agent_id] += 1
        return counts

    def transcript_digest(self) -> dict[str, list[str]]:
        digest: dict[str, list[str]] = defaultdict(list)
        for result in self.orchestrator.activity_log:
            for event in result.events:
                if event.type == "message":
                    digest[result.agent_id].append(event.payload.get("text", ""))
        return digest

    def average_messages_per_agent(self) -> dict[str, float]:
        digest = self.transcript_digest()
        return {agent: statistics.mean([len(text) for text in texts]) for agent, texts in digest.items() if texts}


# ---------------------------------------------------------------------------
# Replaying stored transcripts
# ---------------------------------------------------------------------------

@dataclass
class Transcript:
    agent_id: str
    lines: list[str]

    def replay(self) -> None:
        for line in self.lines:
            LOG.info("%s> %s", self.agent_id, line)


def store_transcripts(results: Iterable[RouteResult], directory: pathlib.Path) -> list[pathlib.Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths: list[pathlib.Path] = []
    for idx, result in enumerate(results):
        lines = [event.payload.get("text", "") for event in result.events if event.type == "message"]
        path = directory / f"transcript_{idx}_{result.agent_id}.txt"
        path.write_text("\n".join(lines), encoding="utf-8")
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# Round-robin routing strategy
# ---------------------------------------------------------------------------

@dataclass
class RoundRobinRouter:
    registry: AgentRegistry
    state: dict[str, itertools.cycle] = field(default_factory=dict)

    def select(self, tag: str) -> AgentConfig | None:
        agents = self.registry.by_tag(tag)
        if not agents:
            return None
        cycle = self.state.setdefault(tag, itertools.cycle(agents))
        return next(cycle)


# ---------------------------------------------------------------------------
# Weighted routing strategy
# ---------------------------------------------------------------------------

@dataclass
class WeightedRouter:
    registry: AgentRegistry
    weights: dict[str, int]

    def select(self, tag: str) -> AgentConfig | None:
        agents = self.registry.by_tag(tag)
        if not agents:
            return None
        expanded: list[AgentConfig] = []
        for agent in agents:
            weight = self.weights.get(agent.agent_id, 1)
            expanded.extend([agent] * weight)
        return random.choice(expanded)


# ---------------------------------------------------------------------------
# Comprehensive orchestration demo
# ---------------------------------------------------------------------------

async def run_full_orchestration_demo() -> None:
    registry = registry_from_env()
    factory = ClientFactory()
    orchestrator = MultiAgentOrchestrator(registry, factory)
    tasks = [
        "Submit expense for dinner",
        "What is the weather in Berlin?",
        "Plan travel and check weather",
        "General guidance",
    ]
    for task in tasks:
        await orchestrator.execute(task, make_task_id())
    analytics = HostAnalytics(orchestrator)
    LOG.info("Usage counts %s", analytics.agent_usage())
    LOG.info("Average message lengths %s", analytics.average_messages_per_agent())
    store_transcripts(orchestrator.activity_log, REPORT_DIR / "transcripts")


# ---------------------------------------------------------------------------
# Inline tests for new strategies
# ---------------------------------------------------------------------------

def _test_round_robin_selection() -> None:
    registry = registry_from_env()
    router = RoundRobinRouter(registry)
    first = router.select("finance")
    second = router.select("finance")
    assert first is not None
    assert second is not None


def _test_weighted_router() -> None:
    registry = registry_from_env()
    weights = {config.agent_id: 3 for config in registry.list()}
    router = WeightedRouter(registry, weights)
    chosen = router.select("finance")
    assert chosen is not None


# ---------------------------------------------------------------------------
# Execute supplementary demo when module is run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(run_full_orchestration_demo())
```
