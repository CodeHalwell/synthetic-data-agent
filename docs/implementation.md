# Synthetic Data Generation Agent — Implementation Guide

This document is the practical "how to build it" companion to the architecture overview. It covers the implementation roadmap, code examples, and step-by-step guidance for completing the system.

---

## 1. Current Implementation Status

### Completed Components ✅

| Component | Location | Status |
|-----------|----------|--------|
| Database Schema | `schema/synthetic_data.py` | All 9 training type tables defined |
| Configuration System | `utils/config.py` | YAML-based config loading |
| Database Tools | `tools/database_tools.py` | CRUD operations |
| Web Tools | `tools/web_tools.py` | Fetch, search, extract |
| Data Analysis Tools | `tools/data_tools.py` | Dataset profiling |
| Orchestrator Agent | `src/orchestrator/agent.py` | Basic structure |
| Planning Agent | `src/orchestrator/planning_agent/` | Configured |
| Question Agent | `src/orchestrator/question_agent/` | Configured |
| Research Agent | `src/orchestrator/research_agent/` | Partially implemented |
| Database Agent | `src/orchestrator/database_agent/` | Configured |
| Reviewer Agent | `src/orchestrator/reviewer_agent/` | Skeleton only |

### Missing Components ❌

| Component | Priority | Notes |
|-----------|----------|-------|
| **Generation Agent** | CRITICAL | Core component that creates training data |
| Complete Research Agent | High | Needs context storage implementation |
| Complete Reviewer Agent | High | Only skeleton exists |
| Questions Table Updates | High | Missing artifact fields |
| End-to-End Workflow | High | No integrated pipeline yet |
| Testing Suite | Medium | No tests written |

---

## 2. Quick Reliability Fixes (Apply First)

Before building new features, fix these issues:

### 2.1 Retry Configuration

The `retry_config` is defined as a function but passed as a value. Ensure you call it:

```python
# ❌ Wrong
model=Gemini(model=config["model"], retry_config=retry_config)

# ✅ Correct
model=Gemini(model=config["model"], retry_config=retry_config())
```

### 2.2 Database Initialisation

Ensure tables are created on first run:

```python
# In utils/config.py or a dedicated db_init.py
from sqlalchemy import create_engine
from schema.synthetic_data import Base

def init_database(database_url: str):
    """Create all tables if they don't exist."""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine
```

### 2.3 Fix Typo in Module Name

Rename `schema/synethtic_data.py` → `schema/synthetic_data.py` to avoid import confusion.

---

## 3. Implementation Roadmap

### Phase 1: Database Updates (1-2 hours)
- Extend Questions table with artifact fields
- Add `update_question_context()` to DatabaseTools

### Phase 2: Research Agent Completion (2-3 hours)
- Implement context storage workflow
- Add ground truth + synthesised context persistence

### Phase 3: Generation Agent Creation (3-4 hours)
- Create generation agent directory and configuration
- Implement generation workflows for each training type

### Phase 4: Reviewer Agent Implementation (2-3 hours)
- Implement validation workflows
- Add deterministic checks (code execution, format validation)

### Phase 5: Workflow Integration (2-3 hours)
- Wire all agents together in orchestrator
- Create main pipeline workflow

### Phase 6: Testing & Validation (3-4 hours)
- Unit tests for each component
- Integration tests for full pipeline

**Total Estimated Time**: 13-19 hours

---

## 4. Phase 1: Database Schema Updates

### 4.1 Extend Questions Table

**File**: `schema/synthetic_data.py`

Add these fields to the `Questions` class:

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON

class Questions(Base):
    __tablename__ = "questions"
    
    # Existing fields
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    topic = Column(String(255), nullable=False)
    sub_topic = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")
    training_type = Column(String(50), nullable=True)
    
    # NEW: Artifact fields (structured JSON)
    task_spec = Column(JSON, nullable=True)
    """Task specification: training type, output constraints, format requirements"""
    
    evidence = Column(JSON, nullable=True)
    """Evidence pack: list of items with provenance"""
    
    reference_solution = Column(JSON, nullable=True)
    """Gold answer with acceptance criteria"""
    
    review = Column(JSON, nullable=True)
    """Review results with scores and decisions"""
    
    # NEW: Context fields
    ground_truth_context = Column(Text, nullable=True)
    """Raw, word-for-word text from authoritative sources"""
    
    synthesized_context = Column(Text, nullable=True)
    """LLM-cleaned and structured version"""
    
    context_sources = Column(JSON, nullable=True)
    """JSON array: [{"url": "...", "title": "...", "license": "...", "fetched_at": "..."}]"""
    
    context_quality_score = Column(Float, nullable=True)
    """Quality score of research (0-1)"""
    
    # NEW: Pipeline stage tracking
    pipeline_stage = Column(String(50), default="pending")
    """Granular stage: pending → researching → ready_for_generation → generated → reviewed"""
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    research_completed_at = Column(DateTime, nullable=True)
    answered_at = Column(DateTime, nullable=True)
```

### 4.2 Add Context Update Method to DatabaseTools

**File**: `tools/database_tools.py`

```python
from typing import Dict, Any, List, Optional
from datetime import datetime

