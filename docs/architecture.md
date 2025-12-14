# Synthetic Data Generation Agent — System Architecture

## Executive Summary

This system generates **synthetic datasets for LLM post-training** (SFT, DPO, GRPO, PPO, RLHF, KTO, ORPO, Chat, QA). A user provides a request (e.g., "generate 100 chemistry SFT examples"), and the system autonomously clarifies requirements, plans the workflow, generates questions, gathers ground truth context, produces training data, validates quality, and stores production-ready results.

The architecture is **artifact-driven** (spec → evidence → gold → candidates → review) rather than "agents chatting and hoping". Google's Agent Development Kit (ADK) handles orchestration, session/state management, and tool calling. SQLite + SQLAlchemy store both intermediate artifacts and final training rows.

---

## 1. Design Goals and Principles

### Goals
- Generate **high-quality**, **diverse**, **auditable** synthetic data for 9 post-training paradigms
- Support multiple domains: STEM, coding, humanities, professional fields
- Enable **deterministic validation** wherever possible (unit tests, parsers, numeric checks)
- Keep orchestration resumable, debuggable, and scalable
- Prioritise quality over quantity with multi-stage validation

### Non-Goals (Early Versions)
- Perfect grounding via live web search on day one
- Full dataset governance, red-teaming, or long-term PII policies
- Production-grade migrations (use `create_all` + simple schema evolution initially)

### Key Architectural Decisions
1. **Artifact-Driven Pipeline**: Structured artifacts (spec, evidence, gold) persist at each stage for auditability
2. **Agent Hierarchy**: Specialised agents with clear responsibilities, coordinated by an orchestrator
3. **Tools Over Sub-Agents**: Prefer function tools for specialist capabilities; only use sub-agents when ADK constraints require it
4. **Model Selection by Task**: Different Gemini models based on task complexity

---

## 2. System Overview

### High-Level Data Flow

```
User Request
    ↓
Orchestrator Agent (clarification & routing)
    ↓
Planning Agent (creates execution strategy)
    ↓
Question Agent (generates domain questions)
    ↓
Research Agent (gathers ground truth + synthesises context)
    ↓
Generation Agent (creates synthetic training data)
    ↓
Reviewer Agent (validates & scores)
    ↓
Database (stores final synthetic data)
```

### Pipeline as State Machine

The orchestrator drives a **deterministic pipeline** per question, not freeform conversation:

| Stage | Agent | Output | Database State |
|-------|-------|--------|----------------|
| 1. Clarify + Plan | Orchestrator → Planning | `PlanningResponse` | — |
| 2. Generate Questions | Question Agent | Questions with tags | `status: pending` |
| 3. Spec + Evidence + Gold | Research Agent | Task spec, evidence pack, reference solution | `status: researched` |
| 4. Generate Candidates | Generation Agent | Training type rows | `status: generated` |
| 5. Review + Score | Reviewer Agent | Quality scores, decisions | `status: approved/rejected` |
| 6. Bounded Repair | Repair loop (if rejected) | Revised data or discard | `status: discarded/needs_human` |

---

## 3. Agent Hierarchy

### 3.1 Orchestrator Agent (Root)

**Purpose**: Main coordinator managing the entire workflow.

**Responsibilities**:
- Receive user requests for synthetic data generation
- Ask clarifying questions to understand requirements
- Route to appropriate sub-agents
- Manage overall workflow state
- Handle errors and retries

**Model**: `gemini-3-pro-preview` (complex reasoning, strategic decisions)

**Sub-Agents**:
- Planning Agent
- Question Agent
- Research Agent
- Generation Agent
- Reviewer Agent

**Configuration**: `src/orchestrator/orchestrator.yaml`

---

### 3.2 Planning Agent

**Purpose**: Creates detailed execution strategy.

**Input**: User requirements (topic, training type, quantity, quality criteria)

**Output**: Structured `PlanningResponse`:
- `topic`: Main subject area
- `training_type`: Target paradigm (sft, dpo, grpo, etc.)
- `research_plan`: Strategy for gathering domain knowledge
- `data_structure_specification`: Required fields for training type
- `execution_plan`: Step-by-step generation strategy
- `reasoning`: Justification for the approach

