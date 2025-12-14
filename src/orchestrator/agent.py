import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "orchestrator.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps.app import App, ResumabilityConfig

from .planning_agent import root_agent as planning_agent
from .question_agent import root_agent as question_agent
from .research_agent import root_agent as research_agent
from .generation_agent import root_agent as generation_agent
from .reviewer_agent import root_agent as reviewer_agent
from .database_agent import root_agent as database_agent

# Import tools for orchestrator
from tools.database_tools import DatabaseTools

# Initialize tools
# Note: Only database_tools needed at orchestrator level
# web_tools is available through research_agent sub-agent
database_tools = DatabaseTools()

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    sub_agents=[
        planning_agent,
        question_agent,
        research_agent,
        generation_agent,
        reviewer_agent,
        database_agent
    ],
    tools=[database_tools]  # Removed web_tools - available through research_agent
)

