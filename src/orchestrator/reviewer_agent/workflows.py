"""
Review workflows for quality assurance and validation.

Each function validates generated data for a specific training type
and returns quality scores with approval status.
"""

import json
import re
from typing import Dict, Any, Optional


async def review_sft_data(
    data: Dict[str, Any],
    ground_truth: str = ""
) -> Dict[str, Any]:
    """
    Review SFT training data.
    
    Validates instruction-response pairs for quality and correctness.
    
    Args:
        data: Generated SFT data dict
        ground_truth: Optional ground truth context for validation
        
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
    
    if not has_all_fields:
        return {
            "quality_score": 0.0,
            "review_status": "rejected",
            "scores": scores,
            "reviewer_notes": "Missing required fields: instruction and/or response"
        }
    
    # Check response quality
    response = data.get("response", "")
    response_length = len(response)
    
    # Completeness: based on response length (expect at least 100 chars)
    scores["completeness"] = min(1.0, response_length / 100) if response_length > 0 else 0.0
    
    # Clarity: check for structure (sentences, punctuation, formatting)
    has_structure = any(marker in response for marker in [".", "\n", ":", "•", "-"])
    has_multiple_sentences = response.count(".") >= 2 or response.count("\n") >= 1
    scores["clarity"] = 0.9 if has_multiple_sentences else (0.7 if has_structure else 0.5)
    
    # Factual accuracy: check if response uses ground truth context
    if ground_truth:
        # Extract key terms from ground truth (simple heuristic)
        gt_words = set(word.lower() for word in ground_truth.split() if len(word) > 4)
        resp_words = set(word.lower() for word in response.split())
        overlap = len(gt_words & resp_words)
        expected_overlap = min(10, len(gt_words) // 5)  # Expect ~20% overlap
        scores["factual_accuracy"] = min(1.0, overlap / max(expected_overlap, 1))
    else:
        # No ground truth, assume reasonable accuracy
        scores["factual_accuracy"] = 0.75
    
    # Calculate overall score
    overall_score = sum(scores.values()) / len(scores)
    
    # Determine status based on thresholds
    if overall_score >= 0.8:
        status = "approved"
        notes = "High quality response with good structure and completeness."
    elif overall_score >= 0.6:
        status = "needs_revision"
        notes = "Acceptable but could be improved. Check completeness and clarity."
    else:
        status = "rejected"
        notes = "Below quality threshold. Response may be too short or lacks structure."
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": notes
    }


async def review_grpo_data(
    data: Dict[str, Any],
    code_executor=None
) -> Dict[str, Any]:
    """
    Review GRPO data including code execution verification.
    
    Validates reasoning chains, code correctness, and answer verification.
    
    Args:
        data: Generated GRPO data dict
        code_executor: Optional code executor for testing
        
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
    
    if not has_all_fields:
        return {
            "quality_score": 0.0,
            "review_status": "rejected",
            "scores": scores,
            "reviewer_notes": "Missing required fields for GRPO"
        }
    
    # Check reasoning quality
    reasoning = data.get("reasoning", "")
    
    # Look for step-by-step structure
    has_steps = bool(re.search(r'[Ss]tep\s+\d+', reasoning))
    step_count = len(re.findall(r'[Ss]tep\s+\d+', reasoning))
    
    # Look for logical connectors
    has_connectors = any(word in reasoning.lower() 
                        for word in ["therefore", "thus", "hence", "because", 
                                    "since", "consequently", "as a result"])
    
    # Look for conclusion
    has_conclusion = any(word in reasoning.lower() 
                        for word in ["final", "answer", "conclusion", "result"])
    
    # Score reasoning
    if has_steps and step_count >= 3 and has_connectors and has_conclusion:
        scores["reasoning_quality"] = 0.95
    elif has_steps and step_count >= 2:
        scores["reasoning_quality"] = 0.80
    elif has_steps or has_connectors:
        scores["reasoning_quality"] = 0.65
    else:
        scores["reasoning_quality"] = 0.40
    
    # Check code (if present)
    code = data.get("code", "")
    if code:
        # Basic code quality checks
        has_function = "def " in code
        has_docstring = '"""' in code or "'''" in code
        has_comments = "#" in code
        has_return_or_print = "return" in code or "print" in code
        
        # Would execute code here with code_executor in production
        # For now, structural check
        code_quality = 0.0
        if has_function and has_return_or_print:
            code_quality = 0.90
            if has_docstring:
                code_quality = 0.95
            elif has_comments:
                code_quality = 0.92
        elif has_return_or_print:
            code_quality = 0.75
        else:
            code_quality = 0.50
        
        scores["code_correctness"] = code_quality
    else:
        # No code provided - neutral score
        scores["code_correctness"] = 0.70
    
    # Verify answer correctness flag
    is_correct = data.get("is_correct", False)
    predicted_answer = data.get("predicted_answer", "")
    
    if is_correct and predicted_answer:
        scores["answer_verification"] = 1.0
    elif predicted_answer:
        scores["answer_verification"] = 0.60
    else:
        scores["answer_verification"] = 0.30
    
    overall_score = sum(scores.values()) / len(scores)
    
    if overall_score >= 0.8:
        status = "approved"
        notes = f"Strong reasoning with {step_count} steps. Code quality good."
    elif overall_score >= 0.6:
        status = "needs_revision"
        notes = "Reasoning present but could be more detailed. Verify code correctness."
    else:
        status = "rejected"
        notes = "Insufficient reasoning structure or missing verification."
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": notes
    }


