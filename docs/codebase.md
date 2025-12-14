# Codebase

This file contains the contents of all Python files in the `.` directory.

---

## code_to_markdown.py

```python
"""Script to recursively save all Python files from src directory to a markdown file."""

import os
from pathlib import Path


def collect_python_files_to_markdown(src_dir: str = ".", output_file: str = "codebase.md") -> None:
    """
    Recursively walk through src directory and save all Python file contents to a markdown file.
    
    Args:
        src_dir: The source directory to scan for Python files.
        output_file: The output markdown file name.
    """
    src_path = Path(src_dir)
    
    if not src_path.exists():
        print(f"Error: Directory '{src_dir}' does not exist.")
        return
    
    # Collect all Python files recursively, excluding .venv directory
    python_files = sorted(
        py_file for py_file in src_path.rglob("*.py")
        if ".venv" not in py_file.parts
    )
    
    if not python_files:
        print(f"No Python files found in '{src_dir}'.")
        return
    
    with open(output_file, "w", encoding="utf-8") as md_file:
        md_file.write("# Codebase\n\n")
        md_file.write(f"This file contains the contents of all Python files in the `{src_dir}` directory.\n\n")
        md_file.write("---\n\n")
        
        for py_file in python_files:
            # Get relative path from src directory for the heading
            relative_path = py_file.relative_to(src_path.parent)
            
            print(f"Processing: {relative_path}")
            
            # Write the heading with the file path
            md_file.write(f"## {relative_path}\n\n")
            
            # Read and write the file contents in a code block
            try:
                content = py_file.read_text(encoding="utf-8")
                md_file.write("```python\n")
                md_file.write(content)
                # Ensure there's a newline before closing the code block
                if not content.endswith("\n"):
                    md_file.write("\n")
                md_file.write("```\n\n")
            except Exception as e:
                md_file.write(f"*Error reading file: {e}*\n\n")
    
    print(f"\nSuccessfully saved {len(python_files)} Python files to '{output_file}'")


if __name__ == "__main__":
    collect_python_files_to_markdown()
```

## main.py

```python
def main():
    print("Hello from synthetic-data-agent!")


if __name__ == "__main__":
    main()
```

## models\models.py

```python
from pydantic import BaseModel, Field
from schema.synethtic_data import TrainingType

class PlanningResponse(BaseModel):
    topic: str = Field(..., description="The topic of the data to be generated")
    training_type: TrainingType = Field(..., description="The training that the user requires")
    research_plan: str = Field(..., description="The research plan to be used")
    data_structure_specification: str = Field(..., description="The data structure specification to be used")
    execution_plan: str = Field(..., description="The execution plan to be used")
    reasoning: str = Field(..., description="The reasoning to be used")

class Questions(BaseModel):
    topic: str = Field(..., description="The topic of the data to be generated")
    sub_topic: str = Field(..., description="The sub topic of the data to be generated")
    questions: list[str] = Field(..., description="The questions to be asked")
```

## schema\synethtic_data.py

```python
"""
Synthetic Data Schemas for LLM Post-Training Techniques

This module defines database schemas for various LLM fine-tuning and alignment methods.
The agent will select the appropriate schema based on the user's training objective.

Supported Training Techniques:
- SFT (Supervised Fine-Tuning): Instruction-response pairs
- DPO (Direct Preference Optimization): Preference pairs with chosen/rejected
- PPO (Proximal Policy Optimization): Prompts with reward signals
- GRPO (Group Relative Policy Optimization): Group-based reward comparisons
- RLHF (Reinforcement Learning from Human Feedback): Reward model training data
- KTO (Kahneman-Tversky Optimization): Binary feedback (good/bad)
- ORPO (Odds Ratio Preference Optimization): Combined SFT + preference alignment
"""

from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class TrainingType(str, Enum):
    """Enum for selecting the appropriate training technique and database."""
    SFT = "sft"                 # Supervised Fine-Tuning
    DPO = "dpo"                 # Direct Preference Optimization
    PPO = "ppo"                 # Proximal Policy Optimization
    GRPO = "grpo"               # Group Relative Policy Optimization
    RLHF = "rlhf"               # Reinforcement Learning from Human Feedback
    KTO = "kto"                 # Kahneman-Tversky Optimization
    ORPO = "orpo"               # Odds Ratio Preference Optimization
    CHAT = "chat"               # Multi-turn conversation data
    QA = "qa"                   # Question-Answer pairs


# =============================================================================
# SFT (Supervised Fine-Tuning) Schema
# Format: instruction -> response pairs, optionally with system prompt
# =============================================================================

class SyntheticDataSFT(Base):
    """
    Schema for Supervised Fine-Tuning (SFT) data.
    
    Standard format for instruction-tuning models like Alpaca, Dolly, etc.
    Can include optional system prompts and input context.
    """
    __tablename__ = "synthetic_data_sft"
    
    id = Column(Integer, primary_key=True)
    
    # Core SFT fields
    system_prompt = Column(Text, nullable=True)          # Optional system instruction
    instruction = Column(Text, nullable=False)           # User instruction/prompt
    input_context = Column(Text, nullable=True)          # Optional additional context
    response = Column(Text, nullable=False)              # Model response to learn
    
    # Metadata
    topic = Column(String(255), nullable=True)           # Topic category
    sub_topic = Column(String(255), nullable=True)       # Sub-topic category (e.g., "organic", "analytical", "inorganic")
    task_type = Column(String(100), nullable=True)       # e.g., "summarization", "coding", "qa"
    difficulty = Column(String(50), nullable=True)       # e.g., "easy", "medium", "hard"
    language = Column(String(50), default="en")          # Language code
    
    # Quality & Source
    source = Column(String(255), nullable=True)          # Data source
    quality_score = Column(Float, nullable=True)         # Quality rating 0-1
    review_status = Column(String(50), nullable=True)    # "pending", "approved", "rejected"
    reviewer_notes = Column(Text, nullable=True)
    
    # Generation metadata
    model_used = Column(String(100), nullable=True)      # Model that generated the data
    temperature = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# DPO (Direct Preference Optimization) Schema