**Model**: `gemini-3-pro-preview` (multi-step reasoning)

**Configuration**: `src/orchestrator/planning_agent/planning.yaml`

---

### 3.3 Question Agent

**Purpose**: Generates domain-specific questions for research and answering.

**Input**: Topic and sub-topic from planning phase

**Output**: `Questions` model with topic, sub_topic, and list of questions

**Database Interaction**:
- Writes questions to `questions` table via `DatabaseTools`
- Each question gets `status='pending'`

**Model**: `gemini-2.5-flash` (straightforward generation)

**Configuration**: `src/orchestrator/question_agent/questions.yaml`

---

### 3.4 Research Agent

**Purpose**: Gathers ground truth information and synthesises structured context.

**Two-Phase Process**:

1. **Ground Truth Collection**
   - Uses `WebTools` to search and fetch content
   - Stores raw, word-for-word text from authoritative sources
   - Tracks source URLs, titles, authors, dates
   - Identifies potential licenses (CC-BY, CC-BY-SA, public domain, etc.)

2. **Context Synthesis**
   - Uses LLM to analyse ground truth
   - Creates structured, cleaned version
   - Extracts key concepts, definitions, examples
   - Organises information for generation phase

**Database Writes**:
- `ground_truth_context`: Raw scraped text
- `synthesized_context`: LLM-structured JSON
- `context_sources`: Array of URLs with metadata
- `status`: Changes to "researched"

**Model**: `gemini-2.5-flash` (web search, extraction, synthesis)

**Tools**: `WebTools`, `DatabaseTools`

**Configuration**: `src/orchestrator/research_agent/research.yaml`

---

### 3.5 Generation Agent

**Purpose**: Creates synthetic training data using context and specialist tools.

**Input**:
- Questions from database with context
- Training type requirements from plan

**Process**:
1. Read researched questions with context
2. Determine required fields based on training type
3. Use context + tools to generate answers
4. For specialised tasks (code, maths), use code executor
5. Write completed data to appropriate training table

**Training Type Handling**:

| Type | Output Fields |
|------|---------------|
| SFT | `instruction`, `response`, `system_prompt` |
| Reasoning SFT | `instruction`, `reasoning`, `response` |
| DPO | `prompt`, `chosen`, `rejected`, ratings |
| GRPO | `prompt`, `reasoning`, `code`, `predicted_answer`, `is_correct` |
| PPO | `prompt`, `response`, `reward` |
| RLHF | Comparison pairs with ratings |
| KTO | Binary feedback (good/bad) |
| ORPO | Combined SFT + preference data |

**Model**: `gemini-3-pro-preview` (complex domains) or `gemini-2.5-flash` (simpler tasks)

**Tools**: `DatabaseTools`, `BuiltInCodeExecutor`

**Configuration**: `src/orchestrator/generation_agent/generation.yaml`

---

### 3.6 Reviewer Agent

**Purpose**: Validates generated data quality and correctness.

**Validation Methods**:
1. **Format Compliance**: Checks structure against training type spec
2. **Correctness**: Verifies against reference solution acceptance criteria
3. **Code Execution**: Tests code snippets for correctness
4. **Independent Verification**: Cross-checks claims via web search
5. **Evidence Consistency**: Ensures claims are supported by evidence

**Scoring Criteria** (0-1 scale):
- Factual accuracy
- Completeness
- Clarity
- Format compliance

**Database Updates**:
- Sets `quality_score` field
- Updates `review_status`: "approved", "rejected", "needs_revision"
- Adds `reviewer_notes` for failures

**Quality Thresholds**:
- Auto-reject: `quality_score < 0.6`
- Flag for review: `0.6 ≤ quality_score < 0.8`
- Auto-approve: `quality_score ≥ 0.8`

**Model**: `gemini-3-pro-preview` (complex validation) or `gemini-2.0-flash` (basic checks)

**Tools**: `WebTools`, `DatabaseTools`, `BuiltInCodeExecutor`

