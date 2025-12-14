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
from google.adk.code_executors import BuiltInCodeExecutor

from tools.database_tools import DatabaseTools

# Initialize tools
database_tools = DatabaseTools()
code_executor = BuiltInCodeExecutor()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    tools=[database_tools],
    code_executor=code_executor,
)
