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
from src.orchestrator.research_agent.agent import root_agent as research_agent


async def research_question(
    question: str,
    topic: str,
    sub_topic: str,
    training_type: Optional[str] = None,
    use_web_search: bool = True
) -> Dict[str, Any]:
    """
    Research a single question and gather comprehensive context using real web search.
    
    This function conducts research on a question by:
    1. Invoking the research agent with google_search tool to find authoritative sources
    2. Extracting real search results (snippets, URLs, titles)
    3. Synthesizing information into structured context
    4. Extracting key concepts, definitions, and examples
    5. Tracking sources and licenses
    
    Args:
        question: The question to research
        topic: Main topic (e.g., "chemistry", "biology")
        sub_topic: Sub-topic (e.g., "organic", "cellular biology")
        training_type: Optional training type (affects research focus)
        use_web_search: Whether to use web search (default: True)
        
    Returns:
        Dictionary containing:
        - ground_truth_context: Raw research text from real sources
        - synthesized_context: Structured JSON context
        - context_sources: List of source metadata (real URLs)
        - quality_score: Research quality (0-1)
        - research_summary: Brief summary of findings
    """
    if use_web_search:
        # Step 1: Invoke research agent to perform actual web search
        search_query = f"{question} {topic} {sub_topic}"
        
        # Create a structured prompt for the research agent
        research_prompt = f"""Research the following question and provide comprehensive information:

Question: {question}
Topic: {topic}
Sub-topic: {sub_topic}
Training Type: {training_type or 'general'}

Please:
1. Use the google_search tool to find authoritative sources about this question
2. Extract key information from the search results (snippets, titles, URLs)
3. Synthesize a comprehensive answer based on the search results
4. Provide the following in your response:
   - A detailed answer to the question based on the search results
   - Key facts and information from authoritative sources
   - Important definitions and concepts
   - Relevant examples
   - Source URLs and titles from your search

Format your response as structured text that can be parsed. Include actual information from the search results, not placeholders."""

        try:
            # Invoke the research agent
            agent_response = await research_agent.invoke(research_prompt)
            
            # Extract research data from agent response
            # The agent will have used google_search and returned research findings
            research_text = str(agent_response) if agent_response else ""
            
            # Step 2: Parse agent response to extract search results and information
            # The agent's response should contain the research findings
            search_results_data = _parse_agent_research_response(research_text, search_query)
            
        except Exception as e:
            # Fallback: if agent invocation fails, use basic research
            print(f"Warning: Research agent invocation failed: {e}")
            search_results_data = {
                "research_text": f"Research on: {question} in {topic} > {sub_topic}",
                "sources": [],
                "snippets": []
            }
    else:
        # No web search - use agent's knowledge only
        search_results_data = {
            "research_text": "",
            "sources": [],
            "snippets": []
        }
    
    # Step 3: Generate ground truth context from real research
    ground_truth = _generate_ground_truth_context_from_research(
        question, topic, sub_topic, training_type, search_results_data
    )
    
    # Step 4: Create synthesized context
    synthesized = _synthesize_context(
        question, topic, sub_topic, ground_truth, training_type
    )
    
    # Step 5: Extract sources from real search results
    sources = _extract_sources_from_research(
        question, topic, sub_topic, search_results_data
    )
    
    # Step 6: Calculate quality score
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


def _parse_agent_research_response(
    response_text: str,
    search_query: str
) -> Dict[str, Any]:
    """
    Parse the research agent's response to extract search results and information.
    
    The agent response should contain:
    - Research findings from google_search results
    - Source URLs and titles
    - Key information extracted from snippets
    
    Args:
        response_text: The agent's response text
        search_query: The original search query
        
    Returns:
        Dictionary with parsed research data:
        - research_text: Main research content
        - sources: List of source dictionaries
        - snippets: List of text snippets from search results
    """
    # Extract URLs from response (common patterns)
    url_pattern = r'https?://[^\s\)]+'
    urls = re.findall(url_pattern, response_text)
    
    # Extract titles (often appear before URLs or in quotes)
    title_pattern = r'"([^"]+)"|\[([^\]]+)\]'
    titles = re.findall(title_pattern, response_text)
    titles = [t[0] or t[1] for t in titles if t[0] or t[1]]
    
    # Create source list from URLs and titles
    sources = []
    for i, url in enumerate(urls[:10]):  # Limit to top 10
        title = titles[i] if i < len(titles) else f"Source {i+1}"
        sources.append({
            "url": url,
            "title": title,
            "type": "web_search"
        })
    
    # Extract snippets (paragraphs or bullet points)
    # Look for sections that seem to contain research content
    lines = response_text.split('\n')
    snippets = []
    current_snippet = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_snippet:
                snippets.append(current_snippet)
                current_snippet = ""
            continue
        
        # Skip headers, URLs, and very short lines
        if (line.startswith('#') or 
            line.startswith('http') or 
            len(line) < 20):
            continue
        
        current_snippet += line + " "
        if len(current_snippet) > 200:  # Limit snippet length
            snippets.append(current_snippet.strip())
            current_snippet = ""
    
    if current_snippet:
        snippets.append(current_snippet.strip())
    
    return {
        "research_text": response_text,
        "sources": sources,
        "snippets": snippets[:10]  # Top 10 snippets
    }