# Format: prompt + chosen response + rejected response
# =============================================================================

class SyntheticDataDPO(Base):
    """
    Schema for Direct Preference Optimization (DPO) data.
    
    DPO requires preference pairs: a chosen (preferred) response and 
    a rejected (less preferred) response for the same prompt.
    """
    __tablename__ = "synthetic_data_dpo"
    
    id = Column(Integer, primary_key=True)
    
    # Core DPO fields
    system_prompt = Column(Text, nullable=True)          # Optional system instruction
    prompt = Column(Text, nullable=False)                # The input prompt
    chosen = Column(Text, nullable=False)                # Preferred/better response
    rejected = Column(Text, nullable=False)              # Less preferred response
    
    # Preference metadata
    chosen_rating = Column(Float, nullable=True)         # Rating for chosen (e.g., 1-5)
    rejected_rating = Column(Float, nullable=True)       # Rating for rejected
    preference_strength = Column(Float, nullable=True)   # How strong is the preference (0-1)
    
    # Categorization
    topic = Column(String(255), nullable=True)
    sub_topic = Column(String(255), nullable=True)       # Sub-topic category (e.g., "organic", "analytical", "inorganic")
    preference_criteria = Column(String(255), nullable=True)  # e.g., "helpfulness", "safety", "accuracy"
    
    # Quality & Source
    source = Column(String(255), nullable=True)
    annotator_id = Column(String(100), nullable=True)    # Who provided the preference
    review_status = Column(String(50), nullable=True)
    
    # Generation metadata
    chosen_model = Column(String(100), nullable=True)    # Model that generated chosen
    rejected_model = Column(String(100), nullable=True)  # Model that generated rejected
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# PPO (Proximal Policy Optimization) Schema
# Format: prompt + response + reward signal
# =============================================================================

class SyntheticDataPPO(Base):
    """
    Schema for Proximal Policy Optimization (PPO) data.
    
    PPO training requires prompts, generated responses, and reward signals
    from a reward model or human feedback.
    """
    __tablename__ = "synthetic_data_ppo"
    
    id = Column(Integer, primary_key=True)
    
    # Core PPO fields
    prompt = Column(Text, nullable=False)                # Input prompt
    response = Column(Text, nullable=False)              # Generated response
    reward = Column(Float, nullable=False)               # Reward signal (-inf to +inf, typically -1 to 1)
    
    # Additional reward breakdown (optional)
    reward_components = Column(JSON, nullable=True)      # {"helpfulness": 0.8, "safety": 0.9, ...}
    
    # Value estimation (for advantage calculation)
    value_estimate = Column(Float, nullable=True)        # Baseline value estimate
    advantage = Column(Float, nullable=True)             # Computed advantage
    
    # Metadata
    topic = Column(String(255), nullable=True)
    sub_topic = Column(String(255), nullable=True)       # Sub-topic category (e.g., "organic", "analytical", "inorganic")
    reward_model = Column(String(100), nullable=True)    # Reward model used
    policy_model = Column(String(100), nullable=True)    # Policy model version
    
    # Quality & Source
    source = Column(String(255), nullable=True)
    review_status = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# GRPO (Group Relative Policy Optimization) Schema
# Format: prompt + multiple responses with group-relative rewards
# =============================================================================

class SyntheticDataGRPO(Base):
    """
    Schema for Group Relative Policy Optimization (GRPO) data.
    
    GRPO uses group-based comparisons where multiple responses are generated
    for the same prompt and ranked/scored relative to each other.
    Often used for reasoning tasks (math, code) with verifiable answers.
    """
    __tablename__ = "synthetic_data_grpo"
    
    id = Column(Integer, primary_key=True)
    
    # Core GRPO fields
    prompt = Column(Text, nullable=False)                # Input prompt/question
    group_id = Column(String(100), nullable=False)       # Groups responses for same prompt
    response = Column(Text, nullable=False)              # One of the group responses
    
    # Reasoning chain (for CoT)
    reasoning = Column(Text, nullable=True)              # Step-by-step reasoning
    
    # For verifiable tasks (math, code)
    code = Column(Text, nullable=True)                   # Generated code if applicable
    expected_answer = Column(String(255), nullable=True) # Ground truth answer
    predicted_answer = Column(String(255), nullable=True) # Model's prediction
    is_correct = Column(Boolean, nullable=True)          # Whether answer is correct
    
    # Group-relative scoring
    group_rank = Column(Integer, nullable=True)          # Rank within the group (1 = best)
    group_size = Column(Integer, nullable=True)          # Total responses in group
    relative_reward = Column(Float, nullable=True)       # Normalized reward within group
    absolute_reward = Column(Float, nullable=True)       # Raw reward score
    
    # Metadata
    topic = Column(String(255), nullable=True)
    sub_topic = Column(String(255), nullable=True)       # Sub-topic category (e.g., "organic", "analytical", "inorganic")
    task_type = Column(String(100), nullable=True)       # "math", "coding", "reasoning"
    difficulty = Column(String(50), nullable=True)
    source = Column(String(255), nullable=True)
    
    # Generation metadata
    model_used = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    sampling_strategy = Column(String(50), nullable=True) # e.g., "diverse", "beam"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# RLHF (Reinforcement Learning from Human Feedback) Schema
# Format: Comparison data for reward model training
# =============================================================================

