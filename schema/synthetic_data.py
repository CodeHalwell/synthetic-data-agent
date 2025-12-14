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
    
    The table stores structured artifacts at each pipeline stage:
    - Task spec: What we're trying to generate (training type, constraints, format)
    - Evidence: Grounding inputs with provenance
    - Reference solution: Gold answer with acceptance criteria
    - Review: Validation results and decisions
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
    
    # Artifact fields (structured JSON blobs for pipeline stages)
    task_spec = Column(JSON, nullable=True)
    """Task specification: training type, output constraints, format requirements, difficulty"""
    
    evidence = Column(JSON, nullable=True)
    """Evidence pack: list of items with provenance (source, content, relevance)"""
    
    reference_solution = Column(JSON, nullable=True)
    """Gold answer with acceptance criteria (final_answer, answer_type, parsing_rules, tests)"""
    
    review = Column(JSON, nullable=True)
    """Review results: scores, decisions, feedback, status"""
    
    # Context fields (research outputs)
    ground_truth_context = Column(Text, nullable=True)
    """Raw, word-for-word text from authoritative sources"""
    
    synthesized_context = Column(Text, nullable=True)
    """LLM-cleaned and structured version (JSON or formatted text)"""
    
    context_sources = Column(JSON, nullable=True)
    """JSON array: [{"url": "...", "title": "...", "license": "...", "fetched_at": "..."}]"""
    
    context_quality_score = Column(Float, nullable=True)
    """Quality score of research context (0-1)"""
    
    # Pipeline stage tracking (granular status)
    pipeline_stage = Column(String(50), default="pending")
    """Granular stage: pending → researching → ready_for_generation → generated → reviewed"""
    
    # Research metadata
    research_agent_id = Column(String(100), nullable=True) # Which agent is researching this
    research_completed_at = Column(DateTime, nullable=True) # When research was completed
    answer = Column(Text, nullable=True)                   # The answer/research findings (legacy field)
    
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
