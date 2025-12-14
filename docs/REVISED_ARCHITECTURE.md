# Revised Architecture: Multi-Agent Database Sub-Agents

**Date**: December 14, 2025  
**Status**: Design Phase  
**Based on**: User requirements for better separation of concerns

---

## Architecture Overview

### New Agent Structure

Each agent now has its own dedicated database sub-agent for writing data, while a central database manager agent handles schema initialization and data review.

```
Orchestrator Agent
├── Question Agent
│   └── Question Database Sub-Agent (writes questions)
├── Research Agent
│   ├── google_search (built-in tool)
│   └── Research Database Sub-Agent (writes research context)
├── Generation Agent
│   ├── DatabaseTools (custom tool - reads only)
│   ├── Code Execution Sub-Agent (if needed)
│   └── Generation Database Sub-Agent (writes generated data)
├── Reviewer Agent
│   ├── DatabaseTools (custom tool - reads only)
│   └── Review Database Sub-Agent (writes review results)
└── Database Manager Agent
    ├── Schema initialization
    ├── Database review/validation
    └── DatabaseTools (custom tool - full access)
```

---

## Key Architectural Changes

### 1. Database Sub-Agents for Each Agent

**Purpose**: Each agent has a dedicated sub-agent that handles database writes for that specific stage.

**Benefits**:
- Clear separation of concerns
- Each agent can write to database as it progresses
- No need to pass data through orchestrator
- Better error isolation

**Implementation**:
- Create lightweight database sub-agents (one per agent)
- Each sub-agent uses `DatabaseTools` as a tool
- Sub-agents are specialized for their agent's data type

### 2. Database Manager Agent

**Purpose**: Centralized database management and oversight.

**Responsibilities**:
1. **Schema Initialization**: Set up correct database schema for the task
2. **Database Review**: Validate data quality, check for duplicates, ensure integrity
3. **Database Health**: Monitor database state, optimize queries
4. **Migration Management**: Handle schema changes

**Not Used For**: Day-to-day CRUD operations (those go to sub-agents)

### 3. Clear Pipeline Stages with Database Writes

**New Pipeline Flow**:

```
Stage 1: Question Generation
├── Question Agent generates questions
├── Question Database Sub-Agent writes to questions table
└── Status: "pending" → "questions_added"

Stage 2: Research
├── Research Agent researches each question (using google_search)
├── Research Database Sub-Agent updates questions with:
│   ├── ground_truth_context
│   ├── synthesized_context
│   ├── sources
│   └── research metadata
└── Status: "questions_added" → "researched"

Stage 3: Generation
├── Generation Agent generates training data
├── Generation Database Sub-Agent writes to:
│   ├── Intermediate storage (before review)
│   └── Links to question_id
└── Status: "researched" → "generated"

Stage 4: Review
├── Reviewer Agent reviews generated data
├── Review Database Sub-Agent updates with:
│   ├── quality_score
│   ├── review_status
│   └── reviewer_notes
└── Status: "generated" → "reviewed"

Stage 5: Final Storage
├── Database Manager Agent:
│   ├── Validates approved data
│   ├── Moves to final training type tables
│   └── Cleans up intermediate data
└── Status: "reviewed" → "approved" (in final table)
```

---

## Agent Specifications

### Question Agent

**Tools**: None (pure generation)  
**Sub-Agents**: `question_db_sub_agent`

**Database Sub-Agent**:
- Writes: Questions to `questions` table
- Updates: Question status to "pending"
- Reads: None (orchestrator provides questions)

**Workflow**:
1. Generate questions based on topic/sub_topic
2. Transfer to `question_db_sub_agent` to store
3. Return question IDs

### Research Agent

**Tools**: `google_search` (ADK built-in)  
**Sub-Agents**: `research_db_sub_agent`

**Database Sub-Agent**:
- Reads: Pending questions from `questions` table
- Writes: Research context to `questions` table
- Updates: Question status to "researched"

**Workflow**:
1. Get pending questions (via sub-agent or orchestrator)
2. For each question:
   - Use `google_search` to find authoritative sources
   - Extract snippets from search results
   - Synthesize context from snippets
   - Transfer to `research_db_sub_agent` to update question
3. Return research results

**Research Implementation**:
```python
async def research_question(question, topic, sub_topic, research_agent):
    # Invoke research agent with google_search
    search_query = f"{question} {topic} {sub_topic}"
    
    # Agent uses google_search tool internally
    result = await research_agent.invoke({
        "question": question,
        "topic": topic,
        "sub_topic": sub_topic,
        "action": "research",
        "search_query": search_query
    })
    
    # Extract search results from agent response
    # Agent returns structured research data
    return {
        "ground_truth_context": result["ground_truth"],
        "synthesized_context": result["synthesized"],
        "sources": result["sources"]
    }
```

### Generation Agent

**Tools**: `DatabaseTools` (custom tool - read-only access)  
**Sub-Agents**: 
- `generation_db_sub_agent` (writes generated data)
- `code_execution_agent` (if code execution needed)

