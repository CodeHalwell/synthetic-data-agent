from pydantic import BaseModel

class Skill(BaseModel):
    name: str
    description: str
    input_format: str
    output_format: str
    input_schema: BaseModel
    output_schema: BaseModel
    input_dir: str
    output_dir: str
    input_file: str

class SearchSkill(Skill):
    name: str = "Search Skill"
    description: str = "A search skill that can search the web for information"
    input_format: str = "json"
    output_format: str = "json"
    input_schema: BaseModel = BaseModel(name="SearchInput", description="A search input")
    output_schema: BaseModel = BaseModel(name="SearchOutput", description="A search output")
    input_dir: str = "search_inputs"
    output_dir: str = "search_outputs"
    input_file: str = "search_inputs.json"