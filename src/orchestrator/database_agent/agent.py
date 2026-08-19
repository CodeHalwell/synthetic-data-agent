import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "database.yaml")

# Note: This agent is now a "manager" agent focused on schema initialization,
# data review, and final storage. Day-to-day CRUD operations are handled
# by specialized database sub-agents (question_db_sub_agent, research_db_sub_agent, etc.)

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from tools.database_tools import DatabaseTools

database_tools = DatabaseTools()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    tools=[database_tools],
)
