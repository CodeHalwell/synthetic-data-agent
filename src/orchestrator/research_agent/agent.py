import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "research.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from tools.web_tools import WebTools
from tools.database_tools import DatabaseTools

# Initialize tools
web_tools = WebTools()
database_tools = DatabaseTools()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config),
    tools=[web_tools, database_tools],
)