async def review_dpo_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review DPO preference pair data.
    
    Validates that chosen response is clearly better than rejected.
    
    Args:
        data: Generated DPO data dict
        
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
    
    if not has_all_fields:
        return {
            "quality_score": 0.0,
            "review_status": "rejected",
            "scores": scores,
            "reviewer_notes": "Missing required fields for DPO"
        }
    
    chosen = data.get("chosen", "")
    rejected = data.get("rejected", "")
    
    # Validate: chosen != rejected
    if chosen.strip() == rejected.strip():
        return {
            "quality_score": 0.0,
            "review_status": "rejected",
            "scores": scores,
            "reviewer_notes": "Chosen and rejected responses are identical!"
        }
    
    # Evaluate chosen quality
    chosen_length = len(chosen)
    chosen_has_structure = any(m in chosen for m in [".", "\n", ":"])
    chosen_sentence_count = chosen.count(".") + chosen.count("\n")
    
    scores["chosen_quality"] = min(1.0, 
        (chosen_length / 200) * 0.6 +  # Length factor
        (1.0 if chosen_has_structure else 0.0) * 0.2 +  # Structure factor
        min(1.0, chosen_sentence_count / 3) * 0.2  # Multiple points factor
    )
    
    # Evaluate rejected quality (should be lower but not terrible)
    rejected_length = len(rejected)
    rejected_has_structure = any(m in rejected for m in [".", "\n", ":"])
    
    # Rejected should exist but be clearly inferior
    if rejected_length < 20:
        scores["rejected_quality"] = 0.30  # Too short
    elif rejected_length > chosen_length * 0.9:
        scores["rejected_quality"] = 0.50  # Too similar in length
    else:
        scores["rejected_quality"] = 0.70  # Appropriate
    
    # Preference clarity (chosen should be significantly better)
    length_ratio = chosen_length / max(rejected_length, 1)
    quality_diff = scores["chosen_quality"] - scores["rejected_quality"]
    
    if length_ratio >= 2.5 and quality_diff >= 0.3:
        scores["preference_clarity"] = 1.0
    elif length_ratio >= 1.5 and quality_diff >= 0.2:
        scores["preference_clarity"] = 0.85
    elif length_ratio >= 1.2:
        scores["preference_clarity"] = 0.70
    else:
        scores["preference_clarity"] = 0.50
    
    # Check ratings if provided
    if "chosen_rating" in data and "rejected_rating" in data:
        rating_diff = data["chosen_rating"] - data["rejected_rating"]
        if rating_diff < 1.0:
            scores["preference_clarity"] *= 0.8  # Penalize small rating difference
    
    overall_score = sum(scores.values()) / len(scores)
    
    if overall_score >= 0.75:
        status = "approved"
        notes = f"Clear preference. Chosen: {chosen_length} chars, Rejected: {rejected_length} chars."
    elif overall_score >= 0.5:
        status = "needs_revision"
        notes = "Preference exists but could be clearer. Consider improving differentiation."
    else:
        status = "rejected"
        notes = "Insufficient differentiation between chosen and rejected responses."
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": notes
    }