**Configuration**: `src/orchestrator/reviewer_agent/reviewer.yaml`

---

### 3.7 Database Agent

**Purpose**: Specialised agent for complex database operations.

**Capabilities**:
- Query statistics and analytics
- Batch operations
- Data export/import
- Schema validation

**Model**: `gemini-2.5-flash`

**Tools**: `DatabaseTools`

**Configuration**: `src/orchestrator/database_agent/database.yaml`

---

## 4. The Core "Missing Middle": Structured Artifacts

The pipeline treats "context" as **structured artifacts**, not just prose. This unlocks reproducibility, reviewer credibility, and deterministic correctness checks.

### Core Artifacts (Per Question)

#### 1. Task Spec
What the system is trying to generate:
- Training type (SFT/DPO/GRPO/…)
- Task type (math/coding/factual/…)
- Output constraints (format, JSON schema, "final must be an integer", etc.)
- Difficulty target
- Allowed tools and constraints

#### 2. Evidence Pack
Grounding inputs:
- List of evidence items with provenance (source, when, how)
- Each item includes content plus "why this matters"
- Can start as "model knowledge" for MVP, upgrade to retrieval later

#### 3. Reference Solution
The "gold" answer:
- `final_answer` in machine-checkable form
- `answer_type` and parsing rules
- Acceptance criteria (regex, numeric tolerance, unit tests, invariants)
- Optional derivation notes for debugging

These artifacts persist so downstream agents can be audited and reviewers can validate against something concrete.

---

## 5. Model Selection Strategy

The system uses different Gemini models based on task complexity:

### gemini-3-pro-preview (Complex Reasoning)
**Use for**:
- Extensive multi-step reasoning
- Strategic planning and decision-making
- Complex task delegation
- Sophisticated content generation

**Agents**: Orchestrator, Planning Agent, Generation Agent (complex domains), Reviewer Agent (deep validation)

### gemini-2.5-flash (Standard Operations)
**Use for**:
- Fast information retrieval
- Web search and data extraction
- Straightforward text processing
- Standard Q&A tasks

**Agents**: Research Agent, Question Agent, Database Agent, Generation Agent (simple domains)

### gemini-2.0-flash (Fast Validation)
**Use for**:
- Quick validation checks
- Format compliance verification
- Basic quality scoring
- Simple transformations

**Agents**: Reviewer Agent (basic checks), Data Export

### Selection Heuristic

```
If task requires:
  - Multi-step reasoning → gemini-3-pro-preview
  - Complex domain expertise → gemini-3-pro-preview
  - Strategic decision-making → gemini-3-pro-preview
  - Fast data retrieval → gemini-2.5-flash
  - Web search operations → gemini-2.5-flash
  - Simple validation → gemini-2.0-flash
```

---

## 6. Specialist Capabilities: Tools vs Sub-Agents

### ADK Constraints
- Only **one built-in tool** can be attached per agent
- Built-in tools generally **cannot be used inside sub-agents**
- Heavy capabilities should live in **specialist tool agents**
- Use **Agent-as-a-Tool** pattern: orchestrator remains in control, specialist returns result

### Recommended Approach: Tools First

Implement verification and grounding as function tools:

| Capability | Tool | Purpose |
|------------|------|---------|
| `PythonExecTool` | Code verification | Run snippets, numeric checks, unit tests |
| `FormatValidatorTool` | Schema validation | Regex, JSON schema checks |
| `ParserTool` | Answer extraction | Extract final answer reliably |
| `WebSearchTool` | Research | Search, fetch, extract content |
| `DatabaseTools` | Data operations | CRUD, queries, statistics |

### When to Use Sub-Agents
Only when you need built-in tools that can't be combined under one agent, or for multi-step domain reasoning:
- Math Specialist (advanced proofs, calculations)
- Chemistry Specialist (equations, reactions)
- Code Specialist (multi-step code generation)

---

## 7. Database Schema

### Questions Table
Work queue and artifact store:

