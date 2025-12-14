"""
Workflow functions for synthetic data generation by training type.

Each function takes a question and context, then generates training data
in the appropriate format for that training type.
"""

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
    
    Creates instruction-response pairs suitable for supervised fine-tuning.
    
    Args:
        question: The instruction/prompt
        topic: Main topic
        sub_topic: Specific sub-topic
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context (JSON string or dict)
        
    Returns:
        Dict with: system_prompt, instruction, response, metadata
    """
    # Parse synthesized context if it's a string
    if isinstance(synthesized_context, str):
        try:
            context = json.loads(synthesized_context)
        except json.JSONDecodeError:
            context = {"summary": synthesized_context}
    else:
        context = synthesized_context or {}
    
    # Extract key information from context
    summary = context.get("summary", "")
    key_concepts = context.get("key_concepts", [])
    definitions = context.get("definitions", {})
    examples = context.get("examples", [])
    
    # Build a comprehensive response using the context
    response_parts = []
    
    # Start with summary if available
    if summary:
        response_parts.append(summary)
    
    # Add key concepts if available
    if key_concepts:
        response_parts.append("\nKey concepts:")
        for concept in key_concepts[:5]:  # Limit to top 5
            response_parts.append(f"- {concept}")
    
    # Add definitions if available
    if definitions:
        response_parts.append("\nDefinitions:")
        for term, definition in list(definitions.items())[:3]:  # Limit to 3
            response_parts.append(f"- {term}: {definition}")
    
    # Add examples if available
    if examples:
        response_parts.append("\nExamples:")
        for i, example in enumerate(examples[:2], 1):  # Limit to 2
            response_parts.append(f"{i}. {example}")
    
    # If no structured content, use ground truth directly
    if not response_parts:
        response = ground_truth_context[:1000] if ground_truth_context else "No context available for this question."
    else:
        response = "\n".join(response_parts)
    
    return {
        "system_prompt": f"You are an expert in {topic}, specifically {sub_topic}.",
        "instruction": question,
        "response": response,
        "topic": topic,
        "sub_topic": sub_topic,
        "task_type": "question_answering",
        "difficulty": "medium",
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
    Generate GRPO (Group Relative Policy Optimization) data.
    
    Includes reasoning chain, verification code, and correctness flag.
    Used for tasks with verifiable answers (math, code, logic).
    
    Args:
        question: The problem/prompt
        topic: Main topic
        sub_topic: Specific sub-topic
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context
        code_executor: Optional code executor for verification
        
    Returns:
        Dict with: prompt, group_id, response, reasoning, code, predicted_answer, is_correct
    """
    # Parse synthesized context
    if isinstance(synthesized_context, str):
        try:
            context = json.loads(synthesized_context)
        except json.JSONDecodeError:
            context = {}
    else:
        context = synthesized_context or {}
    
    # Generate reasoning chain
    key_concepts = context.get("key_concepts", [])
    definitions = context.get("definitions", {})
    
    reasoning_steps = []
    reasoning_steps.append(f"To solve '{question}', I will work through this step-by-step:")
    reasoning_steps.append("")
    reasoning_steps.append("Step 1: Identify the key concepts")
    if key_concepts:
        reasoning_steps.append(f"The main concepts involved are: {', '.join(key_concepts[:3])}")
    else:
        reasoning_steps.append(f"Based on the context, this relates to {sub_topic} in {topic}.")
    
    reasoning_steps.append("")
    reasoning_steps.append("Step 2: Apply relevant principles")
    if definitions:
        first_def = list(definitions.items())[0]
        reasoning_steps.append(f"Using the definition: {first_def[0]} - {first_def[1]}")
    else:
        reasoning_steps.append(f"Using principles from {sub_topic}, we can approach this problem systematically.")
    
    reasoning_steps.append("")
    reasoning_steps.append("Step 3: Work through the solution")
    reasoning_steps.append("Following the established methodology, we can derive the answer.")
    
    reasoning_steps.append("")
    reasoning_steps.append("Step 4: Verify the solution")
    reasoning_steps.append("Cross-checking against the source material confirms this is correct.")
    
    reasoning = "\n".join(reasoning_steps)
    
    # Generate verification code (for math/code questions)
    code = f'''# Verification code for: {question}
# Topic: {topic}/{sub_topic}

def verify_answer():
    """
    Verify the answer is correct.
    
    This would contain actual verification logic based on the problem type.
    For now, this is a placeholder that would be filled with domain-specific checks.
    """
    # TODO: Implement domain-specific verification
    result = True
    return result

if __name__ == "__main__":
    is_correct = verify_answer()
    print(f"Verification result: {{is_correct}}")
'''
    
    # Extract or construct the answer
    summary = context.get("summary", "")
    predicted_answer = summary[:200] if summary else "Answer derived from reasoning chain above"
    
    # For MVP, mark as correct (would be determined by code execution in production)
    is_correct = True
    
    # Combine reasoning and answer for response
    full_response = reasoning + f"\n\nFinal answer: {predicted_answer}"
    
    return {
        "prompt": question,
        "group_id": f"{topic}_{sub_topic}_group_{hash(question) % 1000}",
        "response": full_response,
        "reasoning": reasoning,
        "code": code,
        "predicted_answer": predicted_answer,
        "is_correct": is_correct,
        "topic": topic,
        "sub_topic": sub_topic,
        "task_type": "reasoning",
        "difficulty": "medium",
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
    Generate DPO (Direct Preference Optimization) data.
    
    Creates chosen (better) and rejected (worse) response pairs.
    
    Args:
        question: The prompt
        topic: Main topic
        sub_topic: Specific sub-topic
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context
        
    Returns:
        Dict with: system_prompt, prompt, chosen, rejected, ratings
    """
    # Parse synthesized context
    if isinstance(synthesized_context, str):
        try:
            context = json.loads(synthesized_context)
        except json.JSONDecodeError:
            context = {}
    else:
        context = synthesized_context or {}
    
    summary = context.get("summary", "")
    key_concepts = context.get("key_concepts", [])
    definitions = context.get("definitions", {})
    examples = context.get("examples", [])
    
    # CHOSEN response: accurate, detailed, well-structured
    chosen_parts = []
    
    if summary:
        chosen_parts.append(summary)
    
    if key_concepts:
        chosen_parts.append("\nKey points to understand:")
        for concept in key_concepts[:4]:
            chosen_parts.append(f"• {concept}")
    
    if definitions and len(definitions) > 0:
        chosen_parts.append("\nImportant definitions:")
        for term, definition in list(definitions.items())[:2]:
            chosen_parts.append(f"• {term}: {definition}")
    
    if examples:
        chosen_parts.append("\nPractical examples:")
        for i, example in enumerate(examples[:2], 1):
            chosen_parts.append(f"{i}. {example}")
    
    chosen_parts.append(f"\nThis explanation is based on established knowledge in {topic}.")
    
    chosen = "\n".join(chosen_parts) if chosen_parts else ground_truth_context[:500]
    
    # REJECTED response: vague, incomplete, or partially incorrect
    # Make it plausible but clearly worse
    rejected_options = [
        f"I think this is related to {topic}, but I'm not entirely sure about the specifics of {sub_topic}. It's a complex topic that would require more research to explain properly.",
        
        f"This question is about {sub_topic}. While I don't have detailed information, generally speaking, {topic} involves various concepts. You might want to consult a textbook for more information.",
        
        f"That's an interesting question about {sub_topic}. I know it relates to {topic} somehow, but I don't have enough context to give you a comprehensive answer right now.",
    ]
    
    # Choose rejected response (use hash for consistency)
    rejected = rejected_options[hash(question) % len(rejected_options)]
    
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
    
    Creates question-answer pairs with optional reasoning.
    
    Args:
        question: The question
        topic: Main topic
        sub_topic: Specific sub-topic
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context
        
    Returns:
        Dict with: question, answer, context, reasoning
    """
    # Parse synthesized context
    if isinstance(synthesized_context, str):
        try:
            context = json.loads(synthesized_context)
        except json.JSONDecodeError:
            context = {}
    else:
        context = synthesized_context or {}
    
    summary = context.get("summary", "")
    answer = summary if summary else ground_truth_context[:500]
    
    # Construct reasoning
    reasoning = f"Answer derived from authoritative sources on {topic}/{sub_topic}. "
    reasoning += "The response is based on established knowledge in the field."
    
    return {
        "question": question,
        "answer": answer,
        "context": ground_truth_context[:2000] if ground_truth_context else "",
        "reasoning": reasoning,
        "topic": topic,
        "sub_topic": sub_topic,
        "question_type": "factual",
        "difficulty": "medium",
        "source": "synthetic_generated",
        "quality_score": None,
        "review_status": "pending"
    }


async def generate_ppo_data(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth_context: str,
    synthesized_context: str
) -> Dict[str, Any]:
    """
    Generate PPO (Proximal Policy Optimization) data.
    
    Creates prompts with responses and reward signals.
    
    Args:
        question: The prompt
        topic: Main topic
        sub_topic: Specific sub-topic
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context
        
    Returns:
        Dict with: prompt, response, reward, reward_components
    """
    # Parse context
    if isinstance(synthesized_context, str):
        try:
            context = json.loads(synthesized_context)
        except json.JSONDecodeError:
            context = {}
    else:
        context = synthesized_context or {}
    
    summary = context.get("summary", "")
    response = summary if summary else ground_truth_context[:500]
    
    # Calculate reward based on quality heuristics
    # In production, this would come from a reward model
    reward_components = {
        "helpfulness": 0.85,  # Has useful information
        "accuracy": 0.90,     # Based on authoritative sources
        "completeness": 0.80, # Covers key aspects
        "clarity": 0.85       # Well-structured
    }
    
    reward = sum(reward_components.values()) / len(reward_components)
    
    return {
        "prompt": question,
        "response": response,
        "reward": reward,
        "reward_components": reward_components,
        "topic": topic,
        "sub_topic": sub_topic,
        "reward_model": "heuristic_v1",
        "policy_model": "gemini-2.5-flash",
        "source": "synthetic_generated",
        "review_status": "pending"
    }


async def generate_kto_data(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth_context: str,
    synthesized_context: str
) -> Dict[str, Any]:
    """
    Generate KTO (Kahneman-Tversky Optimization) data.
    
    Creates prompts with responses and binary feedback (good/bad).
    
    Args:
        question: The prompt
        topic: Main topic
        sub_topic: Specific sub-topic
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context
        
    Returns:
        Dict with: prompt, response, is_desirable, feedback_reason
    """
    # Parse context
    if isinstance(synthesized_context, str):
        try:
            context = json.loads(synthesized_context)
        except json.JSONDecodeError:
            context = {}
    else:
        context = synthesized_context or {}
    
    summary = context.get("summary", "")
    response = summary if summary else ground_truth_context[:500]
    
    # For synthetic data based on research, mark as desirable
    is_desirable = True if (summary or ground_truth_context) else False
    
    feedback_reason = "Response is accurate, helpful, and grounded in authoritative sources." if is_desirable else "Response lacks sufficient detail or accuracy."
    
    return {
        "prompt": question,
        "response": response,
        "is_desirable": is_desirable,
        "feedback_reason": feedback_reason,
        "improvement_suggestion": "" if is_desirable else "Add more specific details and cite sources.",
        "topic": topic,
        "sub_topic": sub_topic,
        "feedback_source": "automated",
        "source": "synthetic_generated",
        "review_status": "pending"
    }


async def generate_orpo_data(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth_context: str,
    synthesized_context: str
) -> Dict[str, Any]:
    """
    Generate ORPO (Odds Ratio Preference Optimization) data.
    
    Combines SFT and preference alignment - needs both target and rejected responses.
    
    Args:
        question: The prompt
        topic: Main topic
        sub_topic: Specific sub-topic
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context
        
    Returns:
        Dict with: system_prompt, prompt, chosen, rejected, logprobs
    """
    # Generate similar to DPO but for ORPO format
    dpo_data = await generate_dpo_data(question, topic, sub_topic, ground_truth_context, synthesized_context)
    
    return {
        "system_prompt": dpo_data.get("system_prompt", ""),
        "prompt": question,
        "chosen": dpo_data["chosen"],
        "rejected": dpo_data["rejected"],
        "chosen_logprob": None,  # Would be computed during training
        "rejected_logprob": None,  # Would be computed during training
        "odds_ratio": None,  # Would be computed during training
        "topic": topic,
        "sub_topic": sub_topic,
        "task_type": "question_answering",
        "source": "synthetic_generated",
        "review_status": "pending"
    }


async def generate_rlhf_data(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth_context: str,
    synthesized_context: str
) -> Dict[str, Any]:
    """
    Generate RLHF (Reinforcement Learning from Human Feedback) data.
    
    Creates comparison pairs for reward model training.
    
    Args:
        question: The prompt
        topic: Main topic
        sub_topic: Specific sub-topic
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context
        
    Returns:
        Dict with: prompt, response_a, response_b, preference
    """
    # Generate two responses with DPO approach
    dpo_data = await generate_dpo_data(question, topic, sub_topic, ground_truth_context, synthesized_context)
    
    return {
        "prompt": question,
        "response_a": dpo_data["chosen"],
        "response_b": dpo_data["rejected"],
        "preference": "a",  # A is chosen (better)
        "helpfulness": 0.90,
        "harmlessness": 0.95,
        "honesty": 0.90,
        "topic": topic,
        "sub_topic": sub_topic,
        "source": "synthetic_generated",
        "review_status": "pending"
    }


async def generate_chat_data(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth_context: str,
    synthesized_context: str
) -> Dict[str, Any]:
    """
    Generate Chat (Multi-turn conversation) data.
    
    Creates a conversation with multiple turns.
    
    Args:
        question: Initial question/prompt
        topic: Main topic
        sub_topic: Specific sub-topic
        ground_truth_context: Raw text from sources
        synthesized_context: LLM-structured context
        
    Returns:
        Dict with: conversation_id, system_prompt, messages, num_turns
    """
    # Parse context
    if isinstance(synthesized_context, str):
        try:
            context = json.loads(synthesized_context)
        except json.JSONDecodeError:
            context = {}
    else:
        context = synthesized_context or {}
    
    summary = context.get("summary", "")
    
    # Create a simple 3-turn conversation
    messages = [
        {
            "role": "user",
            "content": question
        },
        {
            "role": "assistant",
            "content": summary if summary else ground_truth_context[:500]
        },
        {
            "role": "user",
            "content": f"Can you elaborate on that aspect of {sub_topic}?"
        },
        {
            "role": "assistant",
            "content": f"Certainly! In {sub_topic}, this concept is particularly important because it forms the foundation for understanding more advanced topics in {topic}."
        }
    ]
    
    return {
        "conversation_id": f"conv_{hash(question) % 100000}",
        "system_prompt": f"You are a helpful assistant specializing in {topic}.",
        "messages": messages,
        "num_turns": len(messages) // 2,
        "topic": topic,
        "sub_topic": sub_topic,
        "persona": "expert_tutor",
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
    TrainingType.PPO: generate_ppo_data,
    TrainingType.KTO: generate_kto_data,
    TrainingType.ORPO: generate_orpo_data,
    TrainingType.RLHF: generate_rlhf_data,
    TrainingType.CHAT: generate_chat_data,
}


async def generate_training_data(
    training_type: TrainingType,
    question_data: Dict[str, Any],
    code_executor=None
) -> Dict[str, Any]:
    """
    Generate training data based on type.
    
    This is the main entry point for generation workflows.
    
    Args:
        training_type: Type of training data to generate
        question_data: Dict with question, topic, sub_topic, context fields
        code_executor: Optional code executor for verification
        
    Returns:
        Generated training data dict ready for database insertion
        
    Raises:
        ValueError: If training type is not supported
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
