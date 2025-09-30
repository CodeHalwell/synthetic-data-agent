from pydantic import BaseModel

class Agent(BaseModel):
    name: str
    description: str
    tools: list[str]
    system_prompt: str
    user_prompt: str
    output_format: str
    output_schema: BaseModel
    output_dir: str
    output_file: str

class SearchAgent(Agent):
    name: str = "Search Agent"
    description: str = "A search agent that can search the web for information"
    tools: list[str] = ["search"]
    system_prompt: str = "You are a search agent that can search the web for information"
    user_prompt: str = "Search the web for information"
    output_format: str = "json"
    output_schema: BaseModel = BaseModel(name="SearchResult", description="A search result")
    output_dir: str = "search_results"
    output_file: str = "search_results.json"

class GenerationAgent(Agent):
    name: str = "Generation Agent"
    description: str = "A generation agent that can generate data"
    tools: list[str] = ["generate"]
    system_prompt: str = "You are a generation agent that can generate data"
    user_prompt: str = "Generate data"
    output_format: str = "json"
    output_schema: BaseModel = BaseModel(name="GenerationResult", description="A generation result")
    output_dir: str = "generation_results"
    output_file: str = "generation_results.json"