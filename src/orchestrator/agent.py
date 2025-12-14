import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.config import load_config, retry_config

config = load_config(Path(__file__).parent / "orchestrator.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps.app import App, ResumabilityConfig

from .planning_agent import root_agent as planning_agent


root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    sub_agents=[planning_agent]
)

