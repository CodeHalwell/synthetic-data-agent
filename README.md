# Synthetic Data Agent

[![CI](https://github.com/CodeHalwell/synthetic-data-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/CodeHalwell/synthetic-data-agent/actions/workflows/ci.yml)
![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)

A multi-agent system for generating high-quality synthetic training datasets for LLM post-training, built on the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) and Gemini models.

Give it a set of questions (e.g. *"Generate 100 chemistry SFT examples"*) and it runs a five-stage pipeline — **Questions → Research → Generation → Review → Storage** — producing reviewed, quality-scored training examples in a local database.

## Supported training paradigms

| Type | Description |
|------|-------------|
| SFT | Instruction–response pairs for supervised fine-tuning |
| DPO | Chosen/rejected preference pairs |
| PPO | Prompt + response + reward signal |
| GRPO | Grouped responses with relative rewards (reasoning/math/code) |
| RLHF | Comparison data for reward-model training |
| KTO | Binary good/bad feedback |
| ORPO | Combined SFT + preference alignment |
| Chat | Multi-turn conversations |
| QA | Question–answer pairs with reasoning |

Each type has its own generation function, review criteria, and database table (`synthetic_data_{type}`).

## Architecture

```
orchestrator_agent (root coordinator)
├── planning_agent      – strategy and execution planning
├── question_agent      – domain question generation
├── research_agent      – knowledge gathering via google_search
│   └── research_db_sub_agent
├── generation_agent    – synthetic data creation
├── reviewer_agent      – quality validation (score ≥ 0.8 → approved)
└── database_agent      – database operations
```

Agents are ADK `LlmAgent`s configured via YAML files in `src/orchestrator/`. The pipeline itself lives in `src/orchestrator/workflows.py`; agents coordinate through a shared SQLite database (via `DatabaseTools`) rather than direct messaging.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) (it will fetch Python 3.13 automatically).

```bash
git clone https://github.com/CodeHalwell/synthetic-data-agent.git
cd synthetic-data-agent

# Install dependencies (add --all-groups for dev tools)
uv sync

# Configure your API key (from https://aistudio.google.com/apikey)
cp .env.example .env   # then edit .env and set GOOGLE_API_KEY

# Run the demo pipeline (chemistry SFT examples)
uv run python main.py
```

You can also explore the agents interactively with the ADK web UI:

```bash
uv run adk web src
```

## Database

- SQLite by default at `db/synthetic_data.db`; tables are created automatically on first use.
- Point `DATABASE_URL` at any SQLAlchemy-compatible URL to use a different database.
- Utilities:

```bash
uv run python utils/inspect_database.py            # print table contents
uv run python utils/inspect_database.py --summary  # counts only
uv run python utils/clear_database.py --confirm    # wipe all data (destructive)
```

## Development

```bash
uv sync --all-groups          # install dev tools (ruff, pytest, pre-commit)
uv run pre-commit install     # optional: run lint hooks on every commit

make lint                     # ruff check + format check
make fix                      # auto-fix lint issues and reformat
make test                     # run the test suite
```

Tests run offline against a throwaway database by default. Integration tests that drive live Gemini agents are only collected when `GOOGLE_API_KEY` is set in the environment:

```bash
uv run pytest                 # offline unit tests (what CI runs)
GOOGLE_API_KEY=... uv run pytest   # includes live integration tests
```

## Project layout

```
src/orchestrator/     # agent definitions (YAML + agent.py) and pipeline workflows
schema/               # SQLAlchemy models: questions + one table per training type
tools/                # DatabaseTools (ADK BaseTool for agent database access)
models/               # Pydantic models for structured agent outputs
utils/                # config loading, central DB config, resilience, DB scripts
tests/                # offline unit tests + live integration tests
docs/                 # design notes and implementation history
```
