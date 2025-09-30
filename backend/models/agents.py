from pydantic import BaseModel
from models.skills import Skill

class Agent(BaseModel):
    name: str
    description: str
    version: str
    url: str
    capabilities: list[str]
    skills: list[Skill]
    extensions: list[str]