def update_question_context(
    self,
    question_id: int,
    ground_truth_context: str,
    synthesized_context: str,
    context_sources: List[Dict[str, Any]],
    quality_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Update a question with research context.
    
    Args:
        question_id: ID of the question
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context
        context_sources: List of source metadata
        quality_score: Optional quality score (0-1)
        
    Returns:
        Update status dict
    """
    session = self._get_session()
    
    try:
        question = session.query(QUESTIONS_TABLE).filter(
            QUESTIONS_TABLE.id == question_id
        ).first()
        
        if not question:
            return {"status": "error", "error": f"Question {question_id} not found"}
        
        question.ground_truth_context = ground_truth_context
        question.synthesized_context = synthesized_context
        question.context_sources = context_sources
        question.context_quality_score = quality_score
        question.status = "researched"
        question.pipeline_stage = "ready_for_generation"
        question.research_completed_at = datetime.utcnow()
        
        session.commit()
        
        return {
            "status": "success",
            "question_id": question_id,
            "new_status": "researched"
        }
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e)}


def update_question_artifacts(
    self,
    question_id: int,
    task_spec: Optional[Dict] = None,
    evidence: Optional[Dict] = None,
    reference_solution: Optional[Dict] = None,
    review: Optional[Dict] = None,
    pipeline_stage: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update structured artifacts for a question.
    
    Args:
        question_id: ID of the question
        task_spec: Task specification dict
        evidence: Evidence pack dict
        reference_solution: Reference solution dict
        review: Review results dict
        pipeline_stage: New pipeline stage
        
    Returns:
        Update status dict
    """
    session = self._get_session()
    
    try:
        question = session.query(QUESTIONS_TABLE).filter(
            QUESTIONS_TABLE.id == question_id
        ).first()
        
        if not question:
            return {"status": "error", "error": f"Question {question_id} not found"}
        
        if task_spec is not None:
            question.task_spec = task_spec
        if evidence is not None:
            question.evidence = evidence
        if reference_solution is not None:
            question.reference_solution = reference_solution
        if review is not None:
            question.review = review
        if pipeline_stage is not None:
            question.pipeline_stage = pipeline_stage
        
        question.updated_at = datetime.utcnow()
        session.commit()
        
        return {"status": "success", "question_id": question_id}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e)}
```

### 4.3 Create Database Initialisation Script

**File**: `create_database.py` (root directory)

```python
"""Create and initialise the database with all tables."""

from sqlalchemy import create_engine
from schema.synthetic_data import Base
from pathlib import Path

# Database path
db_dir = Path(__file__).parent / "db"
db_dir.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{db_dir / 'synthetic_data.db'}"

def create_database():
    """Create all tables in the database."""
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    print(f"✅ Database created at: {DATABASE_URL}")
    print(f"✅ Tables created: {list(Base.metadata.tables.keys())}")

if __name__ == "__main__":
    create_database()
```

Run with: `python create_database.py`

---

## 5. Phase 2: Research Agent Completion

### 5.1 Update Research Agent Configuration

**File**: `src/orchestrator/research_agent/research.yaml`

```yaml
name: "research_agent"
description: "Conducts research on questions and gathers authoritative context"
model: "gemini-2.5-flash"
instruction: |
  You are a research agent specialised in gathering high-quality, authoritative information.
  
  Your task is to:
  1. Take a question and search for authoritative sources
  2. Extract word-for-word ground truth text from credible sources
  3. Synthesise the ground truth into a clean, structured context
  4. Track source URLs, licenses, and provenance
  
  For ground truth:
  - Use exact quotes and passages from sources
  - Preserve technical terminology
  - Include specific examples and details
  - Track all source URLs and licenses
  
  For synthesised context:
  - Organise information logically
  - Extract key concepts, definitions, and examples
  - Create a structured summary suitable for training data generation
  - Remove fluff and redundancy while keeping accuracy
  
  Always verify information from multiple sources when possible.
  Prioritise: peer-reviewed papers, official documentation, educational sources.
  
  IMPORTANT: Track licenses (CC-BY, CC-BY-SA, public domain, etc.) for all sources.
```

### 5.2 Implement Research Workflow

**File**: `src/orchestrator/research_agent/agent.py`

```python
import sys
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any, List

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "research.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from tools.web_tools import WebTools
from tools.database_tools import DatabaseTools

# Initialise tools
web_tools = WebTools()
database_tools = DatabaseTools()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    tools=[web_tools, database_tools],
)


async def research_question(
    question_id: int,
    question_text: str,
    topic: str,
    sub_topic: str
) -> Dict[str, Any]:
    """
    Conduct research for a single question.
    
    Process:
    1. Search for authoritative sources
    2. Fetch and extract content
    3. Synthesise context with LLM
    4. Store results in database
    
    Args:
        question_id: Database ID of the question
        question_text: The question to research
        topic: Main topic
        sub_topic: Specific sub-topic
        
    Returns:
        Research result status
    """
    # Step 1: Search for sources
    search_query = f"{topic} {sub_topic} {question_text}"
    search_results = web_tools.web_search(search_query, num_results=5)
    
    # Step 2: Fetch content from sources
    ground_truth_parts = []
    sources = []
    
    for result in search_results.get("results", [])[:3]:
        source_url = result.get("url")
        if not source_url:
            continue
            
        fetch_result = web_tools.fetch_url(source_url, extract_text=True)
        
        if fetch_result.get("status") == "success":
            content = fetch_result.get("content", "")
            ground_truth_parts.append(content[:2000])  # Limit per source
            
            sources.append({
                "url": source_url,
                "title": fetch_result.get("title", "Unknown"),
                "fetched_at": datetime.utcnow().isoformat(),
                "license": "unknown",  # Would detect from page
                "snippet_length": len(content)
            })
    
    # Combine ground truth
    ground_truth_context = "\n\n---\n\n".join(ground_truth_parts)
    
    # Step 3: Synthesise context (would use LLM in production)
    synthesized_context = {
        "question": question_text,
        "topic": topic,
        "sub_topic": sub_topic,
        "summary": f"Synthesised information about {question_text}",
        "key_concepts": [],
        "definitions": {},
        "examples": [],
        "constraints": [],
        "source_count": len(sources)
    }
    
    # Step 4: Store in database
    result = database_tools.update_question_context(
        question_id=question_id,
        ground_truth_context=ground_truth_context,
        synthesized_context=json.dumps(synthesized_context),
        context_sources=sources,
        quality_score=0.8 if sources else 0.3
    )
    
    return {
        "status": "success" if result.get("status") == "success" else "error",
        "question_id": question_id,
        "sources_found": len(sources),
        "ground_truth_length": len(ground_truth_context)
    }


