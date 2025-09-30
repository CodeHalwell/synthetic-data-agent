# Guide 4 · Python Code Samples

```python
"""Framework integration helpers for Guide 4.
The module demonstrates wrapping different agent frameworks in pure Python,
including adapters, fallbacks, instrumentation, and testing patterns.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

LOG = logging.getLogger("guide4")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Framework-neutral interface definitions
# ---------------------------------------------------------------------------

class FrameworkResult(Protocol):
    content: str


class FrameworkRunner(Protocol):
    async def arun(self, prompt: str) -> FrameworkResult:
        ...


@dataclass
class SimpleFrameworkResult:
    content: str


# ---------------------------------------------------------------------------
# LangChain-style adapter stubs
# ---------------------------------------------------------------------------

@dataclass
class LangChainMock:
    name: str = "langchain"

    async def apredict(self, prompt: str) -> str:
        await asyncio.sleep(0.02)
        return f"LangChain response to: {prompt}"


@dataclass
class LangChainAdapter:
    chain: LangChainMock

    async def arun(self, prompt: str) -> FrameworkResult:
        LOG.info("LangChainAdapter executing prompt %s", prompt)
        text = await self.chain.apredict(prompt)
        return SimpleFrameworkResult(text)


# ---------------------------------------------------------------------------
# LangGraph-style adapter stubs
# ---------------------------------------------------------------------------

@dataclass
class LangGraphMock:
    name: str = "langgraph"

    async def astream(self, prompt: str) -> AsyncIterator[str]:
        for token in ["Plan", " -> ", prompt.upper()]:
            await asyncio.sleep(0.01)
            yield token


@dataclass
class LangGraphAdapter:
    graph: LangGraphMock

    async def arun(self, prompt: str) -> FrameworkResult:
        LOG.info("LangGraphAdapter streaming prompt %s", prompt)
        parts: list[str] = []
        async for token in self.graph.astream(prompt):
            parts.append(token)
        return SimpleFrameworkResult("".join(parts))


# ---------------------------------------------------------------------------
# CrewAI-style adapter stubs
# ---------------------------------------------------------------------------

@dataclass
class CrewAIMock:
    agents: list[str]

    def kickoff(self, topic: str) -> str:
        time.sleep(0.05)
        return f"Crew completed task on {topic} using {', '.join(self.agents)}"


@dataclass
class CrewAIAdapter:
    crew: CrewAIMock

    async def arun(self, prompt: str) -> FrameworkResult:
        LOG.info("CrewAIAdapter running topic %s", prompt)
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, self.crew.kickoff, prompt)
        return SimpleFrameworkResult(text)


# ---------------------------------------------------------------------------
# LlamaIndex-style adapter stubs
# ---------------------------------------------------------------------------

@dataclass
class LlamaIndexMock:
    documents: list[str] = field(default_factory=list)

    def insert(self, text: str) -> None:
        self.documents.append(text)

    async def aquery(self, prompt: str) -> str:
        await asyncio.sleep(0.02)
        joined = " ".join(self.documents[-3:])
        return f"Relevant context: {joined}\nAnswer: summarised for {prompt}"


@dataclass
class LlamaIndexAdapter:
    index: LlamaIndexMock

    async def arun(self, prompt: str) -> FrameworkResult:
        LOG.info("LlamaIndexAdapter answering prompt %s", prompt)
        text = await self.index.aquery(prompt)
        return SimpleFrameworkResult(text)


# ---------------------------------------------------------------------------
# Hybrid executor wiring multiple frameworks
# ---------------------------------------------------------------------------

@dataclass
class HybridExecutor:
    primary: LangChainAdapter
    fallback: LangGraphAdapter
    telemetry: list[str] = field(default_factory=list)

    async def execute(self, prompt: str) -> str:
        try:
            result = await self.primary.arun(prompt)
            self.telemetry.append("primary")
            return result.content
        except Exception as exc:  # noqa: BLE001
            LOG.warning("Primary failed with %s; using fallback", exc)
            result = await self.fallback.arun(prompt)
            self.telemetry.append("fallback")
            return result.content


# ---------------------------------------------------------------------------
# Tool integration using python callables
# ---------------------------------------------------------------------------

@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: Callable[..., str]

    def invoke(self, **kwargs: Any) -> str:
        LOG.debug("Invoking tool %s with %s", self.name, kwargs)
        return self.handler(**kwargs)


def build_currency_tool() -> ToolDefinition:
    def handler(amount: float, currency: str) -> str:
        return f"Processed {amount:.2f} {currency}"

    return ToolDefinition("currency_convert", "Convert currency values", handler)


def build_weather_tool() -> ToolDefinition:
    def handler(location: str) -> str:
        return f"Weather for {location}: sunny"

    return ToolDefinition("weather_lookup", "Get weather information", handler)


# ---------------------------------------------------------------------------
# Adapter pipeline to execute tools before frameworks
# ---------------------------------------------------------------------------

@dataclass
class ToolAwareExecutor:
    executor: HybridExecutor
    tools: dict[str, ToolDefinition]

    async def execute(self, payload: dict[str, Any]) -> str:
        tool = payload.get("tool")
        if tool:
            definition = self.tools.get(tool)
            if not definition:
                raise ValueError(f"Unknown tool {tool}")
            result = definition.invoke(**payload.get("input", {}))
            return result
        prompt = payload.get("prompt", "")
        return await self.executor.execute(prompt)


# ---------------------------------------------------------------------------
# Observability wrappers
# ---------------------------------------------------------------------------

def traced_executor(func: Callable[..., Any]) -> Callable[..., Any]:
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return await func(*args, **kwargs)
        finally:
            LOG.info("%s took %.2f ms", func.__name__, (time.time() - start) * 1000)

    return wrapper


# ---------------------------------------------------------------------------
# Integration tests for adapters
# ---------------------------------------------------------------------------

async def _test_langchain_adapter() -> None:
    adapter = LangChainAdapter(LangChainMock())
    result = await adapter.arun("hello")
    assert "LangChain" in result.content


async def _test_langgraph_adapter() -> None:
    adapter = LangGraphAdapter(LangGraphMock())
    result = await adapter.arun("plan")
    assert "PLAN" in result.content


async def _test_hybrid_executor() -> None:
    hybrid = HybridExecutor(LangChainAdapter(LangChainMock()), LangGraphAdapter(LangGraphMock()))
    output = await hybrid.execute("explain A2A")
    assert "LangChain" in output or "PLAN" in output


# ---------------------------------------------------------------------------
# Multi-provider orchestrator using only python
# ---------------------------------------------------------------------------

@dataclass
class ProviderConfig:
    name: str
    adapter_builder: Callable[[], FrameworkRunner]


class ProviderRouter:
    def __init__(self, providers: list[ProviderConfig]) -> None:
        self.providers = providers

    def select(self, capability: str) -> FrameworkRunner:
        idx = sum(ord(c) for c in capability) % len(self.providers)
        return self.providers[idx].adapter_builder()


# ---------------------------------------------------------------------------
# Configuration of provider router
# ---------------------------------------------------------------------------

def build_provider_router() -> ProviderRouter:
    return ProviderRouter(
        [
            ProviderConfig("langchain", lambda: LangChainAdapter(LangChainMock())),
            ProviderConfig("langgraph", lambda: LangGraphAdapter(LangGraphMock())),
            ProviderConfig("crewai", lambda: CrewAIAdapter(CrewAIMock(["planner", "writer"]))),
        ]
    )


# ---------------------------------------------------------------------------
# Scenario simulation for integration tests
# ---------------------------------------------------------------------------

async def simulate_framework_workflow(prompt: str) -> dict[str, Any]:
    router = build_provider_router()
    adapter = router.select(prompt)
    result = await adapter.arun(prompt)
    return {"prompt": prompt, "response": result.content}


# ---------------------------------------------------------------------------
# Batch execution helper
# ---------------------------------------------------------------------------

async def execute_batch(prompts: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for prompt in prompts:
        outcome = await simulate_framework_workflow(prompt)
        results.append(outcome)
    return results


# ---------------------------------------------------------------------------
# Synthetic metrics recorder
# ---------------------------------------------------------------------------

@dataclass
class ExecutionMetrics:
    durations_ms: list[float] = field(default_factory=list)
    successes: int = 0
    failures: int = 0

    def record(self, duration_ms: float, success: bool) -> None:
        self.durations_ms.append(duration_ms)
        if success:
            self.successes += 1
        else:
            self.failures += 1

    def summary(self) -> dict[str, Any]:
        average = sum(self.durations_ms) / len(self.durations_ms) if self.durations_ms else 0.0
        return {
            "average_ms": average,
            "successes": self.successes,
            "failures": self.failures,
        }


# ---------------------------------------------------------------------------
# Fallback chains with structured retries
# ---------------------------------------------------------------------------

@dataclass
class RetryExecutor:
    adapters: list[FrameworkRunner]
    max_attempts: int = 3

    async def execute(self, prompt: str) -> str:
        for attempt, adapter in enumerate(self.adapters, start=1):
            try:
                result = await adapter.arun(prompt)
                return result.content
            except Exception as exc:  # noqa: BLE001
                LOG.warning("Attempt %s failed: %s", attempt, exc)
                await asyncio.sleep(0.05)
        raise RuntimeError("All adapters failed")


# ---------------------------------------------------------------------------
# Tool-aware hybrid executor
# ---------------------------------------------------------------------------

async def tool_first_executor(prompt: str, payload: dict[str, Any]) -> str:
    tools = {tool.name: tool for tool in [build_currency_tool(), build_weather_tool()]}
    executor = ToolAwareExecutor(
        HybridExecutor(LangChainAdapter(LangChainMock()), LangGraphAdapter(LangGraphMock())),
        tools,
    )
    return await executor.execute({"prompt": prompt, **payload})


# ---------------------------------------------------------------------------
# Sample dataset generator for prompts
# ---------------------------------------------------------------------------

def synthetic_prompts() -> list[str]:
    topics = [
        "summarise A2A architecture",
        "plan agent deployment",
        "explain security requirements",
        "draft integration checklist",
    ]
    return topics


# ---------------------------------------------------------------------------
# Combined demo routine
# ---------------------------------------------------------------------------

async def run_demo() -> None:
    metrics = ExecutionMetrics()
    for prompt in synthetic_prompts():
        start = time.time()
        try:
            response = await tool_first_executor(prompt, {})
            LOG.info("Response for %s -> %s", prompt, response[:40])
            metrics.record((time.time() - start) * 1000, True)
        except Exception:  # noqa: BLE001
            metrics.record((time.time() - start) * 1000, False)
    LOG.info("Metrics summary %s", metrics.summary())


# ---------------------------------------------------------------------------
# Inline async tests execution
# ---------------------------------------------------------------------------

async def run_inline_tests() -> None:
    await _test_langchain_adapter()
    await _test_langgraph_adapter()
    await _test_hybrid_executor()
    LOG.info("Adapter tests passed")


if __name__ == "__main__":
    asyncio.run(run_demo())
```

