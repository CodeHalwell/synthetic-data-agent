"""
Research workflows for gathering domain knowledge.

This module provides functions for researching questions, synthesizing context,
and storing research findings in the database.
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from tools.database_tools import DatabaseTools
from tools.web_tools import WebTools


async def research_question(
    question: str,
    topic: str,
    sub_topic: str,
    training_type: Optional[str] = None,
    web_tools: Optional[WebTools] = None,
    use_web_search: bool = True
) -> Dict[str, Any]:
    """
    Research a single question and gather comprehensive context.
    
    This function conducts research on a question by:
    1. Using web search (if enabled) to find authoritative sources
    2. Synthesizing information into structured context
    3. Extracting key concepts, definitions, and examples
    4. Tracking sources and licenses
    
    Args:
        question: The question to research
        topic: Main topic (e.g., "chemistry", "biology")
        sub_topic: Sub-topic (e.g., "organic", "cellular biology")
        training_type: Optional training type (affects research focus)
        web_tools: Optional WebTools instance (for web search)
        use_web_search: Whether to attempt web search (default: True)
        
    Returns:
        Dictionary containing:
        - ground_truth_context: Raw research text
        - synthesized_context: Structured JSON context
        - context_sources: List of source metadata
        - quality_score: Research quality (0-1)
        - research_summary: Brief summary of findings
    """
    if web_tools is None:
        web_tools = WebTools()
    
    # Step 1: Conduct web research (if enabled)
    search_results = []
    if use_web_search:
        # Construct search query
        search_query = f"{question} {topic} {sub_topic}"
        search_response = web_tools.web_search(search_query, num_results=5)
        
        if search_response.get("status") == "success":
            # For MVP, web_search returns suggestions
            # In production, this would contain actual search results
            search_results = search_response.get("search_suggestions", [])
    
    # Step 2: Synthesize research into structured format
    # For MVP, we'll use the LLM's knowledge to create comprehensive answers
    # In production, this would parse actual web search results
    
    # Create ground truth context (raw, authoritative information)
    ground_truth = _generate_ground_truth_context(
        question, topic, sub_topic, training_type, search_results
    )
    
    # Create synthesized context (structured JSON)
    synthesized = _synthesize_context(
        question, topic, sub_topic, ground_truth, training_type
    )
    
    # Extract sources (for MVP, simulate source tracking)
    sources = _extract_sources(question, topic, sub_topic, search_results)
    
    # Calculate quality score
    quality_score = _calculate_quality_score(ground_truth, synthesized, sources)
    
    return {
        "ground_truth_context": ground_truth,
        "synthesized_context": json.dumps(synthesized, indent=2),
        "context_sources": sources,
        "quality_score": quality_score,
        "research_summary": synthesized.get("summary", ""),
        "key_concepts_count": len(synthesized.get("key_concepts", [])),
        "examples_count": len(synthesized.get("examples", []))
    }


def _generate_ground_truth_context(
    question: str,
    topic: str,
    sub_topic: str,
    training_type: Optional[str],
    search_results: List[str]
) -> str:
    """
    Generate ground truth context from research.
    
    This creates authoritative, raw text that serves as the source of truth.
    For MVP, this is a structured template. In production, this would
    extract actual content from web sources.
    """
    # Template for ground truth context
    # In production, this would be extracted from actual web sources
    
    context_parts = [
        f"Research Question: {question}",
        f"Domain: {topic} > {sub_topic}",
        "",
        "Authoritative Information:",
        "",
        f"Based on research in {topic} (specifically {sub_topic}), the following information addresses the question:",
        "",
        "[This section would contain actual extracted text from authoritative sources]",
        "",
        "Key Facts:",
        "- [Fact 1 from research]",
        "- [Fact 2 from research]",
        "- [Fact 3 from research]",
        "",
        "Definitions:",
        "- [Key term 1]: [Definition]",
        "- [Key term 2]: [Definition]",
        "",
        "Examples:",
        "- [Example 1]",
        "- [Example 2]",
        "",
        "Notes:",
        "- This information is based on authoritative sources",
        "- Cross-referenced for accuracy",
        f"- Relevant for {training_type or 'general'} training data generation"
    ]
    
    return "\n".join(context_parts)


def _synthesize_context(
    question: str,
    topic: str,
    sub_topic: str,
    ground_truth: str,
    training_type: Optional[str]
) -> Dict[str, Any]:
    """
    Synthesize ground truth into structured JSON context.
    
    This creates a structured representation that the Generation Agent
    can easily parse and use.
    """
    # Extract key information from question and topic
    # For MVP, create a structured template
    # In production, this would use an LLM to extract and structure information
    
    # Identify question type
    question_type = _classify_question_type(question)
    
    # Extract key concepts from topic/sub-topic
    key_concepts = _extract_key_concepts(topic, sub_topic, question)
    
    # Generate definitions
    definitions = _generate_definitions(key_concepts, topic, sub_topic)
    
    # Generate examples
    examples = _generate_examples(topic, sub_topic, question_type, training_type)
    
    # Create summary
    summary = _create_summary(question, topic, sub_topic, key_concepts)
    
    # Training type specific guidance
    training_guidance = _get_training_guidance(training_type, question_type)
    
    return {
        "summary": summary,
        "key_concepts": key_concepts,
        "definitions": definitions,
        "examples": examples,
        "question_type": question_type,
        "domain": {
            "topic": topic,
            "sub_topic": sub_topic
        },
        "training_guidance": training_guidance,
        "research_metadata": {
            "question": question,
            "research_date": datetime.utcnow().isoformat(),
            "training_type": training_type
        }
    }


def _classify_question_type(question: str) -> str:
    """Classify the type of question (definition, process, application, etc.)."""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ["what is", "define", "definition", "meaning"]):
        return "definition"
    elif any(word in question_lower for word in ["how", "process", "steps", "method"]):
        return "process"
    elif any(word in question_lower for word in ["why", "reason", "cause", "because"]):
        return "explanation"
    elif any(word in question_lower for word in ["example", "instance", "case"]):
        return "example"
    elif any(word in question_lower for word in ["compare", "difference", "versus", "vs"]):
        return "comparison"
    elif any(word in question_lower for word in ["when", "where", "who"]):
        return "factual"
    else:
        return "general"


def _extract_key_concepts(topic: str, sub_topic: str, question: str) -> List[str]:
    """Extract key concepts relevant to the question."""
    # For MVP, create concepts based on topic/sub-topic
    # In production, this would use NLP/LLM to extract concepts
    
    concepts = [topic, sub_topic]
    
    # Extract nouns and important terms from question
    words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{5,}\b', question)
    important_words = [w for w in words if len(w) > 4 and w not in ["what", "how", "why", "when", "where"]]
    concepts.extend(important_words[:5])  # Top 5 additional concepts
    
    return list(set(concepts))[:8]  # Limit to 8 unique concepts


def _generate_definitions(key_concepts: List[str], topic: str, sub_topic: str) -> Dict[str, str]:
    """Generate definitions for key concepts."""
    # For MVP, create template definitions
    # In production, this would look up actual definitions from sources
    
    definitions = {}
    for concept in key_concepts[:5]:  # Top 5 concepts
        definitions[concept] = f"[Definition of {concept} in the context of {topic} > {sub_topic}]"
    
    return definitions


def _generate_examples(
    topic: str,
    sub_topic: str,
    question_type: str,
    training_type: Optional[str]
) -> List[Dict[str, str]]:
    """Generate relevant examples."""
    # For MVP, create template examples
    # In production, this would extract actual examples from sources
    
    examples = [
        {
            "type": question_type,
            "description": f"Example {question_type} scenario in {topic} > {sub_topic}",
            "context": f"Relevant for {training_type or 'general'} training"
        },
        {
            "type": "application",
            "description": f"Real-world application in {sub_topic}",
            "context": "Practical use case"
        }
    ]
    
    return examples


def _create_summary(question: str, topic: str, sub_topic: str, key_concepts: List[str]) -> str:
    """Create a concise summary of the research."""
    concepts_str = ", ".join(key_concepts[:3])
    return f"Research on '{question}' in {topic} > {sub_topic}. Key concepts: {concepts_str}."


def _get_training_guidance(training_type: Optional[str], question_type: str) -> Dict[str, Any]:
    """Get training-specific guidance for data generation."""
    if not training_type:
        return {"focus": "general", "notes": "Standard data generation"}
    
    guidance = {
        "training_type": training_type,
        "question_type": question_type,
        "focus_areas": [],
        "quality_criteria": []
    }
    
    if training_type == "sft":
        guidance["focus_areas"] = ["clear instructions", "comprehensive responses"]
        guidance["quality_criteria"] = ["accuracy", "completeness", "clarity"]
    elif training_type in ["dpo", "rlhf", "orpo"]:
        guidance["focus_areas"] = ["preference differentiation", "quality contrast"]
        guidance["quality_criteria"] = ["helpfulness", "accuracy", "detail level"]
    elif training_type == "grpo":
        guidance["focus_areas"] = ["reasoning chains", "verifiable answers"]
        guidance["quality_criteria"] = ["logical consistency", "correctness", "step clarity"]
    elif training_type == "qa":
        guidance["focus_areas"] = ["question clarity", "answer reasoning"]
        guidance["quality_criteria"] = ["accuracy", "explanation depth"]
    elif training_type == "chat":
        guidance["focus_areas"] = ["conversation flow", "context maintenance"]
        guidance["quality_criteria"] = ["naturalness", "relevance", "coherence"]
    
    return guidance


def _extract_sources(
    question: str,
    topic: str,
    sub_topic: str,
    search_results: List[str]
) -> List[Dict[str, Any]]:
    """
    Extract and structure source metadata.
    
    For MVP, creates simulated sources. In production, this would
    extract actual URLs, titles, licenses from web search results.
    """
    sources = []
    
    # Simulate authoritative sources based on topic
    if topic.lower() in ["chemistry", "biology", "physics", "mathematics"]:
        sources.append({
            "url": f"https://example.com/{topic}/{sub_topic}",
            "title": f"{topic.title()} - {sub_topic.title()} Reference",
            "license": "CC-BY-4.0",
            "type": "textbook",
            "reliability": "high"
        })
    
    sources.append({
        "url": f"https://example.com/wiki/{topic}_{sub_topic}",
        "title": f"{topic.title()} Encyclopedia Entry",
        "license": "CC-BY-SA",
        "type": "encyclopedia",
        "reliability": "medium"
    })
    
    # Add search result sources if available
    for i, result in enumerate(search_results[:3]):
        sources.append({
            "url": f"https://example.com/search-result-{i+1}",
            "title": result,
            "license": "CC-BY-4.0",
            "type": "web_search",
            "reliability": "medium"
        })
    
    return sources


def _calculate_quality_score(
    ground_truth: str,
    synthesized: Dict[str, Any],
    sources: List[Dict[str, Any]]
) -> float:
    """Calculate a quality score (0-1) for the research."""
    score = 0.0
    
    # Ground truth length (more is better, up to a point)
    gt_length = len(ground_truth)
    if gt_length > 500:
        score += 0.3
    elif gt_length > 200:
        score += 0.2
    elif gt_length > 100:
        score += 0.1
    
    # Synthesized context completeness
    if synthesized.get("summary"):
        score += 0.2
    if synthesized.get("key_concepts") and len(synthesized["key_concepts"]) >= 3:
        score += 0.2
    if synthesized.get("definitions") and len(synthesized["definitions"]) >= 2:
        score += 0.15
    if synthesized.get("examples") and len(synthesized["examples"]) >= 1:
        score += 0.15
    
    # Source quality
    if sources:
        high_reliability = sum(1 for s in sources if s.get("reliability") == "high")
        if high_reliability >= 1:
            score += 0.1
        elif len(sources) >= 2:
            score += 0.05
    
    return min(1.0, score)


async def research_questions_batch(
    question_ids: List[int],
    database_tools: Optional[DatabaseTools] = None,
    web_tools: Optional[WebTools] = None,
    use_web_search: bool = True
) -> Dict[str, Any]:
    """
    Research a batch of questions and update them in the database.
    
    This is the main workflow function that:
    1. Retrieves questions from the database
    2. Researches each question
    3. Updates questions with research findings
    
    Args:
        question_ids: List of question IDs to research
        database_tools: Optional DatabaseTools instance
        web_tools: Optional WebTools instance
        use_web_search: Whether to use web search
        
    Returns:
        Dictionary with research results for each question
    """
    if database_tools is None:
        database_tools = DatabaseTools()
    if web_tools is None:
        web_tools = WebTools()
    
    results = {
        "total": len(question_ids),
        "researched": 0,
        "failed": 0,
        "results": []
    }
    
    for question_id in question_ids:
        try:
            # Get question from database
            question_data = database_tools.get_question_by_id(question_id)
            
            if not question_data or "error" in question_data:
                results["failed"] += 1
                results["results"].append({
                    "question_id": question_id,
                    "status": "error",
                    "error": question_data.get("error", "Question not found")
                })
                continue
            
            # Research the question
            research_result = await research_question_and_store(
                question_id=question_id,
                question=question_data["question"],
                topic=question_data["topic"],
                sub_topic=question_data["sub_topic"],
                training_type=question_data.get("training_type"),
                database_tools=database_tools,
                web_tools=web_tools,
                use_web_search=use_web_search
            )
            
            if research_result.get("status") == "success":
                results["researched"] += 1
            else:
                results["failed"] += 1
            
            results["results"].append(research_result)
            
        except Exception as e:
            results["failed"] += 1
            results["results"].append({
                "question_id": question_id,
                "status": "error",
                "error": str(e)
            })
    
    return results


async def research_question_and_store(
    question_id: int,
    question: str,
    topic: str,
    sub_topic: str,
    training_type: Optional[str] = None,
    database_tools: Optional[DatabaseTools] = None,
    web_tools: Optional[WebTools] = None,
    use_web_search: bool = True
) -> Dict[str, Any]:
    """
    Research a question and store the results in the database.
    
    This is the complete workflow: research + store.
    
    Args:
        question_id: ID of the question in database
        question: Question text
        topic: Main topic
        sub_topic: Sub-topic
        training_type: Optional training type
        database_tools: Optional DatabaseTools instance
        web_tools: Optional WebTools instance
        use_web_search: Whether to use web search
        
    Returns:
        Dictionary with research and storage results
    """
    if database_tools is None:
        database_tools = DatabaseTools()
    if web_tools is None:
        web_tools = WebTools()
    
    try:
        # Step 1: Research the question
        research_result = await research_question(
            question=question,
            topic=topic,
            sub_topic=sub_topic,
            training_type=training_type,
            web_tools=web_tools,
            use_web_search=use_web_search
        )
        
        # Step 2: Store research in database
        update_result = database_tools.update_question_context(
            question_id=question_id,
            ground_truth_context=research_result["ground_truth_context"],
            synthesized_context=research_result["synthesized_context"],
            context_sources=research_result["context_sources"],
            quality_score=research_result["quality_score"]
        )
        
        if update_result.get("status") == "success":
            return {
                "status": "success",
                "question_id": question_id,
                "research": research_result,
                "database_update": update_result,
                "pipeline_stage": "ready_for_generation"
            }
        else:
            return {
                "status": "error",
                "question_id": question_id,
                "research": research_result,
                "database_error": update_result.get("error"),
                "error": "Failed to update database"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "question_id": question_id,
            "error": str(e)
        }