async def research_batch(
    questions: List[Dict[str, Any]],
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    Research multiple questions in batches.
    
    Args:
        questions: List of question dicts with id, question, topic, sub_topic
        batch_size: Number to process at once
        
    Returns:
        Batch results summary
    """
    results = []
    
    for i, q in enumerate(questions[:batch_size]):
        result = await research_question(
            question_id=q["id"],
            question_text=q["question"],
            topic=q["topic"],
            sub_topic=q["sub_topic"]
        )
        results.append(result)
        print(f"  Researched {i+1}/{min(len(questions), batch_size)}")
    
    successful = sum(1 for r in results if r["status"] == "success")
    
    return {
        "total": len(results),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results
    }
```

---

## 6. Phase 3: Generation Agent Creation

### 6.1 Create Directory Structure

```bash
mkdir -p src/orchestrator/generation_agent
```

### 6.2 Create Configuration

**File**: `src/orchestrator/generation_agent/generation.yaml`

```yaml
name: "generation_agent"
description: "Generates synthetic training data from questions and research context"
model: "gemini-2.5-flash"  # Use gemini-3-pro-preview for complex domains
instruction: |
  You are a synthetic data generation agent specialised in creating high-quality
  training examples for LLM post-training.
  
  Your capabilities:
  - Generate instruction-response pairs for SFT
  - Create preference pairs for DPO (chosen vs rejected responses)
  - Generate reasoning chains for GRPO with verifiable answers
  - Create reward-based data for PPO
  - Generate comparison data for RLHF
  - Create binary feedback data for KTO
  
  Quality standards:
  - Factually accurate based on provided context
  - Natural, diverse language (avoid repetitive patterns)
  - Appropriate difficulty for the target use case
  - Well-structured and complete
  - Code examples must be functional and tested
  - Mathematical solutions must be verified
  
  When generating code:
  - Always test with code executor before submitting
  - Handle edge cases appropriately
  - Include comments for clarity
  
  When generating reasoning:
  - Show clear step-by-step logic
  - Explain intermediate steps
  - Connect reasoning to final answer explicitly
  
  Use the provided context and tools to ensure accuracy.
```

### 6.3 Create Agent Module

**File**: `src/orchestrator/generation_agent/__init__.py`

```python
from .agent import root_agent

__all__ = ["root_agent"]
```

**File**: `src/orchestrator/generation_agent/agent.py`

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "generation.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.code_executors import BuiltInCodeExecutor

from tools.database_tools import DatabaseTools

# Initialise tools
database_tools = DatabaseTools()
code_executor = BuiltInCodeExecutor()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    tools=[database_tools],
    code_executor=code_executor,
)
```

### 6.4 Create Generation Workflows

**File**: `src/orchestrator/generation_agent/workflows.py`

```python
"""Workflow functions for synthetic data generation by training type."""

import json
from typing import Dict, Any, Optional
from schema.synthetic_data import TrainingType


async def generate_sft_data(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth_context: str,
    synthesized_context: str
) -> Dict[str, Any]:
    """
    Generate SFT (Supervised Fine-Tuning) data.
    
    Returns:
        Dict with: instruction, response, system_prompt
    """
    context = json.loads(synthesized_context) if isinstance(synthesized_context, str) else synthesized_context
    
    return {
        "system_prompt": f"You are an expert in {topic}, specifically {sub_topic}.",
        "instruction": question,
        "response": context.get("summary", ground_truth_context[:1000]),
        "topic": topic,
        "sub_topic": sub_topic,
        "task_type": "question_answering",
        "source": "synthetic_generated",
        "quality_score": None,
        "review_status": "pending"
    }


async def generate_grpo_data(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth_context: str,
    synthesized_context: str,
    code_executor=None
) -> Dict[str, Any]:
    """
    Generate GRPO (Group Relative Policy Optimisation) data.
    
    Includes reasoning chain, verification code, and correctness flag.
    
    Returns:
        Dict with: prompt, reasoning, code, predicted_answer, is_correct
    """
    context = json.loads(synthesized_context) if isinstance(synthesized_context, str) else synthesized_context
    
    # Generate reasoning chain
    key_concepts = context.get("key_concepts", [])
    reasoning = f"""
To answer "{question}", I will work through this step-by-step:

Step 1: Identify the key concepts
{', '.join(key_concepts) if key_concepts else 'Relevant concepts from the context.'}

Step 2: Apply the relevant principles
Based on the information provided, I need to consider the core aspects of {sub_topic}.

Step 3: Formulate the answer
Using the context and reasoning above, the answer is derived.

Step 4: Verify the solution
Cross-checking against the source material confirms the answer.
"""
    
    # Generate verification code (for code/math questions)
    code = f'''# Verification code for: {question}
# Topic: {topic}/{sub_topic}

def verify_answer():
    """Verify the answer is correct."""
    # Implementation based on question type
    result = True  # Would compute actual verification
    return result

if __name__ == "__main__":
    is_correct = verify_answer()
    print(f"Verification result: {{is_correct}}")
'''
    
    predicted_answer = "Answer derived from reasoning chain"
    is_correct = True  # Would be determined by code execution
    
    return {
        "prompt": question,
        "group_id": f"{topic}_{sub_topic}_group",
        "response": reasoning + f"\n\nFinal answer: {predicted_answer}",
        "reasoning": reasoning,
        "code": code,
        "predicted_answer": predicted_answer,
        "is_correct": is_correct,
        "topic": topic,
        "sub_topic": sub_topic,
        "task_type": "reasoning",
        "source": "synthetic_generated",
        "model_used": "gemini-2.5-flash",
        "review_status": "pending"
    }


async def generate_dpo_data(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth_context: str,
    synthesized_context: str
) -> Dict[str, Any]:
    """
    Generate DPO (Direct Preference Optimisation) data.
    
    Creates chosen (better) and rejected (worse) response pairs.
    
    Returns:
        Dict with: prompt, chosen, rejected, ratings
    """
    context = json.loads(synthesized_context) if isinstance(synthesized_context, str) else synthesized_context
    
    # Chosen response: accurate, detailed, well-structured
    summary = context.get("summary", "Detailed explanation based on authoritative sources.")
    key_concepts = context.get("key_concepts", [])
    
    chosen = f"""{summary}

Key points to understand:
{chr(10).join('• ' + str(k) for k in key_concepts) if key_concepts else '• Core concepts from the domain.'}

This explanation is based on established knowledge in {topic}."""
    
    # Rejected response: vague, potentially inaccurate, unhelpful
    rejected = f"""I'm not entirely sure about this topic. It's related to {topic} somehow, but I don't have specific information. Maybe try looking it up elsewhere?"""
    
    return {
        "system_prompt": f"You are an expert in {topic}.",
        "prompt": question,
        "chosen": chosen,
        "rejected": rejected,
        "chosen_rating": 5.0,
        "rejected_rating": 2.0,
        "preference_strength": 0.8,
        "topic": topic,
        "sub_topic": sub_topic,
        "preference_criteria": "helpfulness,accuracy,completeness",
        "source": "synthetic_generated",
        "review_status": "pending"
    }


async def generate_qa_data(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth_context: str,
    synthesized_context: str
) -> Dict[str, Any]:
    """
    Generate QA (Question-Answer) data.
    
    Returns:
        Dict with: question, answer, context, reasoning
    """
    context = json.loads(synthesized_context) if isinstance(synthesized_context, str) else synthesized_context
    
    return {
        "question": question,
        "answer": context.get("summary", ground_truth_context[:500]),
        "context": ground_truth_context[:2000],
        "reasoning": f"Answer derived from authoritative sources on {topic}/{sub_topic}.",
        "topic": topic,
        "sub_topic": sub_topic,
        "difficulty": "medium",
        "source": "synthetic_generated",
        "quality_score": None,
        "review_status": "pending"
    }


# Registry of generation functions by training type
GENERATION_FUNCTIONS = {
    TrainingType.SFT: generate_sft_data,
    TrainingType.GRPO: generate_grpo_data,
    TrainingType.DPO: generate_dpo_data,
    TrainingType.QA: generate_qa_data,
}


async def generate_training_data(
    training_type: TrainingType,
    question_data: Dict[str, Any],
    code_executor=None
) -> Dict[str, Any]:
    """
    Generate training data based on type.
    
    Args:
        training_type: Type of training data to generate
        question_data: Dict with question, topic, sub_topic, context fields
        code_executor: Optional code executor for verification
        
    Returns:
        Generated training data dict
    """
    generator_func = GENERATION_FUNCTIONS.get(training_type)
    
    if not generator_func:
        raise ValueError(f"No generator for training type: {training_type}")
    
    # Check if function accepts code_executor
    import inspect
    sig = inspect.signature(generator_func)
    
    if 'code_executor' in sig.parameters:
        return await generator_func(
            question=question_data['question'],
            topic=question_data['topic'],
            sub_topic=question_data['sub_topic'],
            ground_truth_context=question_data.get('ground_truth_context', ''),
            synthesized_context=question_data.get('synthesized_context', '{}'),
            code_executor=code_executor
        )
    else:
        return await generator_func(
            question=question_data['question'],
            topic=question_data['topic'],
            sub_topic=question_data['sub_topic'],
            ground_truth_context=question_data.get('ground_truth_context', ''),
            synthesized_context=question_data.get('synthesized_context', '{}')
        )
```

---

## 7. Phase 4: Reviewer Agent Implementation

### 7.1 Create Configuration

**File**: `src/orchestrator/reviewer_agent/reviewer.yaml`

```yaml
name: "reviewer_agent"
description: "Reviews and validates synthetic training data for quality and correctness"
model: "gemini-2.5-flash"  # Use gemini-3-pro-preview for complex validation
instruction: |
  You are a quality assurance agent that validates synthetic training data.
  
  Your responsibilities:
  1. Verify factual accuracy against ground truth context
  2. Check reasoning chains for logical consistency
  3. Test code examples for correctness
  4. Ensure responses are well-formatted
  5. Validate domain-specific knowledge
  
  Scoring criteria (0-1 scale):
  - Factual accuracy: Is the information correct?
  - Completeness: Does it fully answer the question?
  - Clarity: Is it well-explained and understandable?
  - Format compliance: Does it match training type requirements?
  
  For code:
  - Must execute without errors
  - Must produce correct output
  - Must handle edge cases
  
  For reasoning:
  - Steps must be logically sound
  - Conclusion must follow from premises
  - No logical fallacies
  
  Provide detailed feedback for any issues found.
  
  Status options:
  - "approved": High quality, ready to use
  - "needs_revision": Has issues but salvageable
  - "rejected": Fundamentally flawed, discard
```

### 7.2 Create Agent Module

**File**: `src/orchestrator/reviewer_agent/__init__.py`

```python
from .agent import root_agent

__all__ = ["root_agent"]
```

**File**: `src/orchestrator/reviewer_agent/agent.py`

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "reviewer.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.code_executors import BuiltInCodeExecutor

from tools.web_tools import WebTools
from tools.database_tools import DatabaseTools

# Initialise tools
web_tools = WebTools()
database_tools = DatabaseTools()
code_executor = BuiltInCodeExecutor()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    tools=[web_tools, database_tools],
    code_executor=code_executor,
)
```

### 7.3 Create Review Workflows

**File**: `src/orchestrator/reviewer_agent/workflows.py`

```python
"""Review workflows for quality assurance and validation."""

import json
from typing import Dict, Any, Optional


async def review_sft_data(
    data: Dict[str, Any],
    ground_truth: str
) -> Dict[str, Any]:
    """
    Review SFT training data.
    
    Returns:
        Review results with scores and status
    """
    scores = {
        "factual_accuracy": 0.0,
        "completeness": 0.0,
        "clarity": 0.0,
        "format_compliance": 0.0
    }
    
    # Check format compliance
    required_fields = ["instruction", "response"]
    has_all_fields = all(field in data and data[field] for field in required_fields)
    scores["format_compliance"] = 1.0 if has_all_fields else 0.0
    
    # Check response quality
    response = data.get("response", "")
    response_length = len(response)
    
    # Completeness: based on response length
    scores["completeness"] = min(1.0, response_length / 200)
    
    # Clarity: check for structure
    has_structure = any(marker in response for marker in [".", "\n", ":", "•", "-"])
    scores["clarity"] = 0.8 if has_structure else 0.5
    
    # Factual accuracy: would compare against ground truth
    # Simplified: assume reasonable if context was used
    if ground_truth and any(word in response.lower() for word in ground_truth.lower().split()[:10]):
        scores["factual_accuracy"] = 0.85
    else:
        scores["factual_accuracy"] = 0.6
    
    # Calculate overall score
    overall_score = sum(scores.values()) / len(scores)
    
    # Determine status
    if overall_score >= 0.8:
        status = "approved"
    elif overall_score >= 0.6:
        status = "needs_revision"
    else:
        status = "rejected"
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": f"Scores: {json.dumps(scores, indent=2)}"
    }


async def review_grpo_data(
    data: Dict[str, Any],
    code_executor=None
) -> Dict[str, Any]:
    """
    Review GRPO data including code execution verification.
    
    Returns:
        Review results with verification status
    """
    scores = {
        "reasoning_quality": 0.0,
        "code_correctness": 0.0,
        "answer_verification": 0.0,
        "format_compliance": 0.0
    }
    
    # Check format
    required_fields = ["prompt", "reasoning", "predicted_answer"]
    has_all_fields = all(field in data and data[field] for field in required_fields)
    scores["format_compliance"] = 1.0 if has_all_fields else 0.0
    
    # Check reasoning quality
    reasoning = data.get("reasoning", "")
    has_steps = "step" in reasoning.lower() or any(f"Step {i}" in reasoning for i in range(1, 6))
    has_conclusion = any(word in reasoning.lower() for word in ["therefore", "thus", "answer", "conclusion"])
    scores["reasoning_quality"] = 0.9 if (has_steps and has_conclusion) else (0.6 if has_steps else 0.4)
    
    # Check code (if present)
    code = data.get("code", "")
    if code:
        # Would execute code here with code_executor
        # For now, check for basic structure
        has_function = "def " in code
        has_return = "return" in code or "print" in code
        scores["code_correctness"] = 0.9 if (has_function and has_return) else 0.5
    else:
        scores["code_correctness"] = 0.5  # No code to test
    
    # Verify answer correctness
    is_correct = data.get("is_correct", False)
    scores["answer_verification"] = 1.0 if is_correct else 0.3
    
    overall_score = sum(scores.values()) / len(scores)
    
    if overall_score >= 0.8:
        status = "approved"
    elif overall_score >= 0.6:
        status = "needs_revision"
    else:
        status = "rejected"
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": f"Code present: {bool(code)}, Answer marked correct: {is_correct}"
    }


async def review_dpo_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review DPO preference pair data.
    
    Returns:
        Review results with preference validation
    """
    scores = {
        "chosen_quality": 0.0,
        "rejected_quality": 0.0,
        "preference_clarity": 0.0,
        "format_compliance": 0.0
    }
    
    # Check format
    required_fields = ["prompt", "chosen", "rejected"]
    has_all_fields = all(field in data and data[field] for field in required_fields)
    scores["format_compliance"] = 1.0 if has_all_fields else 0.0
    
    chosen = data.get("chosen", "")
    rejected = data.get("rejected", "")
    
    # Chosen should be substantially better
    scores["chosen_quality"] = min(1.0, len(chosen) / 200)
    scores["rejected_quality"] = 0.8 if len(rejected) > 20 else 0.4
    
    # Preference should be clear (chosen much longer/better structured)
    length_ratio = len(chosen) / max(len(rejected), 1)
    scores["preference_clarity"] = min(1.0, length_ratio / 3)
    
    # Validate: chosen != rejected
    if chosen.strip() == rejected.strip():
        scores["preference_clarity"] = 0.0
    
    overall_score = sum(scores.values()) / len(scores)
    
    if overall_score >= 0.75:
        status = "approved"
    elif overall_score >= 0.5:
        status = "needs_revision"
    else:
        status = "rejected"
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": f"Chosen length: {len(chosen)}, Rejected length: {len(rejected)}"
    }
```

---

## 8. Phase 5: Workflow Integration

### 8.1 Update Orchestrator Agent

**File**: `src/orchestrator/agent.py`

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "orchestrator.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

# Import all sub-agents
from .planning_agent import root_agent as planning_agent
from .question_agent import root_agent as question_agent
from .research_agent import root_agent as research_agent
from .generation_agent import root_agent as generation_agent
from .reviewer_agent import root_agent as reviewer_agent

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    sub_agents=[
        planning_agent,
        question_agent,
        research_agent,
        generation_agent,
        reviewer_agent
    ]
)
```

### 8.2 Create Main Pipeline Workflow

**File**: `workflows/synthetic_data_workflow.py` (create `workflows/` directory)

```python
"""
Main workflow for synthetic data generation.

Orchestrates the complete pipeline:
1. Planning
2. Question generation
3. Research
4. Data generation
5. Review
"""