class SyntheticDataRLHF(Base):
    """
    Schema for RLHF Reward Model training data.
    
    Used to train reward models that score responses based on human preferences.
    Supports pairwise comparisons and absolute ratings.
    """
    __tablename__ = "synthetic_data_rlhf"
    
    id = Column(Integer, primary_key=True)
    
    # Core fields
    prompt = Column(Text, nullable=False)                # Input prompt
    
    # Comparison data (for pairwise training)
    response_a = Column(Text, nullable=True)             # First response
    response_b = Column(Text, nullable=True)             # Second response
    preference = Column(String(10), nullable=True)       # "a", "b", or "tie"
    
    # Single response rating (for pointwise training)
    response = Column(Text, nullable=True)               # Single response
    rating = Column(Float, nullable=True)                # Absolute rating (e.g., 1-5)
    
    # Multi-dimensional feedback
    helpfulness = Column(Float, nullable=True)           # 0-1 score
    harmlessness = Column(Float, nullable=True)          # 0-1 score
    honesty = Column(Float, nullable=True)               # 0-1 score
    
    # Annotator information
    annotator_id = Column(String(100), nullable=True)
    annotation_time_seconds = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)            # Annotator confidence 0-1
    
    # Metadata
    topic = Column(String(255), nullable=True)
    sub_topic = Column(String(255), nullable=True)       # Sub-topic category (e.g., "organic", "analytical", "inorganic")
    source = Column(String(255), nullable=True)
    review_status = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# KTO (Kahneman-Tversky Optimization) Schema
# Format: prompt + response + binary signal (desirable/undesirable)
# =============================================================================

class SyntheticDataKTO(Base):
    """
    Schema for Kahneman-Tversky Optimization (KTO) data.
    
    KTO uses binary feedback (good/bad) rather than preference pairs,
    making it easier to collect training data at scale.
    """
    __tablename__ = "synthetic_data_kto"
    
    id = Column(Integer, primary_key=True)
    
    # Core KTO fields
    prompt = Column(Text, nullable=False)                # Input prompt
    response = Column(Text, nullable=False)              # Generated response
    is_desirable = Column(Boolean, nullable=False)       # True = good, False = bad
    
    # Optional refinement
    feedback_reason = Column(Text, nullable=True)        # Why it's good/bad
    improvement_suggestion = Column(Text, nullable=True) # How to improve if bad
    
    # Metadata
    topic = Column(String(255), nullable=True)
    sub_topic = Column(String(255), nullable=True)       # Sub-topic category (e.g., "organic", "analytical", "inorganic")
    feedback_source = Column(String(100), nullable=True) # "human", "model", "rule-based"
    
    # Quality & Source
    source = Column(String(255), nullable=True)
    annotator_id = Column(String(100), nullable=True)
    review_status = Column(String(50), nullable=True)
    
    # Generation metadata
    model_used = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# ORPO (Odds Ratio Preference Optimization) Schema
# Format: Combines SFT and preference alignment in single training
# =============================================================================

class SyntheticDataORPO(Base):
    """
    Schema for Odds Ratio Preference Optimization (ORPO) data.
    
    ORPO combines SFT and preference alignment, so data includes
    both the target response and a rejected alternative.
    """
    __tablename__ = "synthetic_data_orpo"
    
    id = Column(Integer, primary_key=True)
    
    # Core ORPO fields (combines SFT + DPO structure)
    system_prompt = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)                # Input prompt
    chosen = Column(Text, nullable=False)                # Target response (for SFT + preference)
    rejected = Column(Text, nullable=False)              # Rejected response (for preference)
    
    # Odds ratio specific
    chosen_logprob = Column(Float, nullable=True)        # Log probability of chosen
    rejected_logprob = Column(Float, nullable=True)      # Log probability of rejected
    odds_ratio = Column(Float, nullable=True)            # Computed odds ratio
    
    # Metadata
    topic = Column(String(255), nullable=True)
    sub_topic = Column(String(255), nullable=True)       # Sub-topic category (e.g., "organic", "analytical", "inorganic")
    task_type = Column(String(100), nullable=True)
    
    # Quality & Source
    source = Column(String(255), nullable=True)
    review_status = Column(String(50), nullable=True)
    
    # Generation metadata
    model_used = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# Chat/Conversation Schema
# Format: Multi-turn conversations for chat fine-tuning
# =============================================================================

class SyntheticDataChat(Base):
    """
    Schema for multi-turn conversation data.
    
    Used for training chat models with multi-turn dialogue history.
    Each row represents a complete conversation.
    """
    __tablename__ = "synthetic_data_chat"
    
    id = Column(Integer, primary_key=True)
    
    # Core chat fields
    conversation_id = Column(String(100), nullable=False) # Groups turns in same conversation
    system_prompt = Column(Text, nullable=True)
    messages = Column(JSON, nullable=False)              # [{"role": "user", "content": "..."}, ...]
    
    # Conversation metadata
    num_turns = Column(Integer, nullable=True)           # Number of turns
    topic = Column(String(255), nullable=True)
    sub_topic = Column(String(255), nullable=True)       # Sub-topic category (e.g., "organic", "analytical", "inorganic")
    persona = Column(String(255), nullable=True)         # AI persona if any
    
    # Quality & Source
    source = Column(String(255), nullable=True)
    quality_score = Column(Float, nullable=True)
    review_status = Column(String(50), nullable=True)
    
    # Generation metadata
    model_used = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# QA (Question-Answer) Schema
# Format: Question-answer pairs with optional reasoning
# =============================================================================

