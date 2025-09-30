from pydantic import BaseModel
from models.agent import SearchAgent, GenerationAgent, Agent

class Task(BaseModel):
    name: str
    description: str
    agents: list[Agent]
    output_format: str
    output_schema: BaseModel
    output_dir: str
    output_file: str
    
class SearchTask(Task):
    name: str = "Search Task"
    description: str = "A search task that can search the web for information"
    agents: list[SearchAgent] = [SearchAgent()]
    output_format: str = "json"
    output_schema: BaseModel = BaseModel(name="SearchResult", description="A search result")
    output_dir: str = "search_results"
    output_file: str = "search_results.json"