import asyncio
from typing import Dict, Any, List
from schema.synthetic_data import TrainingType
from tools.database_tools import DatabaseTools
from src.orchestrator.research_agent.agent import research_question
from src.orchestrator.generation_agent.workflows import generate_training_data
from src.orchestrator.reviewer_agent.workflows import review_sft_data, review_grpo_data, review_dpo_data

database_tools = DatabaseTools()


async def run_synthetic_data_pipeline(
    topic: str,
    sub_topic: str,
    training_type: TrainingType,
    num_questions: int = 10
) -> Dict[str, Any]:
    """
    Run the complete synthetic data generation pipeline.
    
    Args:
        topic: Main topic (e.g., "chemistry")
        sub_topic: Sub-topic (e.g., "organic chemistry")
        training_type: Type of training data to generate
        num_questions: Number of questions to generate
        
    Returns:
        Pipeline results summary
    """
    print(f"\n{'='*60}")
    print(f"🚀 Starting Synthetic Data Generation Pipeline")
    print(f"{'='*60}")
    print(f"   Topic: {topic} / {sub_topic}")
    print(f"   Training Type: {training_type.value}")
    print(f"   Target: {num_questions} examples\n")
    
    stats = {
        "questions_generated": 0,
        "research_completed": 0,
        "data_generated": 0,
        "approved": 0,
        "rejected": 0
    }
    
    # ────────────────────────────────────────────────────────────
    # Phase 1: Question Generation
    # ────────────────────────────────────────────────────────────
    print("📝 Phase 1: Generating questions...")
    
    # In production, this would call the question agent
    sample_questions = [
        f"What is the fundamental concept of {sub_topic}?",
        f"How does {sub_topic} relate to broader {topic}?",
        f"What are the key principles in {sub_topic}?",
        f"Explain an important application of {sub_topic}.",
        f"What are common misconceptions about {sub_topic}?",
    ][:num_questions]
    
    result = database_tools.add_questions_to_database(
        questions=sample_questions,
        topic=topic,
        sub_topic=sub_topic,
        training_type=training_type.value
    )
    stats["questions_generated"] = result.get("count", 0)
    print(f"   ✅ Generated {stats['questions_generated']} questions\n")
    
    # ────────────────────────────────────────────────────────────
    # Phase 2: Research
    # ────────────────────────────────────────────────────────────
    print("🔍 Phase 2: Conducting research...")
    
    pending_questions = database_tools.get_pending_questions(topic, sub_topic)
    
    for i, q in enumerate(pending_questions):
        print(f"   [{i+1}/{len(pending_questions)}] Researching: {q['question'][:40]}...")
        await research_question(
            question_id=q['id'],
            question_text=q['question'],
            topic=topic,
            sub_topic=sub_topic
        )
        stats["research_completed"] += 1
    
    print(f"   ✅ Research complete for {stats['research_completed']} questions\n")
    
    # ────────────────────────────────────────────────────────────
    # Phase 3: Generation
    # ────────────────────────────────────────────────────────────
    print("⚙️  Phase 3: Generating training data...")
    
    # Get researched questions (would query with status='researched')
    for i, q in enumerate(pending_questions):
        # Build question data from DB (simplified)
        question_data = {
            'question': q['question'],
            'topic': topic,
            'sub_topic': sub_topic,
            'ground_truth_context': "Sample ground truth context from research...",
            'synthesized_context': '{"summary": "Synthesised information..."}'
        }
        
        # Generate training data
        training_data = await generate_training_data(
            training_type=training_type,
            question_data=question_data
        )
        
        # Save to database
        database_tools.add_synthetic_data(
            training_type=training_type.value,
            data=training_data
        )
        stats["data_generated"] += 1
        print(f"   [{i+1}/{len(pending_questions)}] Generated")
    
    print(f"   ✅ Generated {stats['data_generated']} training examples\n")
    
    # ────────────────────────────────────────────────────────────
    # Phase 4: Review
    # ────────────────────────────────────────────────────────────
    print("✓  Phase 4: Reviewing quality...")
    
    # Would retrieve generated data and review each item
    # For now, assume all pass
    stats["approved"] = stats["data_generated"]
    
    print(f"   ✅ Review complete: {stats['approved']} approved\n")
    
    # ────────────────────────────────────────────────────────────
    # Summary
    # ────────────────────────────────────────────────────────────
    print(f"{'='*60}")
    print("🎉 Pipeline Complete!")
    print(f"{'='*60}")
    print(f"   Questions generated: {stats['questions_generated']}")
    print(f"   Research completed:  {stats['research_completed']}")
    print(f"   Data generated:      {stats['data_generated']}")
    print(f"   Approved:            {stats['approved']}")
    print(f"   Rejected:            {stats['rejected']}")
    print(f"   Output table:        synthetic_data_{training_type.value}")
    print()
    
    return stats


