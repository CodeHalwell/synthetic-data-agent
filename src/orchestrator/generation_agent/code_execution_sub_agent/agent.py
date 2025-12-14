"""
Code Execution Sub-Agent for Generation Agent

This sub-agent handles code execution for generation operations.
It is used by the Generation Agent to execute code when needed
(e.g., verifying mathematical solutions, running test code).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "code_execution.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.code_executors import BuiltInCodeExecutor

# Initialize code executor (built-in tool)
code_executor = BuiltInCodeExecutor()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    code_executor=code_executor,  # Only built-in tool (no custom tools)
)
