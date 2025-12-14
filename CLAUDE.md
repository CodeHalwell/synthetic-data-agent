# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **multi-agent synthetic data generation system** built on Google Agent Development Kit (ADK). It generates high-quality synthetic training datasets for LLM post-training across 9 training paradigms: SFT, DPO, PPO, GRPO, RLHF, KTO, ORPO, Chat, and QA.

The system takes user requirements (e.g., "Generate 100 chemistry SFT examples") and autonomously executes a 5-stage pipeline: **Questions → Research → Generation → Review → Storage**.

## Development Commands

### Running the Application

```bash
# Run the main demo (generates chemistry examples)
python main.py
```

### Database Management

```bash
# Initialize database tables
python utils/create_database.py

# Inspect database contents
python utils/inspect_database.py

# Clear all data (caution: destructive)
python utils/clear_database.py

# Inspect database structure and contents
python utils/db_inspector.py
```

### Testing

```bash
# Run individual test modules
python tests/test_end_to_end.py
python tests/test_orchestrator_workflows.py
python tests/test_research_agent.py
python tests/test_generation_agent.py
python tests/test_reviewer_agent.py

# Run specific workflow test
python tests/test_workflow_direct.py
```

### Environment Setup

The project requires Python 3.13+ and uses a virtual environment in `.venv/`. Environment variables are stored in `.env` (not tracked in git).

Required environment variable:
- `GOOGLE_API_KEY` - Google AI API key for Gemini models

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
- **Model**: Gemini 3-pro-preview
- **Framework**: Google ADK (`google.adk.agents.LlmAgent`)
- **HTTP Retry**: Exponential backoff (5 attempts, base delay 7s)

Configuration is loaded via `utils/config.py:load_config()`.

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
**Location**: `db/synthetic_data.db`
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
- Custom `web_tools` module (removed in recent commits)
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
    "errors": [...]
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

Recent commits focus on **AFC compatibility**:
- Removed custom `web_tools` in favor of built-in `google_search`
- Cleaned up tool imports from orchestrator and reviewer agents
- Updated research agent instructions to emphasize `google_search` usage

When adding tools, ensure they follow ADK's `BaseTool` interface and don't break AFC compatibility.

## Testing Patterns

Tests use async/await and demonstrate:
- End-to-end pipeline execution (`test_end_to_end.py`)
- Individual agent workflows (`test_{agent}_agent.py`)
- Database operations (`test_database_updates.py`)
- Integration tests (`test_research_integration.py`)

Run tests individually, not as a suite (no pytest/unittest runner configured).

## File Organization

```
src/orchestrator/          # Agent definitions and workflows
  ├── agent.py             # Root orchestrator agent
  ├── workflows.py         # Main pipeline workflows
  ├── {agent_name}/        # Agent subdirectories
  │   ├── agent.py         # Agent definition
  │   ├── workflows.py     # Agent workflows (if applicable)
  │   └── {name}.yaml      # Agent configuration
schema/                    # SQLAlchemy schemas
tools/                     # Agent tools (DatabaseTools, etc.)
models/                    # Pydantic models for structured outputs
utils/                     # Config loading, database utilities
tests/                     # Test modules
db/                        # SQLite database files
```

## Key Constraints

1. **Python 3.13+** - Required for dependencies
2. **Google ADK framework** - All agents inherit from `LlmAgent`
3. **Gemini models only** - Currently uses gemini-3-pro-preview
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