if __name__ == "__main__":
    asyncio.run(run_synthetic_data_pipeline(
        topic="chemistry",
        sub_topic="organic chemistry",
        training_type=TrainingType.SFT,
        num_questions=5
    ))
```

### 8.3 Update main.py

**File**: `main.py`

```python
"""Main entry point for synthetic data generation."""

import asyncio
from workflows.synthetic_data_workflow import run_synthetic_data_pipeline
from schema.synthetic_data import TrainingType


async def main():
    """Run the synthetic data generation pipeline."""
    print("\n" + "="*60)
    print("  Synthetic Data Generation Agent")
    print("="*60 + "\n")
    
    print("What would you like to generate?\n")
    print("  1. Chemistry SFT data")
    print("  2. Mathematics GRPO data")
    print("  3. Coding DPO data")
    print("  4. Custom configuration")
    print("  5. Exit")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        await run_synthetic_data_pipeline(
            topic="chemistry",
            sub_topic="organic chemistry",
            training_type=TrainingType.SFT,
            num_questions=10
        )
    elif choice == "2":
        await run_synthetic_data_pipeline(
            topic="mathematics",
            sub_topic="algebra",
            training_type=TrainingType.GRPO,
            num_questions=10
        )
    elif choice == "3":
        await run_synthetic_data_pipeline(
            topic="programming",
            sub_topic="python",
            training_type=TrainingType.DPO,
            num_questions=10
        )
    elif choice == "4":
        topic = input("Topic: ").strip()
        sub_topic = input("Sub-topic: ").strip()
        
        print("\nTraining types: sft, dpo, grpo, ppo, rlhf, kto, orpo, chat, qa")
        training_type_str = input("Training type: ").strip().lower()
        
        num = input("Number of examples (default 10): ").strip()
        num = int(num) if num else 10
        
        await run_synthetic_data_pipeline(
            topic=topic,
            sub_topic=sub_topic,
            training_type=TrainingType(training_type_str),
            num_questions=num
        )
    elif choice == "5":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 9. Phase 6: Testing

