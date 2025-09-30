# A2A Guide 1 · Getting Started

This guide covers the essentials for bringing up an A2A-compliant agent from scratch, validating it with the A2A Inspector, and exploring the canonical samples. It compiles practical notes from the upstream [`a2a-samples`](./a2a-samples) repository, the [`a2a-inspector`](./a2a-inspector) tool, and the SDK manifest.

## 1. Environment Setup

### Prerequisites
- Python 3.11 or newer (samples target 3.12/3.13; align your interpreter when reusing code).
- [`uv`](https://docs.astral.sh/uv/) for Python dependency management.
- Node.js 18+ and npm (Inspector front-end).
- Access to at least one supported model provider (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, etc.).
- Optional: Docker or Podman if you prefer containerized workflows as demonstrated in `a2a-samples/demo/ui/Containerfile` and `a2a-inspector/Dockerfile`.

### Install Dependencies
```bash
uv sync                                         # installs Python deps from pyproject.toml + uv.lock
npm install --prefix a2a-inspector/frontend     # prepares the Inspector frontend assets
```

### Configure Environment Variables
Create `.env` with at minimum:
```
OPENAI_API_KEY=sk-...
```
Add provider-specific keys as needed (Gemini, Vertex AI, Anthropic). Override runtime defaults using the `A2A_*` variables consumed by `config/congfig.py`, for example:
```
A2A_HOST=0.0.0.0
A2A_PORT=8080
A2A_MODEL_NAME=gpt-4o-mini
A2A_TEMPERATURE=0.4
```

## 2. Understand the Minimal Agent

| Component | Location | Responsibilities |
| --- | --- | --- |
| Agent metadata | `agent_skills/skills.py` | Defines `AgentCard`, `AgentSkill`, and capabilities exposed to other agents. |
| Executor | `agents/my_agent.py` | Implements `LLMAgentExecutor` by subclassing `AgentExecutor` and emitting events via `EventQueue`. |
| Application wiring | `main.py` | Ties together executor, card, `DefaultRequestHandler`, and `InMemoryTaskStore` into an `A2AStarletteApplication`. |
| Config | `config/congfig.py` | Pydantic model reading `A2A_*` variables to keep runtime settings centralized. |

Key points:
- `AgentCard` is public and must remain accurate—hosts rely on its skills, URL, auth schemes, and version when negotiating tasks.
- `AgentExecutor.execute()` should be deterministic. Use dependency injection for external services so you can mock them in tests.
- The default setup streams responses; verify the `capabilities` flags reflect this so hosts can request streaming output.

## 3. Boot & Smoke Test the Agent

```bash
uv run python main.py
```

Verify the manifest:
```bash
curl http://127.0.0.1:8000/.well-known/agent.json | jq
```
Expected fields include `name`, `description`, `version`, `capabilities`, and a list of skills. Common issues:
- HTTP 500 ⇒ environment variables missing or executor import failure.
- Missing skills ⇒ ensure `agent_skills/skills.py` exports the right skill list.

Send a task via curl (simplified REST path):
```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"input": {"text": "Say hello"}}'
```
Use the returned `task_id` to poll `/tasks/{id}` or `/tasks/{id}/messages`.

## 4. Validate with A2A Inspector

Inspector shortens the feedback loop by verifying AgentCards, exercising transports, and visualizing JSON-RPC traffic.

```bash
bash a2a-inspector/scripts/run.sh
# or manually: uv run a2a-inspector/backend/app.py & npm run dev --prefix a2a-inspector/frontend
```

Open http://127.0.0.1:5001 and connect to your agent URL. Confirm:
- **Agent Card View** shows green checks for required fields. Warnings about missing descriptions or unsupported security schemes signal documentation gaps.
- **Live Chat** round-trips a message and displays streaming updates. If nothing appears, inspect the backend console for transport errors.
- **Debug Console** logs raw JSON-RPC payloads—save these as regression artifacts with your pull requests.

Pro tip: The Inspector backend exposes a WebSocket API; integrate it into CI to automate manifest verification on every commit.

## 5. Learn from `a2a-samples`

The mirrored `a2a-samples` directory illustrates a wide spectrum of deployments:

- `samples/python/agents/helloworld` – Minimal executor & server using `A2AServer` helper.
- `samples/python/agents/langgraph` – LangGraph planner wrapped in an A2A executor with streaming events.
- `samples/python/agents/adk_expense_reimbursement` – Google ADK agent bridging tool usage and multi-turn clarifications.
- `samples/python/hosts/cli` – Simple host using `A2AClient` to send tasks via the command line.
- `samples/python/hosts/multiagent` – Host agent orchestrating multiple remote agents; a blueprint for Guide 3.
- `demo/ui` – Mesop front-end that delegates work to remote agents and displays artifacts like forms and images.
- `samples/js`, `samples/java`, `samples/go`, `samples/dotnet` – Cross-language references proving transport interoperability.
- `extensions/timestamp` & `extensions/traceability` – Implementation of optional protocol extensions, referenced in Guide 7.

Each sample includes a README with commands, prerequisites, and security caveats (notably the reminder to treat external agents as untrusted input). Use these as templates when documenting your own agents.

## 6. Next Steps

- Proceed to **Guide 2** for deep dives into executor design, tooling, and testing.
- Bookmark **Guide 6** and apply its sanitisation checklist from day one—prompt injection and malformed AgentCards are common attack vectors.
- Once your agent passes Inspector checks, integrate it with a host from `a2a-samples` or build your own using `a2a.client`.
- Keep the [`a2a_sdk_api_documentation.csv`](./a2a_sdk_api_documentation.csv) nearby for exact class signatures; Guide 8 (API reference) explains how to navigate it quickly.

With the fundamentals covered here, you can iterate confidently on new skills, swap LLM providers, and extend your agent without deviating from the A2A specification.
