"""
Reviewer Agent for Quality Assurance

This agent validates synthetic training data for quality and correctness.
It performs deterministic checks and quality scoring.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "reviewer.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from tools.database_tools import DatabaseTools
from .review_db_sub_agent import root_agent as review_db_sub_agent
from ..code_execution_agent import root_agent as code_execution_agent

# Initialize tools
# DatabaseTools for read-only access (querying generated data, etc.)
database_tools = DatabaseTools()

# Sub-agents for writes and code execution
# review_db_sub_agent: Writes review results to database
# code_execution_agent: Executes code for verification (uses BuiltInCodeExecutor)
root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    tools=[database_tools],  # Custom tool (read-only database access)
    sub_agents=[review_db_sub_agent, code_execution_agent],  # Sub-agents for writes and code execution
)