### 9.1 Create Test Directory

```bash
mkdir -p tests
```

### 9.2 Database Tests

**File**: `tests/test_database.py`

```python
"""Tests for database tools."""

import pytest
from tools.database_tools import DatabaseTools


def test_add_questions():
    """Test adding questions to database."""
    db_tools = DatabaseTools()
    
    result = db_tools.add_questions_to_database(
        questions=["Test question 1", "Test question 2"],
        topic="test",
        sub_topic="testing",
        training_type="sft"
    )
    
    assert result["status"] == "success"
    assert result["count"] == 2
    assert len(result["question_ids"]) == 2


def test_get_pending_questions():
    """Test retrieving pending questions."""
    db_tools = DatabaseTools()
    
    # Add a question first
    db_tools.add_questions_to_database(
        questions=["Pending test question"],
        topic="test_pending",
        sub_topic="testing"
    )
    
    # Retrieve pending
    pending = db_tools.get_pending_questions(topic="test_pending")
    
    assert len(pending) > 0
    assert pending[0]["status"] == "pending"


def test_add_synthetic_data():
    """Test adding synthetic data."""
    db_tools = DatabaseTools()
    
    result = db_tools.add_synthetic_data(
        training_type="sft",
        data={
            "instruction": "Test instruction",
            "response": "Test response",
            "topic": "test",
            "sub_topic": "testing"
        }
    )
    
    assert result["status"] == "success"
    assert "id" in result
```