**Database Sub-Agent**:
- Reads: Researched questions (via DatabaseTools)
- Writes: Generated training data to intermediate storage
- Updates: Question status to "generated"

**Workflow**:
1. Read researched questions (via DatabaseTools)
2. Generate training data for each question
3. Transfer to `generation_db_sub_agent` to store
4. Return generation results

### Reviewer Agent

**Tools**: `DatabaseTools` (custom tool - read-only access)  
**Sub-Agents**: `review_db_sub_agent`

**Database Sub-Agent**:
- Reads: Generated data (via DatabaseTools)
- Writes: Review results (quality_score, review_status)
- Updates: Data status to "reviewed"

**Workflow**:
1. Read generated data (via DatabaseTools)
2. Review quality for each item
3. Transfer to `review_db_sub_agent` to store review results
4. Return review results

### Database Manager Agent

**Tools**: `DatabaseTools` (full access)  
**Sub-Agents**: None

**Responsibilities**:
1. **Schema Initialization**:
   - Create/verify database schema
   - Set up indexes
   - Initialize tables for training type

2. **Data Review**:
   - Validate approved data before final storage
   - Check for duplicates
   - Ensure data integrity
   - Move from intermediate to final tables

3. **Database Health**:
   - Monitor query performance
   - Optimize indexes
   - Clean up old data

---

## Database Sub-Agent Pattern

### Generic Database Sub-Agent Structure

Each database sub-agent follows this pattern:

```python
# src/orchestrator/{agent_name}_db_sub_agent/agent.py
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from tools.database_tools import DatabaseTools

database_tools = DatabaseTools()

root_agent = LlmAgent(
    name=f"{agent_name}_db_sub_agent",
    description=f"Database operations for {agent_name}",
    instruction=f"""
    You are the database sub-agent for {agent_name}.
    Your role is to write {agent_name} data to the database.
    
    Available operations:
    - {specific_write_operations}
    
    Always validate data before writing.
    Return success/error status for each operation.
    """,
    model=Gemini(model="gemini-2.5-flash", retry_config=retry_config()),
    tools=[database_tools]
)
```

### Specific Sub-Agent Implementations

#### Question Database Sub-Agent
- **Writes**: Questions to `questions` table
- **Operations**: `add_questions_to_database()`

#### Research Database Sub-Agent
- **Writes**: Research context to `questions` table
- **Operations**: `update_question_context()`, `update_question_status()`

#### Generation Database Sub-Agent
- **Writes**: Generated data to intermediate storage
- **Operations**: `add_synthetic_data()` (intermediate table)

#### Review Database Sub-Agent
- **Writes**: Review results to data records
- **Operations**: `update_review_status()`, `update_quality_score()`

---

## Tool Usage Compliance

### Fixed Tool Violations

**Before**:
- Generation agent: `tools=[database_tools]` + `code_executor=code_executor` ❌
- Research agent: `sub_agents=[database_agent]` (LLM for CRUD) ❌

**After**:
- Generation agent: 
  - `tools=[database_tools]` (read-only)
  - `sub_agents=[generation_db_sub_agent, code_execution_agent]` ✅
- Research agent:
  - `tools=[google_search]` (built-in)
  - `sub_agents=[research_db_sub_agent]` ✅

### Tool Usage Rules

1. **One Built-In Tool Per Agent**: ✅
   - Research agent: `google_search` only
   - Other agents: No built-in tools (use sub-agents)

2. **Custom Tools + Sub-Agents**: ✅
   - Generation/Reviewer: `DatabaseTools` (custom) + sub-agents
   - This is allowed by ADK

3. **Sub-Agents as Tools**: ✅
   - Database sub-agents act as "tools" for writing
   - Code execution agent acts as "tool" for code

---

## Pipeline Implementation

### Stage-by-Stage Processing

```python
async def generate_synthetic_data_pipeline(
    questions: List[str],
    topic: str,
    sub_topic: str,
    training_type: str
):
    # Stage 1: Generate and store questions
    question_ids = await stage_1_generate_questions(
        questions, topic, sub_topic, training_type
    )
    
    # Stage 2: Research all questions (parallel)
    await stage_2_research_questions(question_ids, topic, sub_topic)
    
    # Stage 3: Generate all training data (parallel)
    await stage_3_generate_data(question_ids, training_type)
    
    # Stage 4: Review all data (parallel)
    await stage_4_review_data(question_ids, training_type)
    
    # Stage 5: Final storage (database manager)
    await stage_5_final_storage(question_ids, training_type)
```

### Stage 1: Question Generation

