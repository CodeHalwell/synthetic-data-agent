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
from google.adk.code_executors import BuiltInCodeExecutor

from tools.database_tools import DatabaseTools

# Initialize tools
# Note: Reviewer agent doesn't need web_tools - it reviews data, doesn't research
database_tools = DatabaseTools()
code_executor = BuiltInCodeExecutor()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    tools=[database_tools],  # Removed web_tools - reviewer doesn't need web search
    code_executor=code_executor,
)
