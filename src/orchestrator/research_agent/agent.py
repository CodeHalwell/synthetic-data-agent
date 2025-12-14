import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "research.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search

from .database_agent import root_agent as database_agent

# Initialize tools
# Use only google_search to avoid AFC compatibility issues
# Database operations available through database_agent sub-agent
root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    sub_agents=[database_agent],  # Use database_agent for database operations
    tools=[google_search],  # Only google_search to avoid AFC conflicts
)

