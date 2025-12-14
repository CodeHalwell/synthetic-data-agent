"""
Generation Agent for Synthetic Data

This agent creates synthetic training data for various LLM post-training methods.
It uses research context and specialist tools to generate high-quality examples.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "generator.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from tools.database_tools import DatabaseTools
from .generation_db_sub_agent import root_agent as generation_db_sub_agent
from .code_execution_sub_agent import root_agent as code_execution_agent

# Initialize tools
# DatabaseTools for read-only access (querying questions, etc.)
database_tools = DatabaseTools()

# Sub-agents for writes and code execution
# generation_db_sub_agent: Writes generated data to database
# code_execution_agent: Executes code for verification (uses BuiltInCodeExecutor)
root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    tools=[database_tools],  # Custom tool (read-only database access)
    sub_agents=[generation_db_sub_agent, code_execution_agent],  # Sub-agents for writes and code execution
)
