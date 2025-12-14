# Agent Integration Guide

## Problem Identified

During test runs, agents coordinate through ADK App conversations but **don't actually execute workflow functions**. The Database Agent claims to store data but no records appear in the database.

## Root Cause

**Agents are simulating actions instead of calling tools.**

When agents use `transfer_to_agent`, they're coordinating conversations but not executing the actual workflow functions we built (`generate_synthetic_data`, `add_synthetic_data`, etc.).

## Solution: Make Workflow Functions Available as Tools

### Current Architecture

```
ADK App
  └── Orchestrator Agent
       └── Sub-agents (Planning, Question, Research, etc.)
            └── Tools (DatabaseTools, WebTools)
```

**Problem**: Agents have tools but aren't calling workflow functions.

### Recommended Architecture

```
ADK App
  └── Orchestrator Agent
       └── Tools:
            ├── generate_synthetic_data_tool (wraps workflows.generate_synthetic_data)
            ├── process_pending_questions_tool
            ├── get_pipeline_status_tool
            └── DatabaseTools, WebTools (existing)
```

## Implementation Steps

### Step 1: Create Tool Wrappers

Create `tools/workflow_tools.py`:

```python
from google.adk.tools import BaseTool
from src.orchestrator.workflows import (
    generate_synthetic_data,
    process_pending_questions,
    get_pipeline_status
)

class GenerateSyntheticDataTool(BaseTool):
    """Tool wrapper for generate_synthetic_data workflow."""
    
    def __init__(self):
        super().__init__(
            name="generate_synthetic_data",
            description="Generate synthetic training data from questions through complete pipeline"
        )
    
    async def __call__(
        self,
        questions: List[str],
        topic: str,
        sub_topic: str,
        training_type: str,
        max_questions: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the complete synthetic data generation pipeline."""
        return await generate_synthetic_data(
            questions=questions,
            topic=topic,
            sub_topic=sub_topic,
            training_type=training_type,
            max_questions=max_questions
        )
```

### Step 2: Add Tools to Orchestrator

Update `src/orchestrator/agent.py`:

```python
from tools.workflow_tools import GenerateSyntheticDataTool

# Initialize workflow tools
generate_data_tool = GenerateSyntheticDataTool()

root_agent = LlmAgent(
    # ... existing config ...
    tools=[
        database_tools,
        web_tools,
        generate_data_tool  # Add workflow tool
    ]
)
```

### Step 3: Update Agent Instructions

Update `orchestrator.yaml` to instruct the agent to use the workflow tool:

```yaml
instruction: |
  ...
  
  ## Using Workflow Tools
  
  When a user requests synthetic data generation:
  
  1. Gather requirements (domain, topic, training type, volume)
  2. Use the `generate_synthetic_data` tool with the collected parameters
  3. Report the results to the user
  
  DO NOT simulate the workflow - use the actual tool!
```

## Alternative: Direct Function Calls

If tool integration is complex, you can call workflow functions directly:

```python
from src.orchestrator.workflows import generate_synthetic_data

# In your application code
result = await generate_synthetic_data(
    questions=["What is photosynthesis?"],
    topic="biology",
    sub_topic="plant biology",
    training_type="sft"
)

print(f"Approved: {result['summary']['approved']}")
```

## Verification

After implementing, verify:

1. ✅ Agents actually call tools (check logs)
2. ✅ Data is stored in database (query after generation)
3. ✅ Workflow functions execute (add logging)
4. ✅ Error handling works (test failure scenarios)

## Testing

Test both approaches:

1. **Direct Function Call** (Already working ✅):
   ```python
   result = await generate_synthetic_data(...)
   ```

2. **Agent Tool Call** (Needs implementation):
   - Orchestrator Agent uses `generate_synthetic_data` tool
   - Verify data stored in database
   - Check tool execution logs

## Current Status

- ✅ Workflow functions work correctly
- ✅ Direct function calls work
- ❌ Agent tool integration incomplete
- ❌ Agents simulate instead of execute

## Next Steps

1. Create workflow tool wrappers
2. Add tools to Orchestrator Agent
3. Update agent instructions
4. Test agent-based workflow
5. Verify data storage