class SyntheticDataQA(Base):
    """
    Schema for Question-Answer data.
    
    General-purpose Q&A format that can be converted to other formats.
    Includes reasoning chain for chain-of-thought training.
    """
    __tablename__ = "synthetic_data_qa"
    
    id = Column(Integer, primary_key=True)
    
    # Core QA fields
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)              # Step-by-step reasoning
    
    # Context and sources
    context = Column(Text, nullable=True)                # Reference context if any
    source = Column(String(255), nullable=True)
    source_url = Column(String(500), nullable=True)
    
    # Categorization
    topic = Column(String(255), nullable=True)
    sub_topic = Column(String(255), nullable=True)       # Sub-topic category (e.g., "organic", "analytical", "inorganic")
    question_type = Column(String(100), nullable=True)   # "factual", "reasoning", "opinion"
    difficulty = Column(String(50), nullable=True)
    
    # Quality
    quality_score = Column(Float, nullable=True)
    review_status = Column(String(50), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    
    # Generation metadata
    model_used = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# Questions Schema
# Format: Questions to be researched and answered for synthetic data generation
# =============================================================================

class Questions(Base):
    """
    Schema for storing questions that need to be researched and answered.
    
    These questions are generated by the question agent and used by research
    agents to gather domain knowledge for synthetic data generation.
    """
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True)
    
    # Core fields
    question = Column(Text, nullable=False)                # The question text
    topic = Column(String(255), nullable=False)           # Main topic (e.g., "chemistry", "mathematics")
    sub_topic = Column(String(255), nullable=False)       # Sub-topic (e.g., "organic", "analytical", "inorganic")
    
    # Status tracking
    status = Column(String(50), default="pending")        # "pending", "researching", "answered", "skipped"
    answered_at = Column(DateTime, nullable=True)         # When the question was answered
    
    # Research metadata
    research_agent_id = Column(String(100), nullable=True) # Which agent is researching this
    answer = Column(Text, nullable=True)                   # The answer/research findings
    
    # Generation metadata
    training_type = Column(String(50), nullable=True)      # Which training type this question relates to
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# =============================================================================
# Schema Registry - Maps training types to their schemas
# =============================================================================

SCHEMA_REGISTRY = {
    TrainingType.SFT: SyntheticDataSFT,
    TrainingType.DPO: SyntheticDataDPO,
    TrainingType.PPO: SyntheticDataPPO,
    TrainingType.GRPO: SyntheticDataGRPO,
    TrainingType.RLHF: SyntheticDataRLHF,
    TrainingType.KTO: SyntheticDataKTO,
    TrainingType.ORPO: SyntheticDataORPO,
    TrainingType.CHAT: SyntheticDataChat,
    TrainingType.QA: SyntheticDataQA,
}

# Questions table (not tied to a specific training type)
QUESTIONS_TABLE = Questions


def get_schema_for_training_type(training_type: TrainingType):
    """
    Returns the appropriate schema class for the given training type.
    
    Args:
        training_type: The TrainingType enum value
        
    Returns:
        The SQLAlchemy model class for that training type
        
    Example:
        >>> schema = get_schema_for_training_type(TrainingType.DPO)
        >>> schema.__tablename__
        'synthetic_data_dpo'
    """
    return SCHEMA_REGISTRY.get(training_type)


def get_table_name_for_training_type(training_type: TrainingType) -> str:
    """Returns the database table name for a training type."""
    schema = get_schema_for_training_type(training_type)
    return schema.__tablename__ if schema else None


# Description mapping for agent to understand each technique
TRAINING_TYPE_DESCRIPTIONS = {
    TrainingType.SFT: "Supervised Fine-Tuning - Train on instruction-response pairs to teach the model to follow instructions",
    TrainingType.DPO: "Direct Preference Optimization - Train on preference pairs (chosen vs rejected) without a reward model",
    TrainingType.PPO: "Proximal Policy Optimization - Reinforcement learning with reward signals from a reward model",
    TrainingType.GRPO: "Group Relative Policy Optimization - Compare multiple responses for same prompt, good for reasoning/math/code",
    TrainingType.RLHF: "Reinforcement Learning from Human Feedback - Train reward models from human preference data",
    TrainingType.KTO: "Kahneman-Tversky Optimization - Binary feedback (good/bad) without needing preference pairs",
    TrainingType.ORPO: "Odds Ratio Preference Optimization - Combines SFT and preference alignment in one training phase",
    TrainingType.CHAT: "Multi-turn conversation data for training chat/dialogue models",
    TrainingType.QA: "Question-Answer pairs with optional reasoning chains",
}
```

## src\orchestrator\__init__.py

```python
from .agent import root_agent

__all__ = ["root_agent"]
```

## src\orchestrator\agent.py

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "orchestrator.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps.app import App, ResumabilityConfig

from .planning_agent import root_agent as planning_agent


root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config),
    sub_agents=[planning_agent]
)

```

## src\orchestrator\database_agent\__init__.py

```python
from .agent import root_agent

__all__ = ["root_agent"]
```

## src\orchestrator\database_agent\agent.py

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "database.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps.app import App, ResumabilityConfig

from tools.database_tools import DatabaseTools

database_tools = DatabaseTools()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config),
    tools=[database_tools],
)
```

## src\orchestrator\planning_agent\__init__.py

```python
from .agent import root_agent

__all__ = ["root_agent"]
```

## src\orchestrator\planning_agent\agent.py

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config
from models.models import PlanningResponse

config = load_config(Path(__file__).parent / "planning.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps.app import App, ResumabilityConfig


root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config),
    output_key="planning_response",
)
```

## src\orchestrator\question_agent\__init__.py

```python
from .agent import root_agent

__all__ = ["root_agent"]
```

## src\orchestrator\question_agent\agent.py

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config
from models.models import Questions

config = load_config(Path(__file__).parent / "questions.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps.app import App, ResumabilityConfig


root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config),
    output_schema=Questions,
)
```

## src\orchestrator\research_agent\__init__.py

```python
from .agent import root_agent

__all__ = ["root_agent"]
```

## src\orchestrator\research_agent\agent.py

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "research.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from tools.web_tools import WebTools
from tools.database_tools import DatabaseTools

# Initialize tools
web_tools = WebTools()
database_tools = DatabaseTools()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config),
    tools=[web_tools, database_tools],
)

```