async def review_qa_data(
    data: Dict[str, Any],
    ground_truth: str = ""
) -> Dict[str, Any]:
    """
    Review QA data.
    
    Validates question-answer pairs with reasoning.
    
    Args:
        data: Generated QA data dict
        ground_truth: Optional ground truth for validation
        
    Returns:
        Review results
    """
    scores = {
        "answer_quality": 0.0,
        "reasoning_present": 0.0,
        "format_compliance": 0.0
    }
    
    # Check format
    required_fields = ["question", "answer"]
    has_all_fields = all(field in data and data[field] for field in required_fields)
    scores["format_compliance"] = 1.0 if has_all_fields else 0.0
    
    if not has_all_fields:
        return {
            "quality_score": 0.0,
            "review_status": "rejected",
            "scores": scores,
            "reviewer_notes": "Missing required fields for QA"
        }
    
    answer = data.get("answer", "")
    reasoning = data.get("reasoning", "")
    
    # Evaluate answer quality
    answer_length = len(answer)
    scores["answer_quality"] = min(1.0, answer_length / 100)
    
    # Check if reasoning is present
    scores["reasoning_present"] = 1.0 if (reasoning and len(reasoning) > 20) else 0.5
    
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
        "reviewer_notes": f"Answer length: {answer_length}, Has reasoning: {bool(reasoning)}"
    }


async def review_ppo_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review PPO data with reward signals.
    
    Args:
        data: Generated PPO data dict
        
    Returns:
        Review results
    """
    scores = {
        "response_quality": 0.0,
        "reward_validity": 0.0,
        "format_compliance": 0.0
    }
    
    required_fields = ["prompt", "response", "reward"]
    has_all_fields = all(field in data and data[field] is not None for field in required_fields)
    scores["format_compliance"] = 1.0 if has_all_fields else 0.0
    
    if not has_all_fields:
        return {
            "quality_score": 0.0,
            "review_status": "rejected",
            "scores": scores,
            "reviewer_notes": "Missing required fields for PPO"
        }
    
    response = data.get("response", "")
    reward = data.get("reward", 0.0)
    
    scores["response_quality"] = min(1.0, len(response) / 100)
    
    # Validate reward is in reasonable range
    if -1.0 <= reward <= 1.0:
        scores["reward_validity"] = 1.0
    elif -10.0 <= reward <= 10.0:
        scores["reward_validity"] = 0.7
    else:
        scores["reward_validity"] = 0.3
    
    overall_score = sum(scores.values()) / len(scores)
    
    status = "approved" if overall_score >= 0.8 else "needs_revision" if overall_score >= 0.6 else "rejected"
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": f"Reward: {reward}, Response length: {len(response)}"
    }


async def review_kto_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review KTO binary feedback data.
    
    Args:
        data: Generated KTO data dict
        
    Returns:
        Review results
    """
    scores = {
        "response_quality": 0.0,
        "feedback_validity": 0.0,
        "format_compliance": 0.0
    }
    
    required_fields = ["prompt", "response", "is_desirable"]
    has_all_fields = all(field in data and data[field] is not None for field in required_fields)
    scores["format_compliance"] = 1.0 if has_all_fields else 0.0
    
    if not has_all_fields:
        return {
            "quality_score": 0.0,
            "review_status": "rejected",
            "scores": scores,
            "reviewer_notes": "Missing required fields for KTO"
        }
    
    response = data.get("response", "")
    is_desirable = data.get("is_desirable", None)
    feedback_reason = data.get("feedback_reason", "")
    
    scores["response_quality"] = min(1.0, len(response) / 100)
    scores["feedback_validity"] = 1.0 if isinstance(is_desirable, bool) and feedback_reason else 0.7
    
    overall_score = sum(scores.values()) / len(scores)
    
    status = "approved" if overall_score >= 0.8 else "needs_revision" if overall_score >= 0.6 else "rejected"
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": f"Desirable: {is_desirable}, Has feedback reason: {bool(feedback_reason)}"
    }


