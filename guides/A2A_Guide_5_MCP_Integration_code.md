# Guide 5 · Python Code Samples

```python
"""MCP bridge utilities expressed purely in Python."""

from __future__ import annotations

import asyncio
import dataclasses
import datetime as dt
import json
import logging
import random
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Iterable

LOG = logging.getLogger("guide5")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# MCP client abstractions
# ---------------------------------------------------------------------------

@dataclass
class MCPResponseChunk:
    kind: str
    data: Any


class MCPClient:
    def __init__(self, endpoint: str, token: str) -> None:
        self.endpoint = endpoint
        self.token = token

    async def connect(self) -> None:
        LOG.info("Connecting to MCP server %s", self.endpoint)
        await asyncio.sleep(0.01)

    async def close(self) -> None:
        LOG.info("Closing MCP connection")
        await asyncio.sleep(0.01)

    async def list_tools(self) -> list[dict[str, Any]]:
        await asyncio.sleep(0.02)
        return [
            {
                "name": "weather",
                "display_name": "Weather Lookup",
                "description": "Returns weather data",
                "input_schema": {
                    "properties": {
                        "location": {"type": "string", "description": "City name"}
                    },
                    "required": ["location"],
                },
            }
        ]

    async def call_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(0.02)
        return {"tool": name, "result": f"Processed {payload}"}

    async def call_tool_stream(self, name: str, payload: dict[str, Any]) -> AsyncIterator[MCPResponseChunk]:
        yield MCPResponseChunk("text", f"Invoking {name} with {payload}")
        await asyncio.sleep(0.01)
        yield MCPResponseChunk("json", {"status": "done"})


# ---------------------------------------------------------------------------
# Conversion from MCP tool definitions to A2A-compatible structures
# ---------------------------------------------------------------------------

@dataclass
class ToolParameter:
    name: str
    type: str
    required: bool
    description: str


@dataclass
class AgentTool:
    identifier: str
    name: str
    description: str
    parameters: list[ToolParameter]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.identifier,
            "name": self.name,
            "description": self.description,
            "parameters": [dataclasses.asdict(param) for param in self.parameters],
        }


def convert_tool(tool: dict[str, Any]) -> AgentTool:
    properties = tool.get("input_schema", {}).get("properties", {})
    required = tool.get("input_schema", {}).get("required", [])
    parameters = [
        ToolParameter(name=name, type=spec.get("type", "string"), required=name in required, description=spec.get("description", ""))
        for name, spec in properties.items()
    ]
    return AgentTool(tool["name"], tool.get("display_name", tool["name"]), tool.get("description", ""), parameters)


# ---------------------------------------------------------------------------
# Bridge executor
# ---------------------------------------------------------------------------

@dataclass
class MCPBridgeExecutor:
    client_factory: Callable[[], MCPClient]

    async def execute(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        async with MCPClientContext(self.client_factory()) as client:
            tool = payload.get("tool")
            if not tool:
                raise ValueError("Tool not specified")
            results = []
            async for chunk in client.call_tool_stream(tool, payload.get("input", {})):
                if chunk.kind == "text":
                    results.append({"type": "message", "text": chunk.data})
                elif chunk.kind == "json":
                    results.append({"type": "artifact", "data": chunk.data})
            return results


@dataclass
class MCPClientContext:
    client: MCPClient

    async def __aenter__(self) -> MCPClient:
        await self.client.connect()
        return self.client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.client.close()


# ---------------------------------------------------------------------------
# Tool catalog builder
# ---------------------------------------------------------------------------

async def build_tool_catalog(factory: Callable[[], MCPClient]) -> list[dict[str, Any]]:
    async with MCPClientContext(factory()) as client:
        raw_tools = await client.list_tools()
    return [convert_tool(tool).as_dict() for tool in raw_tools]


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

async def call_with_retries(client: MCPClient, name: str, payload: dict[str, Any], attempts: int = 3) -> dict[str, Any]:
    for attempt in range(1, attempts + 1):
        try:
            return await client.call_tool(name, payload)
        except Exception as exc:  # noqa: BLE001
            LOG.warning("Attempt %s failed: %s", attempt, exc)
            await asyncio.sleep(0.05)
    raise RuntimeError("All attempts failed")


# ---------------------------------------------------------------------------
# Bridge harness for direct invocation
# ---------------------------------------------------------------------------

@dataclass
class BridgeHarness:
    executor: MCPBridgeExecutor

    async def invoke(self, tool: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        request = {"tool": tool, "input": payload}
        return await self.executor.execute(request)


# ---------------------------------------------------------------------------
# Transcript generator for documentation
# ---------------------------------------------------------------------------

def generate_transcript(tool: str, payload: dict[str, Any], responses: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tool": tool,
        "input": payload,
        "responses": list(responses),
        "generated_at": dt.datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Synthetic compliance checks
# ---------------------------------------------------------------------------

@dataclass
class ComplianceCheck:
    name: str
    passed: bool
    details: str


def run_compliance_checks() -> list[ComplianceCheck]:
    checks = [
        ComplianceCheck("schema", True, "Schema validated"),
        ComplianceCheck("auth", True, "Token supplied"),
        ComplianceCheck("rate_limit", True, "Within thresholds"),
    ]
    return checks


# ---------------------------------------------------------------------------
# Metrics collection for bridge latency
# ---------------------------------------------------------------------------

@dataclass
class BridgeMetrics:
    latencies_ms: list[float] = field(default_factory=list)

    def record(self, duration_ms: float) -> None:
        self.latencies_ms.append(duration_ms)

    def summary(self) -> dict[str, float]:
        average = sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 0.0
        peak = max(self.latencies_ms) if self.latencies_ms else 0.0
        return {"average_ms": average, "peak_ms": peak}


# ---------------------------------------------------------------------------
# CLI-style helpers
# ---------------------------------------------------------------------------

async def list_and_print_tools(factory: Callable[[], MCPClient]) -> None:
    catalog = await build_tool_catalog(factory)
    LOG.info("Available tools: %s", catalog)


async def run_single_call(factory: Callable[[], MCPClient], tool: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with MCPClientContext(factory()) as client:
        return await client.call_tool(tool, payload)


# ---------------------------------------------------------------------------
# Demo routine orchestrating multiple calls
# ---------------------------------------------------------------------------

async def run_demo() -> None:
    factory = lambda: MCPClient("https://mcp.example.com", "token")
    await list_and_print_tools(factory)
    harness = BridgeHarness(MCPBridgeExecutor(factory))
    responses = await harness.invoke("weather", {"location": "Paris"})
    transcript = generate_transcript("weather", {"location": "Paris"}, responses)
    LOG.info("Transcript %s", json.dumps(transcript, indent=2))
    metrics = BridgeMetrics()
    for _ in range(5):
        start = dt.datetime.utcnow()
        await harness.invoke("weather", {"location": random.choice(["Paris", "London"])})
        metrics.record((dt.datetime.utcnow() - start).total_seconds() * 1000)
    LOG.info("Metrics %s", metrics.summary())


# ---------------------------------------------------------------------------
# Inline tests for the bridge
# ---------------------------------------------------------------------------

async def _test_convert_tool() -> None:
    tool = {
        "name": "echo",
        "display_name": "Echo",
        "description": "Repeats",
        "input_schema": {"properties": {"text": {"type": "string"}}, "required": ["text"]},
    }
    converted = convert_tool(tool)
    assert converted.parameters[0].name == "text"


async def _test_bridge_executor() -> None:
    factory = lambda: MCPClient("https://mcp.example.com", "token")
    executor = MCPBridgeExecutor(factory)
    responses = await executor.execute({"tool": "weather", "input": {"location": "Berlin"}})
    assert responses and responses[0]["type"] == "message"


if __name__ == "__main__":
    asyncio.run(run_demo())
```