```python
"""Supplementary adapters and utilities."""

from __future__ import annotations

import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Prompt normalisation and validation
# ---------------------------------------------------------------------------

def normalise_prompt(prompt: str) -> str:
    return " ".join(prompt.split())


def validate_prompt(prompt: str, max_length: int = 4000) -> None:
    if len(prompt) > max_length:
        raise ValueError("Prompt exceeds maximum length")


# ---------------------------------------------------------------------------
# Adapter composition utilities
# ---------------------------------------------------------------------------

@dataclass
class AdapterPipeline:
    steps: list[Callable[[str], str]]

    def run(self, prompt: str) -> str:
        value = prompt
        for step in self.steps:
            value = step(value)
        return value


# ---------------------------------------------------------------------------
# Sample pipeline creation
# ---------------------------------------------------------------------------

def build_pipeline() -> AdapterPipeline:
    return AdapterPipeline([
        normalise_prompt,
        str.lower,
        lambda text: text.replace("a2a", "Agent-to-Agent"),
    ])


# ---------------------------------------------------------------------------
# File-based caching of framework responses
# ---------------------------------------------------------------------------

@dataclass
class ResponseCache:
    path: Path

    def save(self, prompt: str, response: str) -> None:
        key = prompt.replace(" ", "_")[:40]
        file = self.path / f"cache_{key}.txt"
        file.write_text(response, encoding="utf-8")

    def load(self, prompt: str) -> str | None:
        key = prompt.replace(" ", "_")[:40]
        file = self.path / f"cache_{key}.txt"
        if file.exists():
            return file.read_text(encoding="utf-8")
        return None


# ---------------------------------------------------------------------------
# Cached executor wrapper
# ---------------------------------------------------------------------------

@dataclass
class CachedExecutor:
    executor: HybridExecutor
    cache: ResponseCache

    async def execute(self, prompt: str) -> str:
        cached = self.cache.load(prompt)
        if cached:
            LOG.info("Returning cached response for %s", prompt)
            return cached
        result = await self.executor.execute(prompt)
        self.cache.save(prompt, result)
        return result


# ---------------------------------------------------------------------------
# Token counting utility
# ---------------------------------------------------------------------------

@dataclass
class TokenCounter:
    token_size: int = 4

    def estimate(self, text: str) -> int:
        return math.ceil(len(text) / self.token_size)


# ---------------------------------------------------------------------------
# Example integration test for cached executor
# ---------------------------------------------------------------------------

async def _test_cached_executor(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path)
    executor = CachedExecutor(
        HybridExecutor(LangChainAdapter(LangChainMock()), LangGraphAdapter(LangGraphMock())),
        cache,
    )
    result1 = await executor.execute("describe integration")
    result2 = await executor.execute("describe integration")
    assert result1 == result2


# ---------------------------------------------------------------------------
# Run supplementary demo
# ---------------------------------------------------------------------------

async def supplementary_demo(tmp_dir: Path) -> None:
    cache = ResponseCache(tmp_dir)
    executor = CachedExecutor(
        HybridExecutor(LangChainAdapter(LangChainMock()), LangGraphAdapter(LangGraphMock())),
        cache,
    )
    pipeline = build_pipeline()
    prompt = pipeline.run("Explain A2A integration")
    response = await executor.execute(prompt)
    LOG.info("Supplementary response: %s", response)


if __name__ == "__main__":
    temp = Path("./tmp-cache")
    temp.mkdir(exist_ok=True)
    asyncio.run(supplementary_demo(temp))
```