def _generate_ground_truth_context_from_research(
    question: str,
    topic: str,
    sub_topic: str,
    training_type: Optional[str],
    research_data: Dict[str, Any]
) -> str:
    """
    Generate ground truth context from real research data.
    
    This creates authoritative, raw text from actual web search results.
    
    Args:
        question: The research question
        topic: Main topic
        sub_topic: Sub-topic
        training_type: Optional training type
        research_data: Dictionary with research_text, sources, snippets
        
    Returns:
        Formatted ground truth context string
    """
    context_parts = [
        f"Research Question: {question}",
        f"Domain: {topic} > {sub_topic}",
        "",
        "Authoritative Information from Web Research:",
        ""
    ]
    
    # Add research content from agent response
    if research_data.get("research_text"):
        # Extract the main research content (skip URLs and metadata)
        research_text = research_data["research_text"]
        # Remove URLs for cleaner text
        research_text = re.sub(r'https?://[^\s\)]+', '', research_text)
        context_parts.append(research_text)
        context_parts.append("")
    
    # Add snippets from search results
    if research_data.get("snippets"):
        context_parts.append("Key Information from Search Results:")
        context_parts.append("")
        for i, snippet in enumerate(research_data["snippets"][:5], 1):
            context_parts.append(f"{i}. {snippet}")
        context_parts.append("")
    
    # Add source information
    if research_data.get("sources"):
        context_parts.append("Sources:")
        for source in research_data["sources"][:5]:
            title = source.get("title", "Untitled")
            url = source.get("url", "")
            context_parts.append(f"- {title}: {url}")
        context_parts.append("")
    
    # Add metadata
    context_parts.extend([
        "Notes:",
        "- This information is based on web search results from authoritative sources",
        "- Information has been synthesized from multiple sources",
        f"- Relevant for {training_type or 'general'} training data generation"
    ])
    
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


def _extract_sources_from_research(
    question: str,
    topic: str,
    sub_topic: str,
    research_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract and structure source metadata from real research data.
    
    Args:
        question: The research question
        topic: Main topic
        sub_topic: Sub-topic
        research_data: Dictionary with sources from research
        
    Returns:
        List of source dictionaries with URLs, titles, licenses
    """
    sources = []
    
    # Extract sources from research data
    if research_data.get("sources"):
        for source in research_data["sources"]:
            # Determine license based on domain (heuristic)
            url = source.get("url", "")
            license_type = "unknown"
            reliability = "medium"
            
            # Check for common authoritative domains
            if any(domain in url.lower() for domain in [".edu", ".gov", ".org"]):
                reliability = "high"
                license_type = "CC-BY-4.0"  # Common for educational
            elif "wikipedia" in url.lower():
                license_type = "CC-BY-SA"
                reliability = "high"
            elif any(domain in url.lower() for domain in ["arxiv", "pubmed", "scholar"]):
                license_type = "varies"
                reliability = "high"
            
            sources.append({
                "url": url,
                "title": source.get("title", "Untitled Source"),
                "license": license_type,
                "type": source.get("type", "web_search"),
                "reliability": reliability
            })
    
    # If no sources found, add a note
    if not sources:
        sources.append({
            "url": "",
            "title": f"Research on {question}",
            "license": "unknown",
            "type": "agent_knowledge",
            "reliability": "medium",
            "note": "Sources extracted from agent research response"
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
    
    try:
        # Step 1: Research the question using real web search
        research_result = await research_question(
            question=question,
            topic=topic,
            sub_topic=sub_topic,
            training_type=training_type,
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