```python
"""Supplementary MCP bridge helpers."""

from __future__ import annotations

import pathlib

# ---------------------------------------------------------------------------
# Cached tool metadata
# ---------------------------------------------------------------------------

@dataclass
class ToolCache:
    path: Path

    def load(self) -> list[dict[str, Any]] | None:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, tools: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(tools, indent=2), encoding="utf-8")


async def cached_tool_catalog(factory: Callable[[], MCPClient], cache: ToolCache) -> list[dict[str, Any]]:
    cached = cache.load()
    if cached is not None:
        return cached
    catalog = await build_tool_catalog(factory)
    cache.save(catalog)
    return catalog


# ---------------------------------------------------------------------------
# Stream replay utility
# ---------------------------------------------------------------------------

async def replay_stream(chunks: Iterable[MCPResponseChunk]) -> list[str]:
    lines: list[str] = []
    for chunk in chunks:
        if chunk.kind == "text":
            lines.append(chunk.data)
        elif chunk.kind == "json":
            lines.append(json.dumps(chunk.data))
    return lines


# ---------------------------------------------------------------------------
# Asynchronous unit tests executed manually
# ---------------------------------------------------------------------------

async def run_inline_tests() -> None:
    await _test_convert_tool()
    await _test_bridge_executor()
    LOG.info("Bridge inline tests passed")


# ---------------------------------------------------------------------------
# Integration scenario combining caching and execution
# ---------------------------------------------------------------------------

async def integration_scenario(tmp_dir: Path) -> None:
    cache = ToolCache(tmp_dir / "tools.json")
    factory = lambda: MCPClient("https://mcp.example.com", "token")
    catalog = await cached_tool_catalog(factory, cache)
    LOG.info("Cached catalog %s", catalog)
    harness = BridgeHarness(MCPBridgeExecutor(factory))
    responses = await harness.invoke("weather", {"location": "Rome"})
    transcript = generate_transcript("weather", {"location": "Rome"}, responses)
    (tmp_dir / "transcript.json").write_text(json.dumps(transcript, indent=2), encoding="utf-8")


if __name__ == "__main__":
    temp_dir = Path("./tmp-mcp")
    temp_dir.mkdir(exist_ok=True)
    asyncio.run(integration_scenario(temp_dir))
```

