from pydantic import BaseModel
from a2a.types import AgentSkill

class Skill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str]
    tools: list[AgentSkill]

class SearchSkill(Skill):
    id: str = "search"
    name: str = "Search"
    description: str = "A search skill that can search the web for information"
    tags: list[str] = ["search"]
    tools: list[AgentSkill] = [AgentSkill(id="search", name="Search", description="A search tool that can search the web for information", tags=["search"])]