## src\orchestrator\reviewer_agent\__init__.py

```python
from .agent import root_agent

__all__ = ["root_agent"]
```

## src\orchestrator\reviewer_agent\agent.py

```python

```

## tools\data_tools.py

```python
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from io import StringIO

sys.path.append(str(Path(__file__).parent.parent))

from google.adk.tools import Tool

class DataAnalysisTools(Tool):
    """
    Tools for analyzing and summarizing synthetic data.
    
    Provides methods for statistical analysis, quality assessment,
    and data profiling of synthetic datasets.
    """
    
    def __init__(self):
        super().__init__(
            name="data_analysis_tools",
            description="Tools for analyzing and summarizing synthetic data, including statistical summaries, quality metrics, and data profiling",
        )

    def analyze_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the data and return a comprehensive summary.
        
        Args:
            data: The DataFrame to analyze
            
        Returns:
            Dictionary containing summary statistics, data info, missing values, and data types
        """
        # Capture info() output as string
        buffer = StringIO()
        data.info(buf=buffer)
        info_str = buffer.getvalue()
        
        return {
            "row_count": len(data),
            "column_count": len(data.columns),
            "summary": data.describe().to_dict() if len(data.select_dtypes(include=[np.number]).columns) > 0 else {},
            "head": data.head().to_dict('records'),
            "info": info_str,
            "missing_values": data.isnull().sum().to_dict(),
            "missing_percentage": (data.isnull().sum() / len(data) * 100).to_dict(),
            "data_types": {col: str(dtype) for col, dtype in data.dtypes.items()},
            "columns": list(data.columns),
        }
    
    def analyze_synthetic_data_quality(
        self, 
        data: pd.DataFrame, 
        topic_column: Optional[str] = "topic",
        sub_topic_column: Optional[str] = "sub_topic"
    ) -> Dict[str, Any]:
        """
        Analyze quality metrics specific to synthetic data generation.
        
        Args:
            data: The DataFrame containing synthetic data
            topic_column: Name of the topic column (default: "topic")
            sub_topic_column: Name of the sub_topic column (default: "sub_topic")
            
        Returns:
            Dictionary with quality metrics including diversity, coverage, and distribution
        """
        quality_metrics = {
            "total_records": len(data),
        }
        
        # Topic and sub-topic distribution
        if topic_column and topic_column in data.columns:
            topic_counts = data[topic_column].value_counts().to_dict()
            quality_metrics["topic_distribution"] = topic_counts
            quality_metrics["unique_topics"] = data[topic_column].nunique()
        
        if sub_topic_column and sub_topic_column in data.columns:
            sub_topic_counts = data[sub_topic_column].value_counts().to_dict()
            quality_metrics["sub_topic_distribution"] = sub_topic_counts
            quality_metrics["unique_sub_topics"] = data[sub_topic_column].nunique()
        
        # Difficulty distribution (if present)
        if "difficulty" in data.columns:
            difficulty_counts = data["difficulty"].value_counts().to_dict()
            quality_metrics["difficulty_distribution"] = difficulty_counts
        
        # Quality score analysis (if present)
        if "quality_score" in data.columns:
            quality_metrics["quality_score_stats"] = {
                "mean": float(data["quality_score"].mean()) if not data["quality_score"].isna().all() else None,
                "median": float(data["quality_score"].median()) if not data["quality_score"].isna().all() else None,
                "min": float(data["quality_score"].min()) if not data["quality_score"].isna().all() else None,
                "max": float(data["quality_score"].max()) if not data["quality_score"].isna().all() else None,
                "std": float(data["quality_score"].std()) if not data["quality_score"].isna().all() else None,
            }
        
        # Review status (if present)
        if "review_status" in data.columns:
            review_counts = data["review_status"].value_counts().to_dict()
            quality_metrics["review_status_distribution"] = review_counts
        
        return quality_metrics
    
    def get_text_statistics(
        self, 
        data: pd.DataFrame, 
        text_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze text statistics for text columns in the dataset.
        
        Useful for analyzing instruction, response, prompt, and other text fields.
        
        Args:
            data: The DataFrame to analyze
            text_columns: List of column names to analyze. If None, auto-detects text columns.
            
        Returns:
            Dictionary with text statistics (length, word count, etc.)
        """
        if text_columns is None:
            # Auto-detect text columns (object/string type columns)
            text_columns = [col for col in data.columns if data[col].dtype == 'object']
        
        text_stats = {}
        
        for col in text_columns:
            if col not in data.columns:
                continue
                
            # Convert to string and remove NaN
            text_series = data[col].astype(str).replace('nan', np.nan).dropna()
            
            if len(text_series) == 0:
                text_stats[col] = {"error": "No valid text data"}
                continue
            
            # Calculate statistics
            char_lengths = text_series.str.len()
            word_counts = text_series.str.split().str.len()
            
            text_stats[col] = {
                "mean_char_length": float(char_lengths.mean()),
                "median_char_length": float(char_lengths.median()),
                "min_char_length": int(char_lengths.min()),
                "max_char_length": int(char_lengths.max()),
                "mean_word_count": float(word_counts.mean()),
                "median_word_count": float(word_counts.median()),
                "min_word_count": int(word_counts.min()),
                "max_word_count": int(word_counts.max()),
                "non_empty_count": int((text_series != '').sum()),
                "empty_count": int((text_series == '').sum()),
            }
        
        return text_stats
    
    def compare_datasets(
        self, 
        dataset1: pd.DataFrame, 
        dataset2: pd.DataFrame,
        key_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare two datasets to identify differences and similarities.
        
        Useful for comparing synthetic data against reference data or
        comparing different versions of synthetic data.
        
        Args:
            dataset1: First DataFrame to compare
            dataset2: Second DataFrame to compare
            key_columns: Optional list of columns to use for comparison
            
        Returns:
            Dictionary with comparison metrics
        """
        comparison = {
            "dataset1_size": len(dataset1),
            "dataset2_size": len(dataset2),
            "size_difference": len(dataset1) - len(dataset2),
            "common_columns": list(set(dataset1.columns) & set(dataset2.columns)),
            "unique_to_dataset1": list(set(dataset1.columns) - set(dataset2.columns)),
            "unique_to_dataset2": list(set(dataset2.columns) - set(dataset1.columns)),
        }
        
        # Compare column statistics if columns match
        common_cols = comparison["common_columns"]
        if common_cols:
            comparison["column_statistics"] = {}
            for col in common_cols:
                if dataset1[col].dtype == dataset2[col].dtype:
                    if pd.api.types.is_numeric_dtype(dataset1[col]):
                        comparison["column_statistics"][col] = {
                            "dataset1_mean": float(dataset1[col].mean()) if not dataset1[col].isna().all() else None,
                            "dataset2_mean": float(dataset2[col].mean()) if not dataset2[col].isna().all() else None,
                        }
        
        return comparison
```

