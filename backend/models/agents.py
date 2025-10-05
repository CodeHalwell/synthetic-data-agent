from pydantic import BaseModel
from skills import Skill

class Agent(BaseModel):
    name: str
    description: str
    version: str
    url: str
    capabilities: list[str]
    skills: list[Skill]
    extensions: list[str]

class SearchAgent(Agent):
    name: str = "Search Agent"
    description: str = "A search agent that can search the web for information"
    version: str
    url: str
    capabilities: list[str]
    skills: list[Skill]
    extensions: list[str]