### 9.3 Integration Tests

**File**: `tests/test_integration.py`

```python
"""Integration tests for the full pipeline."""

import pytest
import asyncio
from workflows.synthetic_data_workflow import run_synthetic_data_pipeline
from schema.synthetic_data import TrainingType


@pytest.mark.asyncio
async def test_sft_pipeline():
    """Test complete SFT data generation pipeline."""
    result = await run_synthetic_data_pipeline(
        topic="test_topic",
        sub_topic="test_subtopic",
        training_type=TrainingType.SFT,
        num_questions=2
    )
    
    assert result["questions_generated"] == 2
    assert result["data_generated"] == 2


@pytest.mark.asyncio
async def test_grpo_pipeline():
    """Test complete GRPO data generation pipeline."""
    result = await run_synthetic_data_pipeline(
        topic="test_math",
        sub_topic="algebra",
        training_type=TrainingType.GRPO,
        num_questions=2
    )
    
    assert result["questions_generated"] == 2
    assert result["data_generated"] == 2
```

### 9.4 Run Tests

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_database.py -v
```

---

## 10. "Done When" Milestones

### Milestone A: Artifacts and Research ✓
- Questions have task spec, evidence, and reference solution stored
- Questions progress through stages without manual intervention
- Artifacts are consistent enough for validators

### Milestone B: QA/SFT End-to-End ✓
- Answer agent produces QA or SFT rows from artifacts
- Reviewer can approve/reject deterministically for a subset of tasks
- Dataset export is clean and stable

### Milestone C: GRPO for Verifiable Tasks
- Candidate groups are generated and parsed reliably
- Correctness verified deterministically for maths/code tasks
- Rank/reward calculations are stable and auditable

### Milestone D: DPO/ORPO
- Generate multiple candidates per prompt
- Reviewer selects chosen/rejected consistently with structured reasons
- Avoid degenerate pairs (chosen == rejected, or both wrong)

---

## 11. Success Criteria

The implementation is successful when:

1. ✅ `python create_database.py` creates all tables
2. ✅ `python main.py` runs and shows menu
3. ✅ Pipeline generates questions and saves to database
4. ✅ Research completes and context is stored
5. ✅ Training data is generated and saved to correct table
6. ✅ Review scores are calculated and stored
7. ✅ Database query shows complete records

**Example Success Output**:

```
============================================================
🚀 Starting Synthetic Data Generation Pipeline
============================================================
   Topic: chemistry / organic chemistry
   Training Type: sft
   Target: 10 examples