```python
async def stage_1_generate_questions(questions, topic, sub_topic, training_type):
    """Generate questions and store in database."""
    question_agent = get_question_agent()
    question_db_agent = get_question_db_sub_agent()
    
    # Generate questions (if needed, or use provided)
    if not questions:
        questions = await question_agent.invoke({
            "topic": topic,
            "sub_topic": sub_topic,
            "training_type": training_type,
            "action": "generate_questions"
        })
    
    # Store via sub-agent
    result = await question_db_agent.invoke({
        "action": "add_questions",
        "questions": questions,
        "topic": topic,
        "sub_topic": sub_topic,
        "training_type": training_type
    })
    
    return result["question_ids"]
```

### Stage 2: Research

```python
async def stage_2_research_questions(question_ids, topic, sub_topic):
    """Research all questions in parallel."""
    research_agent = get_research_agent()
    research_db_agent = get_research_db_sub_agent()
    
    # Parallel research
    research_tasks = []
    for question_id in question_ids:
        task = research_and_store(
            question_id, topic, sub_topic, 
            research_agent, research_db_agent
        )
        research_tasks.append(task)
    
    await asyncio.gather(*research_tasks, return_exceptions=True)

async def research_and_store(question_id, topic, sub_topic, 
                             research_agent, research_db_agent):
    """Research single question and store results."""
    # Get question
    question_data = database_tools.get_question_by_id(question_id)
    
    # Research via agent (uses google_search)
    research_result = await research_agent.invoke({
        "question": question_data["question"],
        "topic": topic,
        "sub_topic": sub_topic,
        "action": "research"
    })
    
    # Store via sub-agent
    await research_db_agent.invoke({
        "action": "update_research",
        "question_id": question_id,
        "ground_truth_context": research_result["ground_truth"],
        "synthesized_context": research_result["synthesized"],
        "sources": research_result["sources"]
    })
```

### Stage 3: Generation

```python
async def stage_3_generate_data(question_ids, training_type):
    """Generate training data for all questions."""
    generation_agent = get_generation_agent()
    generation_db_agent = get_generation_db_sub_agent()
    
    # Get researched questions
    researched_questions = database_tools.get_questions_by_stage("researched")
    
    # Parallel generation
    generation_tasks = []
    for question_data in researched_questions:
        task = generate_and_store(
            question_data, training_type,
            generation_agent, generation_db_agent
        )
        generation_tasks.append(task)
    
    await asyncio.gather(*generation_tasks, return_exceptions=True)
```

### Stage 4: Review

```python
async def stage_4_review_data(question_ids, training_type):
    """Review all generated data."""
    reviewer_agent = get_reviewer_agent()
    review_db_agent = get_review_db_sub_agent()
    
    # Get generated data
    generated_data = database_tools.get_generated_data_by_stage("generated")
    
    # Parallel review
    review_tasks = []
    for data in generated_data:
        task = review_and_store(
            data, training_type,
            reviewer_agent, review_db_agent
        )
        review_tasks.append(task)
    
    await asyncio.gather(*review_tasks, return_exceptions=True)
```

### Stage 5: Final Storage

```python
async def stage_5_final_storage(question_ids, training_type):
    """Move approved data to final tables."""
    db_manager_agent = get_database_manager_agent()
    
    # Get approved data
    approved_data = database_tools.get_approved_data()
    
    # Validate and move to final tables
    await db_manager_agent.invoke({
        "action": "finalize_storage",
        "training_type": training_type,
        "data": approved_data
    })
```

---

## Benefits of This Architecture

1. **Clear Separation of Concerns**: Each agent handles its own database writes
2. **Better Error Isolation**: Failures in one stage don't affect others
3. **Parallel Processing**: Each stage can process items in parallel
4. **Tool Compliance**: No ADK tool violations
5. **Incremental Progress**: Data saved at each stage (no data loss)
6. **Easier Debugging**: Can inspect database at any stage
7. **Resumability**: Can resume from any stage if pipeline fails

---

## Migration Path

### Step 1: Create Database Sub-Agents
1. Create `question_db_sub_agent/` directory
2. Create `research_db_sub_agent/` directory
3. Create `generation_db_sub_agent/` directory
4. Create `review_db_sub_agent/` directory
5. Implement each sub-agent with DatabaseTools

### Step 2: Refactor Database Manager Agent
1. Update `database_agent` to focus on management
2. Add schema initialization logic
3. Add database review/validation logic

### Step 3: Update Main Agents
1. Remove direct DatabaseTools usage (except read-only)
2. Add database sub-agents as sub_agents
3. Update workflows to use sub-agents for writes

### Step 4: Update Pipeline Workflows
1. Refactor to stage-by-stage processing
2. Add parallelization with asyncio.gather
3. Add database writes at each stage

### Step 5: Implement Real Research
1. Use ADK's google_search directly
2. Extract snippets from search results
3. Synthesize context from real sources

---

## Next Steps

1. **Review this architecture** with team
2. **Start with database sub-agents** (foundation)
3. **Implement real research** (critical blocker)
4. **Refactor pipeline** to stage-by-stage
5. **Add parallelization** for performance

---

**Document Status**: Design Complete  
**Ready for Implementation**: Yes  
**Estimated Implementation Time**: 2-3 weeks