```python
id: int (PK)
question: str
topic: str
sub_topic: str
status: str  # pending → researched → generated → approved
training_type: str

# Artifact fields (JSON blobs)
task_spec: JSON           # Output constraints, format requirements
evidence: JSON            # Evidence pack with provenance
reference_solution: JSON  # Gold answer + acceptance criteria
review: JSON              # Review results

# Context fields
ground_truth_context: str   # Raw text from sources
synthesized_context: str    # LLM-structured version
context_sources: JSON       # URLs, licenses, metadata
context_quality_score: float

# Timestamps
created_at: datetime
updated_at: datetime
research_completed_at: datetime
```

### Training Type Tables
Each paradigm has its own table (see `schema/synthetic_data.py`):

- `synthetic_data_sft`: Instruction-response pairs
- `synthetic_data_dpo`: Preference pairs (chosen/rejected)
- `synthetic_data_ppo`: Prompts with reward signals
- `synthetic_data_grpo`: Group-based reasoning with verification
- `synthetic_data_rlhf`: Reward model training comparisons
- `synthetic_data_kto`: Binary feedback data
- `synthetic_data_orpo`: Combined SFT + preference
- `synthetic_data_chat`: Multi-turn conversations
- `synthetic_data_qa`: Question-answer pairs with reasoning

---

## 8. Quality & Safety

### Avoiding Synthetic Data Failure Modes

#### Failure Mode 1: Circularity
If the same model generates questions, fabricates context, answers, and reviews itself, you get "convincing nonsense".

**Mitigation**:
- Evidence pack should come from retrieval/tooling
- Reference solution must include acceptance rules
- Reviewer must run deterministic checks and/or independent retrieval

#### Failure Mode 2: Reward Hacking
Especially in GRPO/RL setups, models learn to **look correct** instead of **being correct**.

**Mitigation**:
- Rewards tied to checkers: correct parse, unit tests, numeric equivalence, invariants
- Deterministic validation wherever possible

### Content Safety
- Model safety settings configured in agent definitions
- Reviewer validates generated content
- Human-in-the-loop for sensitive topics

---

## 9. External Data Sources (MCP Servers)

### Priority 1: Essential
1. **arXiv MCP Server**: Primary academic source
2. **Wikipedia MCP Server**: General knowledge
3. **HuggingFace MCP Server**: Dataset integration
4. **GitHub MCP Server**: Code examples
5. **Semantic Scholar MCP**: Citation tracking

### Priority 2: Domain-Specific
6. **bioRxiv/medRxiv MCP**: Life sciences
7. **chemRxiv MCP**: Chemistry
8. **PubMed Central MCP**: Biomedical literature
9. **Stack Overflow MCP**: Programming Q&A

### License Compliance
All source material must track license information:
- CC0 (Public Domain): Maximum freedom
- CC-BY 4.0: Attribution only
- CC-BY-SA 4.0: Attribution + share-alike
- MIT / Apache-2.0: For code
- CC-BY-NC: Non-commercial (use cautiously)

---

## 10. Technology Stack

### Framework
- **Google ADK**: Core agent orchestration, session management, tool calling
- **Gemini Models**: Strategic selection based on task complexity

### Database
- **SQLAlchemy ORM**: Database abstraction
- **SQLite** (dev) / **PostgreSQL** (production)

### Tools & Libraries
- **requests + BeautifulSoup4**: Web scraping
- **Pydantic**: Data validation and structured outputs
- **PyYAML**: Configuration file parsing
- **Code Executors**: BuiltIn (simple), AgentEngine (sandboxed), GKE (production)
- **HuggingFace Hub**: Dataset repository for augmentation and hosting

---

## 11. Error Handling & Retry Logic

### Retry Configuration

```python
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)
```

### Error Recovery Strategies

| Stage | Failure | Action |
|-------|---------|--------|
| Question Generation | Error | Skip question, log error |
| Research | Error | Mark as "skipped", continue |
| Generation | Error | Flag for manual review |
| Review | Error | Default to "needs_review" status |
| Database | Error | Rollback transaction, retry with backoff |

---