```python
"""Additional examples for niche scenarios."""

from __future__ import annotations

import statistics

# ---------------------------------------------------------------------------
# Batched requests with per-tool metrics
# ---------------------------------------------------------------------------

@dataclass
class BatchedCallResult:
    tool: str
    payload: dict[str, Any]
    response: dict[str, Any]
    latency_ms: float


async def batched_calls(factory: Callable[[], MCPClient], requests: list[tuple[str, dict[str, Any]]]) -> list[BatchedCallResult]:
    results: list[BatchedCallResult] = []
    async with MCPClientContext(factory()) as client:
        for tool, payload in requests:
            start = dt.datetime.utcnow()
            response = await client.call_tool(tool, payload)
            duration = (dt.datetime.utcnow() - start).total_seconds() * 1000
            results.append(BatchedCallResult(tool, payload, response, duration))
    return results


def summarise_batch(results: list[BatchedCallResult]) -> dict[str, Any]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for result in results:
        grouped[result.tool].append(result.latency_ms)
    summary = {
        tool: {
            "average_latency": statistics.mean(latencies),
            "peak_latency": max(latencies),
            "calls": len(latencies),
        }
        for tool, latencies in grouped.items()
    }
    return summary


# ---------------------------------------------------------------------------
# Error translation examples
# ---------------------------------------------------------------------------

@dataclass
class MCPError(Exception):
    code: str
    message: str


ERROR_TRANSLATIONS = {
    "UnknownTool": "The requested tool is not available",
    "InvalidPayload": "Provided payload does not match schema",
}


def translate_error(code: str) -> MCPError:
    message = ERROR_TRANSLATIONS.get(code, "Unexpected MCP error")
    return MCPError(code, message)


# ---------------------------------------------------------------------------
# Extended demo for batched requests and error handling
# ---------------------------------------------------------------------------

async def extended_demo() -> None:
    factory = lambda: MCPClient("https://mcp.example.com", "token")
    requests = [
        ("weather", {"location": "Lisbon"}),
        ("weather", {"location": "Madrid"}),
        ("weather", {"location": "Prague"}),
    ]
    results = await batched_calls(factory, requests)
    summary = summarise_batch(results)
    LOG.info("Batch summary %s", summary)


if __name__ == "__main__":
    asyncio.run(extended_demo())
```

```python
"""Final utilities for MCP integration."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Async context manager for simulated streaming sessions
# ---------------------------------------------------------------------------

@dataclass
class MCPSession:
    client: MCPClient
    tool: str
    payload: dict[str, Any]

    async def __aenter__(self) -> AsyncIterator[MCPResponseChunk]:
        await self.client.connect()
        self._iterator = self.client.call_tool_stream(self.tool, self.payload)
        return self._iterator

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.client.close()


# ---------------------------------------------------------------------------
# Trace logger for MCP sessions
# ---------------------------------------------------------------------------

@dataclass
class MCPTraceLogger:
    path: Path

    def record(self, transcript: dict[str, Any]) -> None:
        existing = []
        if self.path.exists():
            existing = json.loads(self.path.read_text(encoding="utf-8"))
        existing.append(transcript)
        self.path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Synthetic streaming run that stores traces
# ---------------------------------------------------------------------------

async def record_streaming_trace(factory: Callable[[], MCPClient], tool: str, payload: dict[str, Any], trace_path: Path) -> None:
    client = factory()
    logger = MCPTraceLogger(trace_path)
    async with MCPSession(client, tool, payload) as stream:
        chunks = [chunk async for chunk in stream]
    transcript = generate_transcript(tool, payload, [{"type": chunk.kind, "data": chunk.data} for chunk in chunks])
    logger.record(transcript)


# ---------------------------------------------------------------------------
# Execute recording when invoked as script
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    out_path = Path("mcp_traces.json")
    factory = lambda: MCPClient("https://mcp.example.com", "token")
    asyncio.run(record_streaming_trace(factory, "weather", {"location": "Dublin"}, out_path))
```
