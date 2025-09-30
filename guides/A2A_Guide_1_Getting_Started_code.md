# Guide 1 · Python Code Samples

```python
"""Guide 1 companion module.
This script-style module demonstrates how to set up the development environment,
create configuration artifacts, bootstrap the reference agent, and run smoke
checks entirely from Python.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

LOG = logging.getLogger("guide1")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent  # adapt if relocating file
ENV_FILE = PROJECT_ROOT / ".env"
VENV_DIR = PROJECT_ROOT / ".venv-guide"

# ---------------------------------------------------------------------------
# Environment bootstrap helpers
# ---------------------------------------------------------------------------

def ensure_uv_installed() -> None:
    """Install uv in the user environment if missing."""
    if shutil.which("uv"):
        LOG.info("uv already available")
        return
    LOG.info("Installing uv with pip")
    subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)


def create_virtualenv() -> None:
    """Create an isolated virtualenv with required tooling."""
    if VENV_DIR.exists():
        LOG.info("Virtualenv already present at %s", VENV_DIR)
        return
    LOG.info("Creating virtualenv at %s", VENV_DIR)
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)


def write_env_file(api_key: str = "sk-dev-123", model: str = "gpt-4o-mini") -> None:
    """Generate a minimal .env file for local runs."""
    LOG.info("Writing .env configuration")
    content = textwrap.dedent(
        f"""
        OPENAI_API_KEY={api_key}
        A2A_MODEL_NAME={model}
        A2A_TEMPERATURE=0.4
        A2A_MAX_TOKENS=1024
        A2A_HOST=127.0.0.1
        A2A_PORT=8000
        A2A_NUM_WORKERS=2
        """
    ).strip()
    ENV_FILE.write_text(content + "\n", encoding="utf-8")


def run_uv_sync() -> None:
    """Synchronise project dependencies using uv."""
    LOG.info("Running uv sync")
    subprocess.run(["uv", "sync"], cwd=PROJECT_ROOT, check=True)


def install_inspector_frontend() -> None:
    """Install Inspector frontend dependencies via Python subprocess."""
    inspector_frontend = PROJECT_ROOT / "a2a-inspector" / "frontend"
    LOG.info("Installing Inspector frontend packages")
    subprocess.run(["npm", "install"], cwd=inspector_frontend, check=True)


# ---------------------------------------------------------------------------
# Agent metadata and executor samples
# ---------------------------------------------------------------------------

@dataclass
class AgentSkillModel:
    id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
        }


def build_agent_card() -> dict[str, Any]:
    """Construct an AgentCard-style dictionary for local inspection."""
    skill_hello = AgentSkillModel(
        id="hello-world",
        name="Hello World",
        description="Greets callers with a friendly message",
        tags=["demo"],
    )
    skill_echo = AgentSkillModel(
        id="echo",
        name="Echo",
        description="Repeats text supplied in the request",
        tags=["utility"],
    )
    card = {
        "name": "Starter Agent",
        "description": "Reference implementation used in onboarding",
        "version": "1.1.0",
        "url": "http://127.0.0.1:8000",
        "capabilities": {"streaming": True, "attachments": False},
        "skills": [skill_hello.as_dict(), skill_echo.as_dict()],
        "default_input_modes": ["text"],
        "default_output_modes": ["text"],
    }
    LOG.debug("Agent card: %s", card)
    return card


def dump_agent_card(path: pathlib.Path) -> None:
    """Persist the AgentCard to disk for review."""
    card = build_agent_card()
    path.write_text(json.dumps(card, indent=2), encoding="utf-8")
    LOG.info("Agent card written to %s", path)


class GreetingExecutor:
    """Minimal example executor mirroring agents/my_agent.py behaviour."""

    def __init__(self, *, model_name: str = "gpt-4o-mini", temperature: float = 0.6) -> None:
        self.model_name = model_name
        self.temperature = temperature

    async def execute(self, text: str) -> str:
        LOG.info("Executing greeting logic with model=%s temp=%s", self.model_name, self.temperature)
        if not text:
            return "Hello!"
        return f"Hello! You said: {text}"

    async def cancel(self) -> str:
        return "Task cancelled"


# ---------------------------------------------------------------------------
# Smoke testing utilities
# ---------------------------------------------------------------------------

async def run_smoke_test(executor: GreetingExecutor) -> None:
    inputs = ["Ping", "", "Can you help me?", "Summarise the repo"]
    for item in inputs:
        result = await executor.execute(item)
        LOG.info("Input=%r output=%r", item, result)


async def run_cancel_test(executor: GreetingExecutor) -> None:
    LOG.info("Cancel result: %s", await executor.cancel())


# ---------------------------------------------------------------------------
# HTTP client simulation (no external libs to keep snippet self-contained)
# ---------------------------------------------------------------------------

def build_task_payload(text: str) -> dict[str, Any]:
    return {
        "input": {"text": text},
        "metadata": {"trace_id": f"trace-{text[:4].lower()}"},
    }


def pretend_http_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    LOG.info("Pretending to POST to %s with payload %s", url, payload)
    # Simulate immediate acceptance response
    return {"task_id": "task-123", "status": "submitted"}


def poll_fake_messages(task_id: str) -> list[dict[str, Any]]:
    LOG.info("Polling fake messages for %s", task_id)
    return [
        {"role": "agent", "parts": [{"text": "Processing"}]},
        {"role": "agent", "parts": [{"text": "Completed"}]},
    ]


# ---------------------------------------------------------------------------
# Inspector automation stubs
# ---------------------------------------------------------------------------

async def simulate_inspector_validation(agent_url: str) -> dict[str, Any]:
    LOG.info("Simulating Inspector validation for %s", agent_url)
    await asyncio.sleep(0.1)
    return {"agent_url": agent_url, "status": "pass", "warnings": []}


async def simulate_inspector_chat(agent_url: str, prompt: str) -> list[str]:
    LOG.info("Simulating Inspector chat with %s", agent_url)
    await asyncio.sleep(0.1)
    return ["Inspector> Hello!", f"Agent> Echo: {prompt}"]


# ---------------------------------------------------------------------------
# CLI utility functions
# ---------------------------------------------------------------------------

@dataclass
class CLICommand:
    name: str
    description: str
    handler: Callable[[], None]


def register_commands() -> dict[str, CLICommand]:
    commands = {
        "setup": CLICommand("setup", "Create .env and install deps", handler=run_full_setup),
        "card": CLICommand("card", "Output agent card JSON", handler=lambda: dump_agent_card(ROOT / "agent_card.json")),
        "smoke": CLICommand("smoke", "Run executor smoke tests", handler=lambda: asyncio.run(run_smoke_test(GreetingExecutor()))),
    }
    return commands


def run_full_setup() -> None:
    ensure_uv_installed()
    create_virtualenv()
    write_env_file()
    run_uv_sync()
    install_inspector_frontend()
    dump_agent_card(ROOT / "agent_card.json")


# ---------------------------------------------------------------------------
# Pytest-style helpers (illustrative)
# ---------------------------------------------------------------------------

def _test_build_task_payload() -> None:
    payload = build_task_payload("demo")
    assert payload["input"]["text"] == "demo"
    assert payload["metadata"]["trace_id"] == "trace-demo"


def _test_executor_response() -> None:
    executor = GreetingExecutor()
    result = asyncio.run(executor.execute("hello"))
    assert "hello" in result.lower()


def _test_cancel() -> None:
    executor = GreetingExecutor()
    result = asyncio.run(executor.cancel())
    assert result == "Task cancelled"


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    commands = register_commands()
    if not argv or argv[0] not in commands:
        print("Available commands:")
        for cmd in commands.values():
            print(f"  {cmd.name:8s} - {cmd.description}")
        return 0
    command = commands[argv[0]]
    command.handler()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
"""Supplementary utilities for Guide 1."""

from __future__ import annotations

import contextlib
import datetime as dt
import random
import string
from functools import wraps

# ---------------------------------------------------------------------------
# Configuration objects and factories
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class RuntimeConfig:
    host: str
    port: int
    model_name: str
    temperature: float
    max_tokens: int
    extra: dict[str, Any] = field(default_factory=dict)

    def to_env(self) -> dict[str, str]:
        base = {
            "A2A_HOST": self.host,
            "A2A_PORT": str(self.port),
            "A2A_MODEL_NAME": self.model_name,
            "A2A_TEMPERATURE": str(self.temperature),
            "A2A_MAX_TOKENS": str(self.max_tokens),
        }
        base.update({k: str(v) for k, v in self.extra.items()})
        return base


def load_runtime_config() -> RuntimeConfig:
    def _env(name: str, default: str) -> str:
        return os.environ.get(name, default)

    config = RuntimeConfig(
        host=_env("A2A_HOST", "127.0.0.1"),
        port=int(_env("A2A_PORT", "8000")),
        model_name=_env("A2A_MODEL_NAME", "gpt-4o-mini"),
        temperature=float(_env("A2A_TEMPERATURE", "0.4")),
        max_tokens=int(_env("A2A_MAX_TOKENS", "1024")),
        extra={"A2A_NUM_WORKERS": _env("A2A_NUM_WORKERS", "2")},
    )
    LOG.debug("Loaded runtime config: %s", config)
    return config


# ---------------------------------------------------------------------------
# File generators
# ---------------------------------------------------------------------------

@dataclass
class FileTemplate:
    path: pathlib.Path
    content: str

    def write(self) -> None:
        LOG.info("Writing template to %s", self.path)
        self.path.write_text(self.content, encoding="utf-8")


def generate_readme_snippet() -> FileTemplate:
    snippet = textwrap.dedent(
        """
        ## Local Agent Quickstart (Python generated)

        1. Ensure uv is installed (`python -m pip install uv`).
        2. Run `python guide_setup.py setup`.
        3. Start the agent with `uv run python main.py`.
        4. Validate using Inspector at http://127.0.0.1:5001.
        """
    ).strip()
    return FileTemplate(path=ROOT / "README_SNIPPET.md", content=snippet + "\n")


# ---------------------------------------------------------------------------
# Task simulation utilities
# ---------------------------------------------------------------------------

@dataclass
class SimulatedEvent:
    task_id: str
    role: str
    text: str
    timestamp: dt.datetime


def make_task_id(prefix: str = "task") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{suffix}"


def simulate_task_flow(prompt: str) -> list[SimulatedEvent]:
    task_id = make_task_id()
    events = [
        SimulatedEvent(task_id, "user", prompt, dt.datetime.utcnow()),
        SimulatedEvent(task_id, "agent", f"I heard: {prompt}", dt.datetime.utcnow()),
        SimulatedEvent(task_id, "agent", "Task complete", dt.datetime.utcnow()),
    ]
    LOG.info("Simulated %d events", len(events))
    return events


def export_events(events: list[SimulatedEvent], path: pathlib.Path) -> None:
    LOG.info("Exporting events to %s", path)
    serialised = [
        {
            "task_id": event.task_id,
            "role": event.role,
            "text": event.text,
            "timestamp": event.timestamp.isoformat(),
        }
        for event in events
    ]
    path.write_text(json.dumps(serialised, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Decorators and instrumentation
# ---------------------------------------------------------------------------

def time_async(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        start = dt.datetime.now(tz=dt.timezone.utc)
        try:
            return await fn(*args, **kwargs)
        finally:
            delta = dt.datetime.now(tz=dt.timezone.utc) - start
            LOG.info("%s took %.2f ms", fn.__name__, delta.total_seconds() * 1000)

    return wrapper


@time_async
async def run_full_smoke_cycle(prompt: str = "Hello") -> list[SimulatedEvent]:
    executor = GreetingExecutor()
    events = simulate_task_flow(prompt)
    result = await executor.execute(prompt)
    events.append(
        SimulatedEvent(make_task_id("apm"), "agent", f"Executor said: {result}", dt.datetime.utcnow())
    )
    return events


# ---------------------------------------------------------------------------
# Inspector-like behaviours using asyncio streams
# ---------------------------------------------------------------------------

async def fake_inspector_session(url: str, prompts: Iterable[str]) -> dict[str, Any]:
    await asyncio.sleep(0.05)
    transcript = []
    for prompt in prompts:
        transcript.append({"role": "user", "text": prompt})
        transcript.append({"role": "agent", "text": f"Echo: {prompt}"})
    LOG.info("Inspector session with %s produced %d exchanges", url, len(transcript))
    return {
        "agent_url": url,
        "transcript": transcript,
        "validated_at": dt.datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Async command runner for uv / npm from Python
# ---------------------------------------------------------------------------

async def run_async_command(cmd: Sequence[str], cwd: pathlib.Path | None = None) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd) if cwd else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {stderr.decode()}")
    return stdout.decode()


async def run_async_uv_sync() -> None:
    output = await run_async_command(["uv", "sync"], cwd=PROJECT_ROOT)
    LOG.info("uv sync output:\n%s", output)


# ---------------------------------------------------------------------------
# Context managers for temporary environments
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def temporary_env(vars: dict[str, str]):
    original = {key: os.environ.get(key) for key in vars}
    os.environ.update(vars)
    try:
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


# ---------------------------------------------------------------------------
# Comprehensive demo orchestrator
# ---------------------------------------------------------------------------

async def orchestrate_full_demo(prompt: str = "Plan a deployment") -> None:
    LOG.info("=== Environment setup ===")
    ensure_uv_installed()
    create_virtualenv()
    write_env_file()
    LOG.info("=== Building card ===")
    card_path = ROOT / "card.json"
    dump_agent_card(card_path)
    LOG.info("=== Running smoke cycle ===")
    events = await run_full_smoke_cycle(prompt)
    export_events(events, ROOT / "events.json")
    LOG.info("=== Simulating inspector ===")
    inspector_report = await fake_inspector_session("http://127.0.0.1:8000", [prompt])
    (ROOT / "inspector.json").write_text(json.dumps(inspector_report, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Utility to embed README snippet and event log creation
# ---------------------------------------------------------------------------

def generate_all_artifacts() -> None:
    template = generate_readme_snippet()
    template.write()
    card_path = ROOT / "card.json"
    dump_agent_card(card_path)
    events = simulate_task_flow("Stress test guidance")
    export_events(events, ROOT / "events.json")


# ---------------------------------------------------------------------------
# Entry point for asynchronous orchestration via CLI flag
# ---------------------------------------------------------------------------

def main_async() -> None:
    asyncio.run(orchestrate_full_demo())


# ---------------------------------------------------------------------------
# Additional pytests for helper utilities
# ---------------------------------------------------------------------------

def _test_make_task_id() -> None:
    task_id = make_task_id()
    assert task_id.startswith("task-")
    assert len(task_id.split("-")) == 2


def _test_runtime_config_roundtrip() -> None:
    config = RuntimeConfig("0.0.0.0", 9000, "gpt", 0.2, 768)
    env = config.to_env()
    assert env["A2A_PORT"] == "9000"


# ---------------------------------------------------------------------------
# Data classes for documentation summarisation
# ---------------------------------------------------------------------------

@dataclass
class DocumentSummary:
    path: pathlib.Path
    headline: str
    actions: list[str]

    def render(self) -> str:
        steps = "\n".join(f"- {item}" for item in self.actions)
        return textwrap.dedent(
            f"""
            {self.headline}
            Steps:\n{steps}
            File: {self.path}
            """
        )


def collect_document_summaries(paths: Iterable[pathlib.Path]) -> list[DocumentSummary]:
    summaries: list[DocumentSummary] = []
    for path in paths:
        actions = ["Review", "Update", "Validate"]
        summaries.append(DocumentSummary(path=path, headline=f"Summary for {path.name}", actions=actions))
    return summaries


# ---------------------------------------------------------------------------
# Introspection utilities for generated artifacts
# ---------------------------------------------------------------------------

def report_artifacts(directory: pathlib.Path) -> list[str]:
    report: list[str] = []
    for item in directory.iterdir():
        if item.is_file():
            size = item.stat().st_size
            report.append(f"{item.name}: {size} bytes")
    return report


# ---------------------------------------------------------------------------
# Self-check routine to run all inline tests
# ---------------------------------------------------------------------------

def run_inline_tests() -> None:
    _test_build_task_payload()
    _test_executor_response()
    _test_cancel()
    _test_make_task_id()
    _test_runtime_config_roundtrip()
    LOG.info("All inline tests passed")


# ---------------------------------------------------------------------------
# End of supplementary module
# ---------------------------------------------------------------------------
```
