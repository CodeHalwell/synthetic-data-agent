import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "research.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search

from .research_db_sub_agent import root_agent as research_db_sub_agent

# Initialize tools
# Use only google_search to avoid AFC compatibility issues
# Database operations available through research_db_sub_agent sub-agent
root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    sub_agents=[research_db_sub_agent],  # Use research_db_sub_agent for database writes
    tools=[google_search],  # Only google_search (built-in tool)
)

