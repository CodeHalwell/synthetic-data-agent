# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **multi-agent synthetic data generation system** built on Google Agent Development Kit (ADK). It generates high-quality synthetic training datasets for LLM post-training across 9 training paradigms: SFT, DPO, PPO, GRPO, RLHF, KTO, ORPO, Chat, and QA.

The system takes user requirements (e.g., "Generate 100 chemistry SFT examples") and autonomously executes a 5-stage pipeline: **Questions → Research → Generation → Review → Storage**.

## Development Commands

The project is managed with [uv](https://docs.astral.sh/uv/); a `Makefile` wraps the common tasks.

### Running the Application

```bash
uv sync --all-groups        # install dependencies + dev tools
uv run python main.py       # run the main demo (generates chemistry examples)
uv run adk web src          # explore agents in the ADK web UI
```

### Database Management

```bash
uv run python utils/create_database.py            # initialize tables (also happens automatically)
uv run python utils/inspect_database.py           # inspect database contents
uv run python utils/clear_database.py --confirm   # clear all data (caution: destructive)
uv run python utils/db_inspector.py               # inspect structure and contents
```

### Testing and Linting

```bash
uv run pytest               # offline unit tests (this is what CI runs)
GOOGLE_API_KEY=... uv run pytest   # also collects live agent integration tests
uv run ruff check .         # lint
uv run ruff format .        # format
uv run pre-commit install   # optional: lint on every commit
```

The offline/integration split is controlled by `tests/conftest.py`: modules listed in `_INTEGRATION_TEST_FILES` are only collected when `GOOGLE_API_KEY` is set. All tests run against a throwaway database (never `db/synthetic_data.db`).

### Environment Setup

Requires Python 3.13+ (uv installs it automatically per `.python-version`). Environment variables live in `.env` (git-ignored, loaded via python-dotenv; see `.env.example`):
- `GOOGLE_API_KEY` - Google AI API key for Gemini models (required for live runs)
- `DATABASE_URL` - optional SQLAlchemy URL overriding the default SQLite database

## Architecture

### Agent Hierarchy

```
orchestrator_agent (root coordinator)
├── planning_agent - Strategy and execution planning
├── question_agent - Domain question generation
├── research_agent - Knowledge gathering via web search
│   └── database_agent (sub-agent) - Database operations
├── generation_agent - Synthetic data creation
├── reviewer_agent - Quality validation
└── database_agent - Database operations
```

### Agent Configuration Pattern

Each agent is configured via YAML files in its respective directory:
- `src/orchestrator/*.yaml` - Root orchestrator config
- `src/orchestrator/{agent_name}/{agent_name}.yaml` - Agent-specific configs

All agents use:
- **Model**: Gemini, configured per agent YAML (mostly `gemini-2.5-flash`, some `gemini-3-pro-preview`)
- **Framework**: Google ADK (`google.adk.agents.LlmAgent`)
- **HTTP Retry**: Exponential backoff (5 attempts, base delay 7s)

Configuration is loaded via `utils/config.py:load_config()`.

Workflow code invokes agents through `src/orchestrator/runtime.py:run_agent()`, which wraps each agent in a cached ADK `InMemoryRunner` and executes one prompt per fresh session.

### Key Workflows

**Main Entry Point**: `src/orchestrator/workflows.py:generate_synthetic_data()`

5-stage pipeline:
1. **Add Questions** - Store questions in database with status="pending"
2. **Research** - Batch research via `research_agent.research_questions_batch()`
3. **Generate** - Create training data via `generation_agent.generate_{type}_data()`
4. **Review** - Validate via `reviewer_agent.review_{type}_data()`
5. **Store** - Save approved data to training type tables

Supporting workflows:
- `process_pending_questions()` - Resume processing from database
- `resume_failed_questions()` - Retry failed items
- `get_pipeline_status()` - Check stage counts

### Database Architecture

**ORM**: SQLAlchemy 2.0
**Backend**: SQLite (default, extensible)
**Location**: `db/synthetic_data.db`, overridable via the `DATABASE_URL` environment variable
**Central config**: `utils/db.py` (`get_database_url()`, `create_db_engine()`); engines auto-create missing tables
**Schemas**: `schema/synthetic_data.py`

Tables:
- `questions` - Questions with research status
- `synthetic_data_{type}` - One table per training type (sft, dpo, ppo, grpo, rlhf, kto, orpo, chat, qa)

**DatabaseTools**: `tools/database_tools.py`
Implements `BaseTool` interface for agent use. Provides:
- Question management (add, query, update)
- Training data storage by type
- Session management

### Data Flow Pattern

```
User Input → Questions (status=pending)
         ↓
Research Agent → Questions (status=researched, answer field populated)
         ↓
Generation Agent → Training data created (not yet in final table)
         ↓
Reviewer Agent → Quality score + review_status assigned
         ↓
approved → Training type table (synthetic_data_{type})
needs_revision → Can store with auto_approve=True
rejected → Logged in errors
```

### Training Type Dispatch

Each training type has dedicated functions:
- `generation_agent.workflows.generate_{type}_data()` - Generate function
- `reviewer_agent.workflows.review_{type}_data()` - Review function
- `schema/synthetic_data.py:SyntheticData{Type}` - Schema model

Quality thresholds (in reviewer):
- **≥ 0.8** - Approved (auto-stored)
- **0.6-0.8** - Needs revision (stored if auto_approve=True)
- **< 0.6** - Rejected (logged as error)

### Tool Usage Constraints

**CRITICAL**: Only use **built-in ADK tools** to maintain "AFC compatibility" (Agent Framework Compatibility).

Currently approved:
- `google_search` - Built-in web search (used by research_agent)
- `BuiltInCodeExecutor` - Code execution (used by generation/reviewer agents)
- `DatabaseTools` - Custom tool (implements BaseTool interface)

**NEVER** import or use:
- Custom web-scraping tools (the old `web_tools`/`data_tools` modules were deleted; research goes through `google_search`)
- External tool libraries that aren't part of ADK

Check git history for context on AFC compatibility fixes.

## Important Patterns

### Agent Communication

Agents communicate via:
1. **Tool calls** - Using DatabaseTools for shared state
2. **Sub-agents** - research_agent uses database_agent as sub-agent via `transfer_to_agent(agent_name="database_agent")`
3. **Workflows** - Orchestrator calls agent workflows directly

**No direct agent-to-agent messaging** - all coordination through database or orchestrator.

### Progress Tracking

`PipelineProgress` class tracks:
- Stage counts (questions_added, researched, generated, reviewed, approved, failed)
- Error details with timestamps
- Completion percentages

All workflows return:
```python
{
    "status": "success" | "partial" | "error",
    "progress": PipelineProgress.get_summary(),
    "results": [{"question_id": ..., "status": ..., "quality_score": ...}],
    "summary": {"total_questions": ..., "success_rate": ...},
    "errors": [...],
}
```

### Schema Registration

Training type schemas are registered in `SCHEMA_REGISTRY` dict:
```python
SCHEMA_REGISTRY = {
    TrainingType.SFT: SyntheticDataSFT,
    TrainingType.DPO: SyntheticDataDPO,
    # ... etc
}
```

Access via: `get_schema_for_training_type(training_type: str)`

### Pydantic Models

Agent outputs use Pydantic models in `models/models.py`:
- `PlanningResponse` - Planning agent structured output
- `Questions` - Question agent structured output

These enforce agent output schemas via ADK's structured output feature.

## Recent Changes (Context from Git)

The project was modernized in one pass (see the `claude/project-modernization-*` branch):
- Tooling: uv-managed environment, ruff lint+format, pytest (+pytest-asyncio), pre-commit, GitHub Actions CI
- google-adk upgraded to 2.x; broken `agent.invoke()` calls replaced with a proper runner (`src/orchestrator/runtime.py`)
- Pipeline fixes: stage 1 stores questions again; stage 5 filters payloads to real table columns before insert
- Database: central `utils/db.py`, `DATABASE_URL` env support, auto `create_all`, timezone-aware timestamps
- Removed dead `web_tools`/`data_tools` modules and their orphaned dependencies (requests, bs4, numpy, pandas)

When adding tools, ensure they follow ADK's `BaseTool` interface and don't break AFC compatibility.

## Testing Patterns

Tests run under pytest with `asyncio_mode = "auto"` (async test functions need no decorator) and `pythonpath = ["."]` (imports work from the repo root). Two tiers:
- **Offline unit tests** (always run, used in CI): `test_database_tools.py`, `test_schema_registry.py`, `test_utils.py`, `test_generation_review_offline.py`, `test_pipeline_stages.py`, plus older offline scripts
- **Live integration tests** (need `GOOGLE_API_KEY`, listed in `tests/conftest.py`): end-to-end pipeline and agent tests

`tests/conftest.py` points `DATABASE_URL` at a temporary database for the whole test process.

## File Organization

```
src/orchestrator/          # Agent definitions and workflows
  ├── agent.py             # Root orchestrator agent
  ├── workflows.py         # Main pipeline workflows
  ├── {agent_name}/        # Agent subdirectories
  │   ├── agent.py         # Agent definition
  │   ├── workflows.py     # Agent workflows (if applicable)
  │   └── {name}.yaml      # Agent configuration
  ├── runtime.py           # run_agent() helper (ADK InMemoryRunner wrapper)
schema/                    # SQLAlchemy schemas
tools/                     # Agent tools (DatabaseTools, etc.)
models/                    # Pydantic models for structured outputs
utils/                     # Config loading, central DB config (db.py), resilience, DB scripts
tests/                     # Offline unit tests + live integration tests (see conftest.py)
db/                        # SQLite database files (git-ignored)
```

## Key Constraints

1. **Python 3.13+** - Required for dependencies (uv installs it per `.python-version`)
2. **Google ADK framework (2.x)** - All agents inherit from `LlmAgent`
3. **Gemini models only** - Configured per agent YAML (gemini-2.5-flash / gemini-3-pro-preview)
4. **SQLite default** - Database can be swapped via `DATABASE_URL`
5. **AFC compatibility** - Only use approved tools and patterns
6. **No direct file I/O in agents** - Use DatabaseTools for persistence
7. **Async workflows** - All workflows use `async`/`await`

## Modifying Agents

When adding/modifying agents:

1. **Create/update YAML config** - Define name, model, description, instruction
2. **Implement agent.py** - Import config, initialize LlmAgent with Gemini model
3. **Add workflows.py** (if needed) - Define workflow functions
4. **Register tools** - Pass tools to LlmAgent constructor
5. **Update orchestrator** - Import and coordinate new agent
6. **Test** - Create test module in `tests/`

Follow existing patterns in `src/orchestrator/{agent_name}/` directories.

## Quality Review Logic

Each training type has custom review criteria. Example for SFT:
- **Factual accuracy** - Compare generated response with research context
- **Completeness** - Min 100 chars, comprehensive coverage
- **Clarity** - Well-structured, clear sentences
- **Format compliance** - Required fields present

Reviewer agents use code execution (`BuiltInCodeExecutor`) to verify technical content when applicable.

## Common Gotchas

1. **Database sessions** - DatabaseTools manages sessions internally; don't create external sessions
2. **Training type strings** - Use lowercase strings ("sft", "dpo") not TrainingType enum in API calls
3. **Question status flow** - Must be: pending → researched → (in generation) → (in review) → approved/rejected
4. **Auto-approve flag** - Set to True to store "needs_revision" items (useful for demos)
5. **Web search display** - Research agent must display search suggestions if provided by google_search tool
6. **AFC compatibility** - Don't add custom tools without checking ADK compatibility first
