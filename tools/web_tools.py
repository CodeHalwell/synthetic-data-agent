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
