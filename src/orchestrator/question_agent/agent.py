import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.config import load_config, retry_config
from models.models import Questions

config = load_config(Path(__file__).parent / "questions.yaml")

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from .question_db_sub_agent import root_agent as question_db_sub_agent

root_agent = LlmAgent(
    name=config["name"],
    description=config["description"],
    instruction=config["instruction"],
    model=Gemini(model=config["model"], retry_config=retry_config()),
    output_schema=Questions,
    sub_agents=[question_db_sub_agent],  # Use question_db_sub_agent for database writes
)