## tools\database_tools.py

```python
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from google.adk.tools import Tool
from schema.synethtic_data import (
    SCHEMA_REGISTRY, 
    TrainingType, 
    QUESTIONS_TABLE,
    get_schema_for_training_type
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Database connection - adjust connection string as needed
# This should be configured via environment variables or config file
# Database files are stored in the db directory
db_dir = Path(__file__).parent.parent / "db"
db_dir.mkdir(exist_ok=True)  # Ensure db directory exists
DATABASE_URL = f"sqlite:///{db_dir / 'synthetic_data.db'}"  # Default to SQLite, can be changed

# Create engine and session factory
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class DatabaseTools(Tool):
    """
    Database tools for managing synthetic data generation pipeline.
    
    Handles:
    - Storing questions from the question agent
    - Adding synthetic data to appropriate training type tables
    - Querying and managing database records
    """
    
    def __init__(self):
        super().__init__(
            name="database_tools",
            description="Tools for interacting with the synthetic data database. Can add questions, store synthetic data for different training types (SFT, DPO, PPO, GRPO, RLHF, KTO, ORPO, Chat, QA), and query database records.",
            schema=QUESTIONS_TABLE,  # Default schema for questions
        )
        self._session: Optional[Session] = None
    
    def _get_session(self) -> Session:
        """Get or create a database session."""
        if self._session is None:
            self._session = SessionLocal()
        return self._session
    
    def add_questions_to_database(
        self, 
        questions: List[str], 
        topic: str, 
        sub_topic: str,
        training_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add questions to the questions database table.
        
        This method is used by the question agent to store questions that need
        to be researched and answered before generating synthetic data.
        
        Args:
            questions: A list of question strings to add to the database
            topic: The main topic (e.g., "chemistry", "mathematics", "computer science")
            sub_topic: The sub-topic (e.g., "organic", "analytical", "inorganic" for chemistry)
            training_type: Optional training type this question relates to (e.g., "sft", "dpo")
            
        Returns:
            Dictionary with count of questions added and list of question IDs
        """
        session = self._get_session()
        added_ids = []
        
        try:
            for question_text in questions:
                question_record = QUESTIONS_TABLE(
                    question=question_text,
                    topic=topic,
                    sub_topic=sub_topic,
                    training_type=training_type,
                    status="pending"
                )
                session.add(question_record)
                session.flush()  # Get the ID
                added_ids.append(question_record.id)
            
            session.commit()
            return {
                "count": len(added_ids),
                "question_ids": added_ids,
                "topic": topic,
                "sub_topic": sub_topic,
                "status": "success"
            }
        except Exception as e:
            session.rollback()
            return {
                "count": 0,
                "error": str(e),
                "status": "error"
            }
    
    def add_synthetic_data(
        self,
        training_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add synthetic data to the appropriate training type table.
        
        Args:
            training_type: The training type (e.g., "sft", "dpo", "ppo", "grpo", "rlhf", "kto", "orpo", "chat", "qa")
            data: Dictionary containing the data fields for the specific training type schema
            
        Returns:
            Dictionary with the created record ID and status
        """
        session = self._get_session()
        
        try:
            # Get the appropriate schema for the training type
            training_type_enum = TrainingType(training_type.lower())
            schema_class = get_schema_for_training_type(training_type_enum)
            
            if schema_class is None:
                return {
                    "status": "error",
                    "error": f"Unknown training type: {training_type}"
                }
            
            # Create a new record with the provided data
            record = schema_class(**data)
            session.add(record)
            session.flush()
            record_id = record.id
            session.commit()
            
            return {
                "status": "success",
                "id": record_id,
                "training_type": training_type,
                "table": schema_class.__tablename__
            }
        except ValueError as e:
            return {
                "status": "error",
                "error": f"Invalid training type: {training_type}. Valid types: {[t.value for t in TrainingType]}"
            }
        except Exception as e:
            session.rollback()
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_pending_questions(
        self,
        topic: Optional[str] = None,
        sub_topic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending questions from the database.
        
        Args:
            topic: Optional filter by topic
            sub_topic: Optional filter by sub-topic
            
        Returns:
            List of question dictionaries
        """
        session = self._get_session()
        
        try:
            query = session.query(QUESTIONS_TABLE).filter(
                QUESTIONS_TABLE.status == "pending"
            )
            
            if topic:
                query = query.filter(QUESTIONS_TABLE.topic == topic)
            if sub_topic:
                query = query.filter(QUESTIONS_TABLE.sub_topic == sub_topic)
            
            questions = query.all()
            return [
                {
                    "id": q.id,
                    "question": q.question,
                    "topic": q.topic,
                    "sub_topic": q.sub_topic,
                    "status": q.status,
                    "training_type": q.training_type
                }
                for q in questions
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    def update_question_status(
        self,
        question_id: int,
        status: str,
        answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update the status of a question (e.g., mark as answered).
        
        Args:
            question_id: The ID of the question to update
            status: New status ("pending", "researching", "answered", "skipped")
            answer: Optional answer/research findings
            
        Returns:
            Dictionary with update status
        """
        session = self._get_session()
        
        try:
            question = session.query(QUESTIONS_TABLE).filter(
                QUESTIONS_TABLE.id == question_id
            ).first()
            
            if not question:
                return {
                    "status": "error",
                    "error": f"Question with ID {question_id} not found"
                }
            
            question.status = status
            if answer:
                question.answer = answer
            if status == "answered":
                question.answered_at = datetime.utcnow()
            
            session.commit()
            
            return {
                "status": "success",
                "question_id": question_id,
                "new_status": status
            }
        except Exception as e:
            session.rollback()
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_questions_count(
        self,
        topic: Optional[str] = None,
        sub_topic: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get count of questions by filters.
        
        Args:
            topic: Optional filter by topic
            sub_topic: Optional filter by sub-topic
            status: Optional filter by status
            
        Returns:
            Dictionary with counts
        """
        session = self._get_session()
        
        try:
            query = session.query(QUESTIONS_TABLE)
            
            if topic:
                query = query.filter(QUESTIONS_TABLE.topic == topic)
            if sub_topic:
                query = query.filter(QUESTIONS_TABLE.sub_topic == sub_topic)
            if status:
                query = query.filter(QUESTIONS_TABLE.status == status)
            
            count = query.count()
            return {
                "count": count,
                "topic": topic,
                "sub_topic": sub_topic,
                "status": status
            }
        except Exception as e:
            return {
                "count": 0,
                "error": str(e)
            }
```