## 12. Architecture Diagrams

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│  - User interaction                                          │
│  - Workflow coordination                                     │
│  - Error handling                                            │
└────┬────────────────────────────────────────────────────────┘
     │
     ├── Planning Agent
     │   └── Creates execution strategy
     │
     ├── Question Agent
     │   └── Generates domain questions
     │
     ├── Research Agent
     │   ├── WebTools (search, fetch)
     │   └── Synthesises context
     │
     ├── Generation Agent
     │   ├── BuiltInCodeExecutor
     │   ├── Custom Function Tools
     │   └── Optional: Specialist Sub-Agents
     │       ├── Math Specialist
     │       ├── Chemistry Specialist
     │       └── Code Specialist
     │
     ├── Reviewer Agent
     │   ├── WebTools (verification)
     │   ├── CodeExecutor (testing)
     │   └── Scores & validates
     │
     └── Database Agent
         └── Analytics & management
```

### Data Flow Diagram

```
User Input
    ↓
[Planning] → PlanningResponse
    ↓
[Question Generation] → Questions DB (status: pending)
    ↓
[Research] → Questions DB (+ artifacts, status: researched)
    ↓
[Generation] → Training Type DB (status: pending_review)
    ↓
[Review] → Training Type DB (+ quality_score, status: approved)
    ↓
Final Dataset (export to JSONL, HuggingFace, etc.)
```

---

## 13. ADK Implementation Notes

### Sessions, State, Events
- A Session is an event stream plus state
- State supports prefixes: `temp:` (per invocation), `user:` (across sessions), `app:` (global)
- Events capture state/artifact deltas; session service persists via `append_event`
- Use state for orchestration variables (current run id, question ids)
- Use DB for durable pipeline artifacts and datasets

### Memory
ADK memory services can store:
- Topic packs (common rules, definitions, rubrics)
- House style constraints
- Recurring error patterns + fixes

### Callbacks/Plugins
Use for:
- Logging and telemetry
- Enforcing "must cite evidence item IDs"
- Auto-saving intermediate artifacts to DB
- Auto-retry policies on validation failures

---

## 14. Extensibility Points

### Adding New Training Types
1. Define schema in `schema/synthetic_data.py`
2. Add to `TrainingType` enum
3. Register in `SCHEMA_REGISTRY`
4. Update Generation Agent logic

### Adding New Specialist Agents
1. Create agent directory under `src/orchestrator/`
2. Define YAML configuration
3. Implement agent.py with tools
4. Register as sub-agent or Agent-as-a-Tool

### Adding New Tools
1. Create tool class in `tools/` directory
2. Implement tool methods as functions
3. Add to relevant agent's tools list

### Custom Data Sources
1. Create tool for data source (e.g., `arxiv_tools.py`)
2. Add to Research Agent tools
3. Update context collection logic

---

## 15. Reference Links

```
ADK docs home:
https://google.github.io/adk-docs/

Built-in tools + limitations:
https://google.github.io/adk-docs/tools/built-in-tools/

Tools overview (Function tools, MCP tools, OpenAPI):
https://google.github.io/adk-docs/tools/

Function tools + Agent-as-a-Tool (AgentTool):
https://google.github.io/adk-docs/tools-custom/function-tools/

Sessions/state:
https://google.github.io/adk-docs/sessions/state/

Sessions/memory:
https://google.github.io/adk-docs/sessions/memory/

Events:
https://google.github.io/adk-docs/events/

Runtime (Runner loop):
https://google.github.io/adk-docs/runtime/

Callbacks:
https://google.github.io/adk-docs/callbacks/

MCP tools:
https://google.github.io/adk-docs/tools-custom/mcp-tools/

ADK Python GitHub:
https://github.com/google/adk-python
```

---

## Summary

This architecture provides a flexible, extensible system for generating high-quality synthetic training data across multiple LLM post-training paradigms. The modular agent design with structured artifacts allows for easy customisation and scaling, while deterministic validation ensures quality.

The system prioritises:
- **Quality**: Multi-stage validation with deterministic checks
- **Flexibility**: Support for 9+ training types
- **Auditability**: Persistent artifacts at each pipeline stage
- **Extensibility**: Easy to add new domains, tools, agents
- **Reliability**: Error handling, retry logic, bounded repair loops