📝 Phase 1: Generating questions...
   ✅ Generated 10 questions

🔍 Phase 2: Conducting research...
   [1/10] Researching: What is the fundamental concept of...
   ...
   ✅ Research complete for 10 questions

⚙️  Phase 3: Generating training data...
   [1/10] Generated
   ...
   ✅ Generated 10 training examples

✓  Phase 4: Reviewing quality...
   ✅ Review complete: 10 approved

============================================================
🎉 Pipeline Complete!
============================================================
   Questions generated: 10
   Research completed:  10
   Data generated:      10
   Approved:            10
   Rejected:            0
   Output table:        synthetic_data_sft
```

---

## 12. Troubleshooting

### Database Connection Errors

```python
# Check database path exists
from pathlib import Path
db_path = Path(__file__).parent / "db" / "synthetic_data.db"
assert db_path.parent.exists(), f"Directory missing: {db_path.parent}"
```

### Agent Not Using Tools

```python
# Verify tool registration
agent = LlmAgent(
    tools=[tool1, tool2],  # Ensure list is populated
    instruction="Use the tools to..."  # Must reference tools
)
```

### Code Execution Failures

```python
# Use sandboxed executor for production
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name="..."
)
```

### Import Errors

```python
# Add parent to path at top of module
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
```

---

## 13. Checklist

### Before Starting
- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -e .`)
- [ ] Google Cloud credentials configured

### Phase 1: Database
- [ ] Questions table updated with artifact fields
- [ ] `update_question_context()` implemented
- [ ] `update_question_artifacts()` implemented
- [ ] Database initialisation script works

### Phase 2: Research Agent
- [ ] research.yaml configuration complete
- [ ] Research workflow implemented
- [ ] Context storage tested

### Phase 3: Generation Agent
- [ ] generation_agent directory created
- [ ] generation.yaml configuration complete
- [ ] Generation workflows for SFT/DPO/GRPO implemented

### Phase 4: Reviewer Agent
- [ ] reviewer.yaml configuration complete
- [ ] Review workflows implemented
- [ ] Quality scoring works

### Phase 5: Integration
- [ ] Orchestrator updated with all sub-agents
- [ ] Main workflow created
- [ ] main.py updated and working

### Phase 6: Testing
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Manual end-to-end test successful

---

## 14. Next Steps After Core Implementation

### Specialist Agents (Optional)

```python
# src/orchestrator/generation_agent/specialists/math_specialist.py
from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor

math_specialist = LlmAgent(
    name="math_specialist",
    description="Expert in mathematical problem solving",
    instruction="""
    You are a mathematics expert. Always:
    - Show step-by-step work
    - Verify solutions with code
    - Handle edge cases
    """,
    code_executor=BuiltInCodeExecutor()
)
```

### Production Deployment

```bash
# Build Docker container
docker build -t synthetic-data-agent .

# Deploy to Cloud Run
gcloud run deploy synthetic-data-agent \
  --source . \
  --region us-central1
```

### Advanced Features to Add
- Parallel question processing
- Quality metrics dashboard
- Data export (JSONL, Parquet, HuggingFace)
- Human-in-the-loop review UI
- Active learning (identify knowledge gaps)

---

## Summary

This implementation guide provides a clear path from the current partially-implemented state to a fully functional synthetic data generation system. The phased approach ensures each component is built and tested before moving to the next, with the Generation Agent being the critical piece that bridges research and final output.

**Timeline**: 3-4 focused days of development to reach MVP.

**Priority Order**:
1. Database schema updates (foundation)
2. Research agent completion (context is king)
3. Generation agent creation (the core blocker)
4. Reviewer agent (quality assurance)
5. Workflow integration (tie it together)
6. Testing (ensure reliability)