## tools\web_tools.py

```python
"""
Web Tools for Research Agent

Provides web search and content fetching capabilities for researching
domain knowledge to support synthetic data generation.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import re

sys.path.append(str(Path(__file__).parent.parent))

from google.adk.tools import Tool

# Try to import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class WebTools(Tool):
    """
    Web tools for conducting research and gathering domain knowledge.
    
    Provides:
    - Web search functionality
    - URL content fetching
    - Content extraction and summarization
    """
    
    def __init__(self):
        super().__init__(
            name="web_tools",
            description="Tools for web research including search, URL fetching, and content extraction to gather domain knowledge for synthetic data generation",
        )
        self._session = None
    
    def _get_session(self):
        """Get or create a requests session."""
        if not REQUESTS_AVAILABLE:
            return None
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
        return self._session
    
    def web_search(
        self, 
        query: str, 
        num_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search the web for information on a given query.
        
        This uses Google's Programmable Search Engine or falls back to
        a simpler approach if API keys are not configured.
        
        Args:
            query: The search query string
            num_results: Maximum number of results to return (default: 5)
            
        Returns:
            Dictionary containing search results with titles, snippets, and URLs
        """
        if not REQUESTS_AVAILABLE:
            return {
                "status": "error",
                "error": "requests library not installed. Run: pip install requests",
                "query": query
            }
        
        # For now, return a structured response indicating search capability
        # In production, this would integrate with Google Custom Search API,
        # Bing Search API, or similar service
        return {
            "status": "success",
            "query": query,
            "num_results": num_results,
            "message": "Web search executed. Use your knowledge to answer this query.",
            "search_suggestions": [
                f"Research: {query}",
                f"Look for authoritative sources on: {query}",
                f"Find examples and documentation for: {query}"
            ],
            "note": "For production use, integrate with Google Custom Search API, Bing Search API, or SerpAPI"
        }
    
    def fetch_url(
        self, 
        url: str,
        extract_text: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch content from a URL and optionally extract text.
        
        Args:
            url: The URL to fetch content from
            extract_text: Whether to extract clean text from HTML (default: True)
            
        Returns:
            Dictionary containing the fetched content, status, and metadata
        """
        if not REQUESTS_AVAILABLE:
            return {
                "status": "error",
                "error": "requests library not installed. Run: pip install requests",
                "url": url
            }
        
        session = self._get_session()
        
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '')
            
            result = {
                "status": "success",
                "url": url,
                "status_code": response.status_code,
                "content_type": content_type,
            }
            
            # Handle different content types
            if 'text/html' in content_type:
                if extract_text and BS4_AVAILABLE:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    
                    # Get text
                    text = soup.get_text(separator='\n', strip=True)
                    
                    # Clean up whitespace
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    text = '\n'.join(lines)
                    
                    # Truncate if too long
                    max_length = 10000
                    if len(text) > max_length:
                        text = text[:max_length] + "\n\n[Content truncated...]"
                    
                    result["content"] = text
                    result["title"] = soup.title.string if soup.title else None
                else:
                    result["content"] = response.text[:10000]
                    result["note"] = "Raw HTML (beautifulsoup4 not installed for text extraction)"
                    
            elif 'application/json' in content_type:
                result["content"] = response.json()
                
            elif 'text/' in content_type:
                result["content"] = response.text[:10000]
                
            else:
                result["content"] = f"Binary content ({content_type})"
                result["content_length"] = len(response.content)
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": "Request timed out",
                "url": url
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }
    
    def search_documentation(
        self,
        topic: str,
        sub_topic: Optional[str] = None,
        doc_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Search for documentation on a specific topic.
        
        Constructs targeted search queries for finding authoritative
        documentation sources.
        
        Args:
            topic: Main topic to search for
            sub_topic: Optional sub-topic for more specific search
            doc_type: Type of documentation ("general", "api", "tutorial", "reference")
            
        Returns:
            Dictionary with search query suggestions and documentation sources
        """
        # Build search query
        query_parts = [topic]
        if sub_topic:
            query_parts.append(sub_topic)
        
        # Add doc type qualifiers
        doc_qualifiers = {
            "general": ["documentation", "guide"],
            "api": ["API documentation", "API reference"],
            "tutorial": ["tutorial", "getting started", "how to"],
            "reference": ["reference manual", "specification"]
        }
        
        qualifiers = doc_qualifiers.get(doc_type, doc_qualifiers["general"])
        
        # Generate search queries
        search_queries = [
            f"{' '.join(query_parts)} {q}" for q in qualifiers
        ]
        
        # Common documentation sources
        doc_sources = {
            "chemistry": [
                "https://www.rsc.org/",
                "https://pubchem.ncbi.nlm.nih.gov/",
                "https://www.chemguide.co.uk/"
            ],
            "mathematics": [
                "https://mathworld.wolfram.com/",
                "https://www.khanacademy.org/math",
                "https://www.mathsisfun.com/"
            ],
            "computer science": [
                "https://developer.mozilla.org/",
                "https://docs.python.org/",
                "https://www.geeksforgeeks.org/"
            ],
            "physics": [
                "https://www.physics.org/",
                "https://hyperphysics.phy-astr.gsu.edu/",
                "https://www.feynmanlectures.caltech.edu/"
            ]
        }
        
        # Find relevant sources
        relevant_sources = doc_sources.get(topic.lower(), [])
        
        return {
            "status": "success",
            "topic": topic,
            "sub_topic": sub_topic,
            "doc_type": doc_type,
            "suggested_queries": search_queries,
            "relevant_sources": relevant_sources,
            "recommendation": f"Search for '{search_queries[0]}' or browse the relevant sources listed"
        }
    
    def extract_key_information(
        self,
        content: str,
        extraction_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Extract key information from content.
        
        Analyzes text content to extract structured information
        like definitions, examples, and key points.
        
        Args:
            content: Text content to analyze
            extraction_type: Type of extraction ("definitions", "examples", "steps", "general")
            
        Returns:
            Dictionary with extracted information
        """
        if not content:
            return {
                "status": "error",
                "error": "No content provided"
            }
        
        result = {
            "status": "success",
            "extraction_type": extraction_type,
            "content_length": len(content),
        }
        
        # Basic extraction patterns
        if extraction_type == "definitions":
            # Look for definition patterns
            patterns = [
                r"(?:is defined as|means|refers to|is)\s+(.+?)(?:\.|$)",
                r"(?:Definition|DEFINITION):\s*(.+?)(?:\n|$)"
            ]
            definitions = []
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                definitions.extend(matches[:5])  # Limit to 5 per pattern
            result["definitions"] = definitions
            
        elif extraction_type == "examples":
            # Look for example patterns
            patterns = [
                r"(?:for example|e\.g\.|such as|like)\s+(.+?)(?:\.|$)",
                r"(?:Example|EXAMPLE):\s*(.+?)(?:\n|$)"
            ]
            examples = []
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                examples.extend(matches[:5])
            result["examples"] = examples
            
        elif extraction_type == "steps":
            # Look for numbered steps
            patterns = [
                r"(?:\d+\.|Step \d+:?)\s*(.+?)(?:\n|$)"
            ]
            steps = []
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                steps.extend(matches[:10])
            result["steps"] = steps
            
        else:  # general
            # Extract key sentences (first sentence of paragraphs)
            paragraphs = content.split('\n\n')
            key_points = []
            for para in paragraphs[:10]:
                sentences = para.split('.')
                if sentences and sentences[0].strip():
                    key_points.append(sentences[0].strip())
            result["key_points"] = key_points
        
        return result
    
    def summarize_for_data_generation(
        self,
        topic: str,
        sub_topic: str,
        research_findings: List[str]
    ) -> Dict[str, Any]:
        """
        Summarize research findings for synthetic data generation.
        
        Organizes research findings into a structured format optimized
        for informing synthetic data generation.
        
        Args:
            topic: Main topic
            sub_topic: Sub-topic
            research_findings: List of research findings/answers
            
        Returns:
            Dictionary with organized summary for data generation
        """
        if not research_findings:
            return {
                "status": "error",
                "error": "No research findings provided"
            }
        
        # Combine all findings
        combined_text = "\n\n".join(research_findings)
        
        # Basic categorization
        summary = {
            "status": "success",
            "topic": topic,
            "sub_topic": sub_topic,
            "total_findings": len(research_findings),
            "combined_length": len(combined_text),
            "categories": {
                "definitions": [],
                "examples": [],
                "patterns": [],
                "constraints": [],
                "quality_criteria": []
            },
            "data_generation_guidance": {
                "key_concepts": f"Based on research for {topic}/{sub_topic}",
                "suggested_formats": "Use findings to inform instruction/response formats",
                "quality_standards": "Ensure generated data aligns with domain conventions"
            }
        }
        
        # Categorize findings by keywords
        for finding in research_findings:
            finding_lower = finding.lower()
            if any(kw in finding_lower for kw in ["definition", "means", "is defined"]):
                summary["categories"]["definitions"].append(finding[:200])
            elif any(kw in finding_lower for kw in ["example", "such as", "for instance"]):
                summary["categories"]["examples"].append(finding[:200])
            elif any(kw in finding_lower for kw in ["pattern", "typically", "usually", "common"]):
                summary["categories"]["patterns"].append(finding[:200])
            elif any(kw in finding_lower for kw in ["must", "should", "constraint", "rule", "require"]):
                summary["categories"]["constraints"].append(finding[:200])
            elif any(kw in finding_lower for kw in ["quality", "valid", "correct", "accurate"]):
                summary["categories"]["quality_criteria"].append(finding[:200])
        
        return summary
```

## utils\config.py

```python
import yaml
from google.genai import types

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def retry_config():
    return types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)
```