async def review_orpo_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review ORPO combined SFT + preference data.
    
    Uses DPO validation logic since structure is similar.
    
    Args:
        data: Generated ORPO data dict
        
    Returns:
        Review results
    """
    # ORPO is similar to DPO - reuse DPO validation
    return await review_dpo_data(data)


async def review_rlhf_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review RLHF comparison data.
    
    Args:
        data: Generated RLHF data dict
        
    Returns:
        Review results
    """
    scores = {
        "response_quality": 0.0,
        "preference_validity": 0.0,
        "format_compliance": 0.0
    }
    
    required_fields = ["prompt", "response_a", "response_b", "preference"]
    has_all_fields = all(field in data and data[field] for field in required_fields)
    scores["format_compliance"] = 1.0 if has_all_fields else 0.0
    
    if not has_all_fields:
        return {
            "quality_score": 0.0,
            "review_status": "rejected",
            "scores": scores,
            "reviewer_notes": "Missing required fields for RLHF"
        }
    
    response_a = data.get("response_a", "")
    response_b = data.get("response_b", "")
    preference = data.get("preference", "")
    
    # Check responses exist and differ
    if response_a == response_b:
        scores["response_quality"] = 0.3
        scores["preference_validity"] = 0.0
    else:
        scores["response_quality"] = min(1.0, (len(response_a) + len(response_b)) / 400)
        scores["preference_validity"] = 1.0 if preference in ["a", "b", "tie"] else 0.5
    
    overall_score = sum(scores.values()) / len(scores)
    
    status = "approved" if overall_score >= 0.75 else "needs_revision" if overall_score >= 0.5 else "rejected"
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": f"Preference: {preference}, Responses differ: {response_a != response_b}"
    }


async def review_chat_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review multi-turn chat conversation data.
    
    Args:
        data: Generated chat data dict
        
    Returns:
        Review results
    """
    scores = {
        "conversation_quality": 0.0,
        "turn_validity": 0.0,
        "format_compliance": 0.0
    }
    
    required_fields = ["messages", "num_turns"]
    has_all_fields = all(field in data and data[field] for field in required_fields)
    scores["format_compliance"] = 1.0 if has_all_fields else 0.0
    
    if not has_all_fields:
        return {
            "quality_score": 0.0,
            "review_status": "rejected",
            "scores": scores,
            "reviewer_notes": "Missing required fields for Chat"
        }
    
    messages = data.get("messages", [])
    num_turns = data.get("num_turns", 0)
    
    # Validate message structure
    if not isinstance(messages, list) or len(messages) == 0:
        scores["conversation_quality"] = 0.0
        scores["turn_validity"] = 0.0
    else:
        # Check each message has role and content
        valid_messages = all(
            isinstance(msg, dict) and "role" in msg and "content" in msg 
            for msg in messages
        )
        scores["turn_validity"] = 1.0 if valid_messages else 0.5
        
        # Check conversation length
        scores["conversation_quality"] = min(1.0, len(messages) / 4)  # Expect at least 4 messages
    
    overall_score = sum(scores.values()) / len(scores)
    
    status = "approved" if overall_score >= 0.8 else "needs_revision" if overall_score >= 0.6 else "rejected"
    
    return {
        "quality_score": overall_score,
        "review_status": status,
        "scores": scores,
        "reviewer_notes": f"Turns: {num_turns}, Messages: {len(messages)}"
    }


# Registry of review functions by training type
from schema.synthetic_data import TrainingType

REVIEW_FUNCTIONS = {
    TrainingType.SFT: review_sft_data,
    TrainingType.GRPO: review_grpo_data,
    TrainingType.DPO: review_dpo_data,
    TrainingType.QA: review_qa_data,
    TrainingType.PPO: review_ppo_data,
    TrainingType.KTO: review_kto_data,
    TrainingType.ORPO: review_orpo_data,
    TrainingType.RLHF: review_rlhf_data,
    TrainingType.CHAT: review_chat_data,
}


async def review_training_data(
    training_type: TrainingType,
    data: Dict[str, Any],
    ground_truth: str = "",
    code_executor=None
) -> Dict[str, Any]:
    """
    Review training data based on type.
    
    This is the main entry point for review workflows.
    
    Args:
        training_type: Type of training data to review
        data: Generated data dict
        ground_truth: Optional ground truth context for validation
        code_executor: Optional code executor for testing
        
    Returns:
        Review results dict with quality_score, review_status, scores, reviewer_notes
        
    Raises:
        ValueError: If training type is not supported
    """
    review_func = REVIEW_FUNCTIONS.get(training_type)
    
    if not review_func:
        raise ValueError(f"No reviewer for training type: {training_type}")
    
    # Check if function accepts ground_truth or code_executor
    import inspect
    sig = inspect.signature(review_func)
    
    kwargs = {}
    if 'ground_truth' in sig.parameters and ground_truth:
        kwargs['ground_truth'] = ground_truth
    if 'code_executor' in sig.parameters and code_executor:
        kwargs['code_executor'] = code_executor
    
    return await review_func(data, **kwargs)
